"""
Unit tests for MedShare Key Broker, Software KMS, and KeyCapsule.
"""

import json
import unittest

from medshare.broker import (
    KeyBroker,
    KeyCapsule,
    MockKmsClient,
    VaultKmsClient,
)
from medshare.crypto.errors import (
    ContextMismatchError,
    EnvelopeBoundsExceededError,
    InvalidEnvelopeError,
    TenantIsolationViolationError,
)


class KeyBrokerAndKmsUnitTests(unittest.TestCase):
    def setUp(self):
        self.mock_kms = MockKmsClient()
        self.broker = KeyBroker(self.mock_kms)

    def test_key_capsule_validation_and_serialization(self):
        bound_ctx = {"record_id": "rec_001", "data_class": "clinical"}
        cap = KeyCapsule(
            capsule_id="cap_test_01",
            capsule_version=1,
            tenant_id="hospital_a",
            kek_id="kek_hospital_a_clinical_v1",
            kek_version=1,
            wrapped_dek="vault:v1:test_wrapped",
            bound_object_context=bound_ctx,
        )
        self.assertEqual(cap.capsule_id, "cap_test_01")
        self.assertEqual(cap.tenant_id, "hospital_a")

        # Roundtrip JSON
        json_str = cap.to_json()
        cap_restored = KeyCapsule.from_json(json_str)
        self.assertEqual(cap, cap_restored)

        # Context JCS canonical bytes
        ctx_bytes = cap.compute_wrap_context_bytes()
        self.assertIn(b"hospital_a", ctx_bytes)
        self.assertIn(b"medshare/wrap/v1", ctx_bytes)

    def test_key_capsule_invalid_fields(self):
        with self.assertRaises(InvalidEnvelopeError):
            KeyCapsule("", 1, "t1", "k1", 1, "w1", {})
        with self.assertRaises(InvalidEnvelopeError):
            KeyCapsule("c1", 0, "t1", "k1", 1, "w1", {})
        with self.assertRaises(InvalidEnvelopeError):
            KeyCapsule("c1", 1, "", "k1", 1, "w1", {})

    def test_mock_kms_wrap_and_unwrap(self):
        kek_name = "test_mock_kek"
        dek = b"thirty_two_byte_secret_key_12345"
        ctx = b'{"tenant_id":"hospital_a"}'

        wrapped, ver = self.mock_kms.wrap_dek(kek_name, dek, context=ctx)
        self.assertEqual(ver, 1)
        self.assertTrue(wrapped.startswith("vault:v1:"))

        unwrapped = self.mock_kms.unwrap_dek(kek_name, wrapped, context=ctx)
        self.assertEqual(unwrapped, dek)

        # Context mismatch fails
        with self.assertRaises(Exception):
            self.mock_kms.unwrap_dek(kek_name, wrapped, context=b"WRONG_CONTEXT")

    def test_broker_issue_and_unwrap(self):
        dek, cap = self.broker.issue_dek_and_capsule("hospital_a", "rec_999")
        self.assertEqual(len(dek), 32)
        self.assertEqual(cap.tenant_id, "hospital_a")

        # Authorized unwrap
        unwrapped = self.broker.unwrap_dek(cap, {"tenant_id": "hospital_a", "record_id": "rec_999"})
        self.assertEqual(unwrapped, dek)

    def test_broker_tenant_isolation_tc06(self):
        dek, cap = self.broker.issue_dek_and_capsule("hospital_a", "rec_999")
        with self.assertRaises(TenantIsolationViolationError):
            self.broker.unwrap_dek(cap, {"tenant_id": "hospital_b", "record_id": "rec_999"})

    def test_broker_context_mismatch(self):
        dek, cap = self.broker.issue_dek_and_capsule("hospital_a", "rec_999")
        with self.assertRaises(ContextMismatchError):
            self.broker.unwrap_dek(cap, {"tenant_id": "hospital_a", "record_id": "rec_WRONG"})

    def test_broker_anti_replay_registry(self):
        dek, cap = self.broker.issue_dek_and_capsule("hospital_a", "rec_999")
        broker_stale = KeyBroker(self.mock_kms, registry={cap.capsule_id: 2})
        with self.assertRaises(ContextMismatchError):
            broker_stale.unwrap_dek(cap, {"tenant_id": "hospital_a", "record_id": "rec_999"})

    def test_broker_rewrap_capsule_tc09(self):
        dek, cap = self.broker.issue_dek_and_capsule("hospital_a", "rec_999")
        new_cap = self.broker.rewrap_capsule(cap)
        self.assertEqual(new_cap.capsule_version, cap.capsule_version + 1)
        unwrapped = self.broker.unwrap_dek(new_cap, {"tenant_id": "hospital_a", "record_id": "rec_999"})
        self.assertEqual(unwrapped, dek)


if __name__ == "__main__":
    unittest.main()

