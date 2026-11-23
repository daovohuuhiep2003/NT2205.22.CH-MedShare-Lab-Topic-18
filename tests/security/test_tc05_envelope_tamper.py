"""
Security adversarial tests for TC-05: Tamper Resistance and Context Splicing/Swapping.
Topic 18 — NT2205.11.CH (MedShare-Lab).

Mục tiêu kiểm thử bảo mật:
- Threat T-03: Kẻ tấn công tráo đổi ngữ cảnh (Context Splicing/Swapping: Tenant, Record, Field, Version).
- Threat T-05: Kẻ tấn công sửa đổi bit (Bit-flipping) trên Ciphertext, Tag hoặc AAD.
- Yêu cầu kiểm chứng (CR-01 / CR-02 / SR-05):
  1. Mọi can thiệp bit trên bản mã hoặc tag đều bị ném ngoại lệ DecryptionIntegrityError.
  2. Mọi hành vi tráo đổi bản mã giữa các bệnh nhân/tenant đều bị chặn bởi ContextMismatchError.
  3. Tuyệt đối không bao giờ trả về bất kỳ phần plaintext nào khi xảy ra lỗi (Fail-Closed).
"""

import sys
import unittest
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.medshare.crypto import (
    CryptoContext,
    FieldCipherEngine,
    FieldEnvelope,
    generate_dek,
    ContextMismatchError,
    DecryptionIntegrityError,
)


class EnvelopeTamperSecurityTests(unittest.TestCase):
    def setUp(self):
        self.dek = generate_dek()
        self.context_patient_a = CryptoContext(
            tenant_id="tenant_hospital_a",
            record_id="rec-patient-alice-001",
            field_id="diagnosis_code",
            dek_id="dek-patient-alice-dek1",
            data_version=1,
            data_policy_version=1,
        )
        self.secret_plaintext = "C34.9 - Ung thu phoi ac tinh"
        self.envelope = FieldCipherEngine.encrypt_field(
            self.secret_plaintext, self.context_patient_a, self.dek
        )

    # --------------------------------------------------------------------------
    # 1. Bit-Flipping Attacks (Threat T-05)
    # --------------------------------------------------------------------------
    def test_tc05_ciphertext_bit_flip_rejected(self):
        """TC-05: Sửa đổi 1 byte trong Ciphertext -> Bắt buộc bị từ chối bởi DecryptionIntegrityError."""
        raw_ct = bytearray(self.envelope.ciphertext)
        # Flip the first byte
        raw_ct[0] ^= 0x01
        tampered_ct = bytes(raw_ct)

        tampered_envelope = FieldEnvelope(
            tenant_id=self.envelope.tenant_id,
            object_kind=self.envelope.object_kind,
            record_id=self.envelope.record_id,
            field_id=self.envelope.field_id,
            data_version=self.envelope.data_version,
            data_policy_version=self.envelope.data_policy_version,
            dek_id=self.envelope.dek_id,
            nonce=self.envelope.nonce,
            ciphertext=tampered_ct,
            tag=self.envelope.tag,
        )

        with self.assertRaises(DecryptionIntegrityError):
            FieldCipherEngine.decrypt_field(tampered_envelope, self.context_patient_a, self.dek)

    def test_tc05_tag_bit_flip_rejected(self):
        """TC-05: Sửa đổi 1 byte trong Authentication Tag -> Bắt buộc bị từ chối bởi DecryptionIntegrityError."""
        raw_tag = bytearray(self.envelope.tag)
        raw_tag[0] ^= 0x55
        tampered_tag = bytes(raw_tag)

        tampered_envelope = FieldEnvelope(
            tenant_id=self.envelope.tenant_id,
            object_kind=self.envelope.object_kind,
            record_id=self.envelope.record_id,
            field_id=self.envelope.field_id,
            data_version=self.envelope.data_version,
            data_policy_version=self.envelope.data_policy_version,
            dek_id=self.envelope.dek_id,
            nonce=self.envelope.nonce,
            ciphertext=self.envelope.ciphertext,
            tag=tampered_tag,
        )

        with self.assertRaises(DecryptionIntegrityError):
            FieldCipherEngine.decrypt_field(tampered_envelope, self.context_patient_a, self.dek)

    def test_tc05_nonce_tampering_rejected(self):
        """TC-05: Thay đổi Nonce -> Gây sai lệch AAD/keystream dẫn đến xác thực tag thất bại."""
        raw_nonce = bytearray(self.envelope.nonce)
        raw_nonce[-1] ^= 0xFF
        tampered_nonce = bytes(raw_nonce)

        tampered_envelope = FieldEnvelope(
            tenant_id=self.envelope.tenant_id,
            object_kind=self.envelope.object_kind,
            record_id=self.envelope.record_id,
            field_id=self.envelope.field_id,
            data_version=self.envelope.data_version,
            data_policy_version=self.envelope.data_policy_version,
            dek_id=self.envelope.dek_id,
            nonce=tampered_nonce,
            ciphertext=self.envelope.ciphertext,
            tag=self.envelope.tag,
        )

        with self.assertRaises(DecryptionIntegrityError):
            FieldCipherEngine.decrypt_field(tampered_envelope, self.context_patient_a, self.dek)

    # --------------------------------------------------------------------------
    # 2. Context Splicing / Ciphertext Swapping Attacks (Threat T-03)
    # --------------------------------------------------------------------------
    def test_tc05_cross_patient_ciphertext_swap_attack(self):
        """
        TC-05 / Threat T-03: Kẻ tấn công sao chép bản mã bệnh án của Alice
        gán vào hồ sơ của Bob (nhằm giả mạo bệnh án hoặc gây nhầm lẫn y khoa).
        """
        context_patient_bob = CryptoContext(
            tenant_id="tenant_hospital_a",
            record_id="rec-patient-bob-002",  # Tráo sang Bob
            field_id="diagnosis_code",
            dek_id="dek-patient-alice-dek1",
        )

        # Khi Gateway giải mã cho Bob, expected_context là Bob
        with self.assertRaises(ContextMismatchError):
            FieldCipherEngine.decrypt_field(self.envelope, context_patient_bob, self.dek)

    def test_tc05_cross_tenant_swap_attack(self):
        """
        TC-05 / Threat T-03: Kẻ tấn công tráo bản mã từ Bệnh viện A sang Bệnh viện B (Cross-tenant leak).
        """
        context_hospital_b = CryptoContext(
            tenant_id="tenant_hospital_b",  # Tráo sang Bệnh viện B
            record_id="rec-patient-alice-001",
            field_id="diagnosis_code",
            dek_id="dek-patient-alice-dek1",
        )

        with self.assertRaises(ContextMismatchError):
            FieldCipherEngine.decrypt_field(self.envelope, context_hospital_b, self.dek)

    def test_tc05_cross_field_swap_attack(self):
        """
        TC-05 / Threat T-03: Tráo bản mã của trường này sang trường khác (ví dụ: tráo chẩn đoán sang ghi chú).
        """
        context_different_field = CryptoContext(
            tenant_id="tenant_hospital_a",
            record_id="rec-patient-alice-001",
            field_id="patient_name",  # Tráo sang name
            dek_id="dek-patient-alice-dek1",
        )

        with self.assertRaises(ContextMismatchError):
            FieldCipherEngine.decrypt_field(self.envelope, context_different_field, self.dek)

    def test_tc05_stale_data_version_swap(self):
        """
        TC-05 / Threat T-06: Tráo bản mã có version cũ vào version mới.
        """
        context_new_version = CryptoContext(
            tenant_id="tenant_hospital_a",
            record_id="rec-patient-alice-001",
            field_id="diagnosis_code",
            dek_id="dek-patient-alice-dek1",
            data_version=2,  # Expected version 2
        )

        with self.assertRaises(ContextMismatchError):
            FieldCipherEngine.decrypt_field(self.envelope, context_new_version, self.dek)

    # --------------------------------------------------------------------------
    # 3. Wrong Key Failure
    # --------------------------------------------------------------------------
    def test_tc05_wrong_dek_decryption_failure(self):
        """TC-05: Kẻ tấn công dùng sai DEK -> Xác thực tag thất bại tuyệt đối."""
        attacker_dek = generate_dek()  # DEK khác
        with self.assertRaises(DecryptionIntegrityError):
            FieldCipherEngine.decrypt_field(self.envelope, self.context_patient_a, attacker_dek)


if __name__ == "__main__":
    unittest.main()
