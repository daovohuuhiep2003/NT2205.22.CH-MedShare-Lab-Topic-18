"""
Unit tests for Equality Blind Index Engine (WP6 / Tuần 7).
Validates normalization, deterministic HMAC, cryptographic domain separation,
unsupported query rejection (422), and Gateway search post-filter verification.
"""

import unittest
import unicodedata
from medshare.broker.broker import KeyBroker
from medshare.broker.kms import MockKmsClient
from medshare.crypto.blind_index import (
    compute_blind_index,
    derive_search_key,
    normalize_field_value,
    validate_equality_query,
)
from medshare.crypto.engine import FieldCipherEngine
from medshare.crypto.errors import UnsupportedQueryError
from medshare.gateway.service import ClinicalGatewayService
from medshare.policy.abac import (
    AbacPolicyEngine,
    Action,
    EnvironmentContext,
    SubjectAttributes,
)
from medshare.storage.dal import EncryptedPatientRecord, MongoStorage


class TestEqualityBlindIndex(unittest.TestCase):
    def setUp(self):
        self.master_secret = b"test_master_search_secret_32bytes_ok!"
        self.tenant_a = "tenant_hospital_a"
        self.tenant_b = "tenant_hospital_b"

    def test_normalization_rules(self):
        """Verifies Unicode NFC normalization and field-specific casing."""
        # 1. Unicode NFC normalization: precomposed vs combining characters
        decomposed = "B\u1ec7nh vi\u1ec7n"  # "Bệnh viện"
        composed = unicodedata.normalize("NFC", decomposed)
        self.assertEqual(
            normalize_field_value("name", decomposed),
            normalize_field_value("name", composed),
        )

        # 2. Email normalization: lowercase and stripped whitespace
        self.assertEqual(
            normalize_field_value("email", "  Doctor.John@Hospital.org  "),
            "doctor.john@hospital.org",
        )

        # 3. Diagnosis normalization: uppercase and stripped
        self.assertEqual(
            normalize_field_value("diagnosis", "  e11.9  "),
            "E11.9",
        )

        # 4. Gender normalization: uppercase
        self.assertEqual(normalize_field_value("gender", "m"), "M")

        # 5. Numeric normalization: formatted as string integer
        self.assertEqual(normalize_field_value("age", 42), "42")
        self.assertEqual(normalize_field_value("age", 42.0), "42")

    def test_blind_index_determinism(self):
        """Verifies deterministic output for identical inputs and divergence for different inputs."""
        key = derive_search_key(self.master_secret, self.tenant_a, "patient_id", search_epoch=1)
        token1 = compute_blind_index(key, self.tenant_a, "patient_id", "P-1001", search_epoch=1)
        token2 = compute_blind_index(key, self.tenant_a, "patient_id", "P-1001", search_epoch=1)
        token_diff = compute_blind_index(key, self.tenant_a, "patient_id", "P-1002", search_epoch=1)

        self.assertEqual(len(token1), 64)
        self.assertEqual(token1, token2)
        self.assertNotEqual(token1, token_diff)

    def test_tenant_domain_isolation(self):
        """Verifies cross-tenant domain separation: identical values produce distinct tokens."""
        key_a = derive_search_key(self.master_secret, self.tenant_a, "diagnosis", search_epoch=1)
        key_b = derive_search_key(self.master_secret, self.tenant_b, "diagnosis", search_epoch=1)

        self.assertNotEqual(key_a, key_b)

        token_a = compute_blind_index(key_a, self.tenant_a, "diagnosis", "E11.9", search_epoch=1)
        token_b = compute_blind_index(key_b, self.tenant_b, "diagnosis", "E11.9", search_epoch=1)

        self.assertNotEqual(token_a, token_b)

    def test_field_domain_isolation(self):
        """Verifies cross-field separation: identical values in different fields produce distinct tokens."""
        key_pid = derive_search_key(self.master_secret, self.tenant_a, "patient_id", search_epoch=1)
        key_diag = derive_search_key(self.master_secret, self.tenant_a, "diagnosis", search_epoch=1)

        self.assertNotEqual(key_pid, key_diag)

        token_pid = compute_blind_index(key_pid, self.tenant_a, "patient_id", "12345", search_epoch=1)
        token_diag = compute_blind_index(key_diag, self.tenant_a, "diagnosis", "12345", search_epoch=1)

        self.assertNotEqual(token_pid, token_diag)

    def test_epoch_isolation(self):
        """Verifies search epoch rotation changes tokens for future content and reindexing."""
        key_ep1 = derive_search_key(self.master_secret, self.tenant_a, "patient_id", search_epoch=1)
        key_ep2 = derive_search_key(self.master_secret, self.tenant_a, "patient_id", search_epoch=2)

        self.assertNotEqual(key_ep1, key_ep2)

        token_ep1 = compute_blind_index(key_ep1, self.tenant_a, "patient_id", "P-1001", search_epoch=1)
        token_ep2 = compute_blind_index(key_ep2, self.tenant_a, "patient_id", "P-1001", search_epoch=2)

        self.assertNotEqual(token_ep1, token_ep2)

    def test_unsupported_query_validation(self):
        """
        DoD Gate Tuần 7: Rejects range, pattern, wildcard, and regex queries with HTTP 422.
        """
        # Exact query passes
        val = validate_equality_query("patient_id", "P-1001")
        self.assertEqual(val, "P-1001")

        val_dict = validate_equality_query("patient_id", {"op": "eq", "value": "P-1001"})
        self.assertEqual(val_dict, "P-1001")

        # Range operators fail with 422
        with self.assertRaises(UnsupportedQueryError) as ctx:
            validate_equality_query("age", {"op": ">", "value": 50})
        self.assertEqual(ctx.exception.status_code, 422)

        with self.assertRaises(UnsupportedQueryError) as ctx:
            validate_equality_query("age", {"op": "between", "value": [20, 40]})
        self.assertEqual(ctx.exception.status_code, 422)

        # Wildcards / patterns fail with 422
        with self.assertRaises(UnsupportedQueryError) as ctx:
            validate_equality_query("patient_id", "P-10%")
        self.assertEqual(ctx.exception.status_code, 422)

        with self.assertRaises(UnsupportedQueryError) as ctx:
            validate_equality_query("patient_id", "%1001")
        self.assertEqual(ctx.exception.status_code, 422)

        with self.assertRaises(UnsupportedQueryError) as ctx:
            validate_equality_query("patient_id", "*1001*")
        self.assertEqual(ctx.exception.status_code, 422)


class MockStorageInMemory:
    """In-memory DAL for isolated testing of Gateway search post-filtering."""

    def __init__(self):
        self.patients = {}
        self.search_index = []

    def save_patient(self, record, capsule):
        self.patients[record.record_id] = (record, capsule)
        self.search_index = [e for e in self.search_index if e["record_id"] != record.record_id]
        self.search_index.append({
            "tenant_id": record.tenant_id,
            "field_name": "patient_id",
            "search_epoch": 1,
            "token": record.patient_id_bidx,
            "record_id": record.record_id,
        })
        if record.diagnosis_bidx:
            self.search_index.append({
                "tenant_id": record.tenant_id,
                "field_name": "diagnosis",
                "search_epoch": 1,
                "token": record.diagnosis_bidx,
                "record_id": record.record_id,
            })

    def search_by_blind_index(self, tenant_id, field_name, token, search_epoch=1):
        matched = []
        for e in self.search_index:
            if (
                e["tenant_id"] == tenant_id
                and e["field_name"] == field_name
                and e["search_epoch"] == search_epoch
                and e["token"] == token
            ):
                matched.append(self.patients[e["record_id"]])
        return matched


class TestGatewaySearchPostFilter(unittest.TestCase):
    def setUp(self):
        self.kms = MockKmsClient()
        self.pdp = AbacPolicyEngine()
        self.broker = KeyBroker(kms_client=self.kms, pdp=self.pdp)
        self.engine = FieldCipherEngine()
        self.storage = MockStorageInMemory()
        self.gateway = ClinicalGatewayService(
            pdp=self.pdp,
            broker=self.broker,
            engine=self.engine,
            storage=self.storage,
        )
        self.doctor = SubjectAttributes(
            user_id="doc_cardiologist",
            tenant_id="tenant_hospital_a",
            role="DOCTOR",
            department="CARDIOLOGY",
            clearance="CONFIDENTIAL",
        )


    def test_search_equality_success_and_post_filter(self):
        """Verifies ingestion, exact equality search, and rejection of tampered candidate entries."""
        # Ingest record 1
        rec1 = {
            "record_id": "rec_001",
            "patient_id": "PID-999",
            "department": "CARDIOLOGY",
            "name": "Nguyen Van A",
            "dob": "1980-01-01",
            "gender": "M",
            "diagnosis": "I25.1",
            "notes": "Stable",
        }
        self.gateway.ingest_patient_record(self.doctor, rec1)

        # Ingest record 2
        rec2 = {
            "record_id": "rec_002",
            "patient_id": "PID-888",
            "department": "CARDIOLOGY",
            "name": "Tran Thi B",
            "dob": "1990-05-15",
            "gender": "F",
            "diagnosis": "E11.9",
            "notes": "Followup",
        }
        self.gateway.ingest_patient_record(self.doctor, rec2)

        # Search exact match for PID-999
        results = self.gateway.search_patients_by_equality(self.doctor, "patient_id", "PID-999")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["record_id"], "rec_001")
        self.assertEqual(results[0]["fields"]["name"], "Nguyen Van A")

        # Search exact match for PID-888
        results_888 = self.gateway.search_patients_by_equality(self.doctor, "patient_id", "PID-888")
        self.assertEqual(len(results_888), 1)
        self.assertEqual(results_888[0]["record_id"], "rec_002")

        # Search non-existent
        results_none = self.gateway.search_patients_by_equality(self.doctor, "patient_id", "PID-000")
        self.assertEqual(len(results_none), 0)

        # Unsupported query (range/wildcard) raises 422
        with self.assertRaises(UnsupportedQueryError) as ctx:
            self.gateway.search_patients_by_equality(self.doctor, "patient_id", "PID-%")
        self.assertEqual(ctx.exception.status_code, 422)

    def test_tc17_tampered_index_candidate_filtered_out(self):
        """
        TC-17: Active server manipulation (stale/spurious index candidate).
        Verifies that when storage returns a misbound record for a token,
        Gateway post-filter decrypts and rejects the mismatch.
        """
        rec1 = {
            "record_id": "rec_real",
            "patient_id": "PID-REAL",
            "department": "CARDIOLOGY",
            "name": "Nguyen Real",
            "dob": "1985-02-02",
            "gender": "M",
            "diagnosis": "I25.1",
            "notes": "Real patient",
        }
        self.gateway.ingest_patient_record(self.doctor, rec1)

        rec_spurious = {
            "record_id": "rec_spurious",
            "patient_id": "PID-SPURIOUS",
            "department": "CARDIOLOGY",
            "name": "Nguyen Spurious",
            "dob": "1988-03-03",
            "gender": "M",
            "diagnosis": "I25.1",
            "notes": "Spurious patient",
        }
        self.gateway.ingest_patient_record(self.doctor, rec_spurious)

        # Attacker injects spurious record into PID-REAL index
        search_key = self.broker.get_search_key("tenant_hospital_a", "patient_id", search_epoch=1)
        real_token = compute_blind_index(search_key, "tenant_hospital_a", "patient_id", "PID-REAL", search_epoch=1)

        # Manually alter storage index: point real_token to rec_spurious as well
        self.storage.search_index.append({
            "tenant_id": "tenant_hospital_a",
            "field_name": "patient_id",
            "search_epoch": 1,
            "token": real_token,
            "record_id": "rec_spurious",
        })

        # When searching for PID-REAL, storage returns 2 candidates: rec_real and rec_spurious
        # Gateway post-filter MUST decrypt rec_spurious, see "PID-SPURIOUS" != "PID-REAL", and drop it!
        results = self.gateway.search_patients_by_equality(self.doctor, "patient_id", "PID-REAL")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["record_id"], "rec_real")


if __name__ == "__main__":
    unittest.main()
