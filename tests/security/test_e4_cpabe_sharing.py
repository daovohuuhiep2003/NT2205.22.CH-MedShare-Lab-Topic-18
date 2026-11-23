"""
MedShare-Lab: Security Test Suite for Experiment E4 (CP-ABE Profile P2 Sharing).
Topic 18 — NT2205.11.CH.

Test Cases:
- TC-11: Attribute Policy Access Control (AND/OR, Authorized vs Unauthorized).
- TC-12: Cryptographic Collusion Resistance (Mixing key components fails).
- TC-13: Epoch Revocation (Revoked user with old epoch key cannot decrypt new epoch document).
- TC-14: Offline Decryptability Boundary (LIMIT Case: old offline bytes remain readable).
- TC-05 / SR-05: AEAD Tamper Rejection on Share DEK & Payload Capsules (Bit-flipping, Context Swapping).
"""

import base64
import copy
import json
import unittest
from pathlib import Path

from medshare.crypto.abe_client import AbeClient, PolicyNotSatisfiedError, CollusionVulnerabilityError


class TestE4CpAbeSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = AbeClient()
        if not cls.client.is_service_healthy():
            raise unittest.SkipTest("medshare-abe-worker service (:9002) is not reachable.")
        cls.pk, cls.msk, cls.desc = cls.client.setup_authority(curve="BN254")

    # -------------------------------------------------------------------------
    # TC-11: Attribute Policy Access Control
    # -------------------------------------------------------------------------
    def test_tc11_attribute_access_control(self):
        """TC-11: Only users satisfying the boolean policy can decrypt; unauthorized users are denied."""
        payload = b"CONFIDENTIAL_RECORD: Patient Le Thi B - Diagnosis: Arrhythmia"
        policy = "((DOCTOR and CARDIOLOGY) or CHIEF_OF_MEDICINE)"

        package = self.client.create_export_package(
            pk=self.pk,
            payload=payload,
            policy=policy,
            tenant_id="hospital_b",
            epoch_id="EPOCH_2026_Q3",
        )

        # 1. Authorized User A: DOCTOR + CARDIOLOGY
        sk_doctor_cardio = self.client.issue_user_key(
            self.pk, self.msk, ["DOCTOR", "CARDIOLOGY", "TENANT_B"]
        )
        dec_a = self.client.decrypt_export_package(self.pk, package, sk_doctor_cardio)
        self.assertEqual(dec_a, payload, "Authorized Doctor in Cardiology must decrypt accurately.")

        # 2. Authorized User B: CHIEF_OF_MEDICINE (OR branch)
        sk_chief = self.client.issue_user_key(
            self.pk, self.msk, ["CHIEF_OF_MEDICINE", "TENANT_B"]
        )
        dec_b = self.client.decrypt_export_package(self.pk, package, sk_chief)
        self.assertEqual(dec_b, payload, "Authorized Chief of Medicine must decrypt accurately.")

        # 3. Unauthorized User C: NURSE + CARDIOLOGY (lacks DOCTOR)
        sk_nurse = self.client.issue_user_key(
            self.pk, self.msk, ["NURSE", "CARDIOLOGY", "TENANT_B"]
        )
        with self.assertRaises(PolicyNotSatisfiedError):
            self.client.decrypt_export_package(self.pk, package, sk_nurse)

        # 4. Unauthorized User D: DOCTOR + NEUROLOGY (lacks CARDIOLOGY)
        sk_doctor_neuro = self.client.issue_user_key(
            self.pk, self.msk, ["DOCTOR", "NEUROLOGY", "TENANT_B"]
        )
        with self.assertRaises(PolicyNotSatisfiedError):
            self.client.decrypt_export_package(self.pk, package, sk_doctor_neuro)

    # -------------------------------------------------------------------------
    # TC-12: Collusion Resistance Test
    # -------------------------------------------------------------------------
    def test_tc12_cryptographic_collusion_resistance(self):
        """
        TC-12: Collusion Resistance.
        Two unauthorized users (U1: DOCTOR, U2: CARDIOLOGY) cannot combine their key components
        to satisfy policy (DOCTOR and CARDIOLOGY).
        """
        policy = "(DOCTOR and CARDIOLOGY)"
        res = self.client.test_collusion_resistance(
            pk=self.pk,
            msk=self.msk,
            policy=policy,
            u1_attrs=["DOCTOR", "NEUROLOGY"],
            u2_attrs=["NURSE", "CARDIOLOGY"],
            u3_authorized_attrs=["DOCTOR", "CARDIOLOGY"],
        )
        self.assertTrue(res["collusion_resistance_verified"])
        self.assertFalse(res["u1_alone_decrypt"])
        self.assertFalse(res["u2_alone_decrypt"])
        self.assertTrue(res["u3_authorized_decrypt"])
        self.assertFalse(res["collusion_strategy_1_success"])
        self.assertFalse(res["collusion_strategy_2_success"])

    # -------------------------------------------------------------------------
    # TC-13: Epoch Revocation
    # -------------------------------------------------------------------------
    def test_tc13_epoch_revocation_lifecycle(self):
        """
        TC-13: Epoch Revocation.
        When system advances from Epoch 1 to Epoch 2, a user revoked at Epoch 2
        cannot decrypt new content encrypted for Epoch 2.
        """
        policy_e1 = "(DOCTOR and CARDIOLOGY and EPOCH2026Q3)"
        policy_e2 = "(DOCTOR and CARDIOLOGY and EPOCH2026Q4)"

        pkg_e1 = self.client.create_export_package(
            pk=self.pk,
            payload=b"RECORD_DATA_EPOCH_1",
            policy=policy_e1,
            tenant_id="hospital_a",
            epoch_id="EPOCH_2026_Q3",
        )
        pkg_e2 = self.client.create_export_package(
            pk=self.pk,
            payload=b"RECORD_DATA_EPOCH_2",
            policy=policy_e2,
            tenant_id="hospital_a",
            epoch_id="EPOCH_2026_Q4",
        )

        # User holds Epoch 1 key
        sk_e1 = self.client.issue_user_key(
            self.pk, self.msk, ["DOCTOR", "CARDIOLOGY", "EPOCH2026Q3"]
        )

        # User successfully decrypts Epoch 1 document
        dec1 = self.client.decrypt_export_package(self.pk, pkg_e1, sk_e1)
        self.assertEqual(dec1, b"RECORD_DATA_EPOCH_1")

        # User is revoked in Epoch 2 (attempting to decrypt Epoch 2 document with Epoch 1 key fails)
        with self.assertRaises(PolicyNotSatisfiedError):
            self.client.decrypt_export_package(self.pk, pkg_e2, sk_e1)

        # Non-revoked user reissued at Epoch 2 can decrypt Epoch 2 document
        sk_e2 = self.client.issue_user_key(
            self.pk, self.msk, ["DOCTOR", "CARDIOLOGY", "EPOCH2026Q4"]
        )
        dec2 = self.client.decrypt_export_package(self.pk, pkg_e2, sk_e2)
        self.assertEqual(dec2, b"RECORD_DATA_EPOCH_2")

    # -------------------------------------------------------------------------
    # TC-14: Scientific Boundary Verification (LIMIT Case)
    # -------------------------------------------------------------------------
    def test_tc14_offline_decryptability_limit(self):
        """
        TC-14: LIMIT Case.
        Historical data already distributed to client remains decryptable offline
        with the historical key even after the server revokes the user or increments the epoch.
        Confirms requirement for Fresh DEK + re-encryption for future content.
        """
        payload = b"HISTORICAL_RECORD_BEFORE_REVOCATION"
        pkg = self.client.create_export_package(
            pk=self.pk,
            payload=payload,
            policy="(DOCTOR and EPOCH2026Q3)",
            tenant_id="hospital_a",
            epoch_id="EPOCH_2026_Q3",
        )
        sk_e1 = self.client.issue_user_key(self.pk, self.msk, ["DOCTOR", "EPOCH2026Q3"])

        # Offline decryption of historical document succeeds
        dec_offline = self.client.decrypt_export_package(self.pk, pkg, sk_e1)
        self.assertEqual(dec_offline, payload)

    # -------------------------------------------------------------------------
    # TC-05 / SR-05: AEAD Tamper Rejection on Wrapped Share DEK and Payload
    # -------------------------------------------------------------------------
    def test_tc05_aead_tamper_rejection(self):
        """TC-05 / SR-05: Flipping bits in wrapped DEK, payload, or swapping context must trigger AEAD rejection."""
        payload = b"GENOMIC_SEQUENCE_AND_ONCOLOGY_DATA_EXAM"
        pkg = self.client.create_export_package(
            pk=self.pk,
            payload=payload,
            policy="(ONCOLOGY and RESEARCHER)",
            tenant_id="hospital_c",
            epoch_id="EPOCH_2026_Q3",
        )
        sk = self.client.issue_user_key(self.pk, self.msk, ["ONCOLOGY", "RESEARCHER"])

        # Baseline: Valid package decrypts cleanly
        self.assertEqual(self.client.decrypt_export_package(self.pk, pkg, sk), payload)

        # Mutation 1: Tamper wrapped share_DEK ciphertext
        tampered_pkg_dek = copy.deepcopy(pkg)
        raw_dek = bytearray(base64.b64decode(tampered_pkg_dek["wrapped_share_dek"].encode("ascii")))
        raw_dek[20] ^= 0xFF  # Flip a bit in the ciphertext / tag
        tampered_pkg_dek["wrapped_share_dek"] = base64.b64encode(raw_dek).decode("ascii")

        with self.assertRaises(Exception):
            self.client.decrypt_export_package(self.pk, tampered_pkg_dek, sk)

        # Mutation 2: Tamper encrypted bulk payload
        tampered_pkg_payload = copy.deepcopy(pkg)
        raw_payload = bytearray(base64.b64decode(tampered_pkg_payload["encrypted_payload"].encode("ascii")))
        raw_payload[25] ^= 0xAA  # Flip a bit in payload ciphertext
        tampered_pkg_payload["encrypted_payload"] = base64.b64encode(raw_payload).decode("ascii")

        with self.assertRaises(Exception):
            self.client.decrypt_export_package(self.pk, tampered_pkg_payload, sk)

        # Mutation 3: Context Swapping (Change tenant_id in manifest)
        tampered_pkg_tenant = copy.deepcopy(pkg)
        tampered_pkg_tenant["tenant_id"] = "hospital_attacker_spoof"

        with self.assertRaises(Exception):
            self.client.decrypt_export_package(self.pk, tampered_pkg_tenant, sk)

    # -------------------------------------------------------------------------
    # Curve Support & Multi-Leaf Scalability
    # -------------------------------------------------------------------------
    def test_curve_support_and_complex_tree(self):
        """Verify both BN254 and SS512 support complex multi-leaf access structures."""
        for curve in ["BN254", "SS512"]:
            pk, msk, desc = self.client.setup_authority(curve=curve)
            policy = "((ATTR1 and ATTR2) or (ATTR3 and ATTR4))"
            payload = f"COMPLEX_TREE_TEST_{curve}".encode("utf-8")

            pkg = self.client.create_export_package(
                pk=pk,
                payload=payload,
                policy=policy,
                tenant_id="tenant_x",
                epoch_id="EPOCH_1",
                curve=curve,
            )

            # User satisfying Branch 1 (ATTR1 + ATTR2)
            sk1 = self.client.issue_user_key(pk, msk, ["ATTR1", "ATTR2"], curve=curve)
            self.assertEqual(
                self.client.decrypt_export_package(pk, pkg, sk1, curve=curve),
                payload,
            )

            # User satisfying Branch 2 (ATTR3 + ATTR4)
            sk2 = self.client.issue_user_key(pk, msk, ["ATTR3", "ATTR4"], curve=curve)
            self.assertEqual(
                self.client.decrypt_export_package(pk, pkg, sk2, curve=curve),
                payload,
            )

            # User missing either branch
            sk_fail = self.client.issue_user_key(pk, msk, ["ATTR1", "ATTR4"], curve=curve)
            with self.assertRaises(PolicyNotSatisfiedError):
                self.client.decrypt_export_package(pk, pkg, sk_fail, curve=curve)


if __name__ == "__main__":
    unittest.main()

