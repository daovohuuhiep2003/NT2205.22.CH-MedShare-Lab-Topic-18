"""
Unit tests for MedShare-Lab Field Envelope Engine (Topic 18 — NT2205.11.CH).
Validates:
- TC-01: Correct round-trip encryption/decryption for various data types.
- Randomized ciphertext property (fresh nonces produce different ciphertexts).
- Canonical AAD computation stability and determinism.
- TC-24: Serialization/deserialization bounds and malformed payload handling.
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
    EnvelopeValidationError,
    InvalidKeyError,
)


class FieldCryptoUnitTests(unittest.TestCase):
    def setUp(self):
        self.dek = generate_dek()
        self.context = CryptoContext(
            tenant_id="tenant_hospital_a",
            record_id="rec-1111-2222",
            field_id="clinical_note",
            dek_id="dek-uuid-0001",
        )

    def test_tc01_round_trip_text(self):
        """TC-01: Round-trip mã hóa và giải mã chuỗi văn bản UTF-8 bình thường."""
        plaintext = "Bệnh nhân có tiền sử cao huyết áp và hen suyễn mãn tính."
        envelope = FieldCipherEngine.encrypt_field(plaintext, self.context, self.dek)
        decrypted_bytes = FieldCipherEngine.decrypt_field(envelope, self.context, self.dek)
        self.assertEqual(decrypted_bytes.decode("utf-8"), plaintext)

    def test_tc01_round_trip_empty_and_null(self):
        """TC-01: Round-trip mã hóa chuỗi rỗng và None."""
        # Empty string
        env_empty = FieldCipherEngine.encrypt_field("", self.context, self.dek)
        dec_empty = FieldCipherEngine.decrypt_field(env_empty, self.context, self.dek)
        self.assertEqual(dec_empty, b"")

        # None value
        env_none = FieldCipherEngine.encrypt_field(None, self.context, self.dek)
        dec_none = FieldCipherEngine.decrypt_field(env_none, self.context, self.dek)
        self.assertEqual(dec_none, b"")

    def test_tc01_round_trip_integers(self):
        """TC-01: Round-trip số nguyên (ví dụ: amount_units chi phí điều trị)."""
        amount = 750
        envelope = FieldCipherEngine.encrypt_field(amount, self.context, self.dek)
        decrypted = FieldCipherEngine.decrypt_field(envelope, self.context, self.dek)
        self.assertEqual(int(decrypted.decode("utf-8")), amount)

    def test_tc01_randomized_ciphertext_fresh_nonce(self):
        """TC-01: Hai lần mã hóa cùng một bản rõ phải sinh ra Nonce và Ciphertext khác nhau."""
        msg = "Chẩn đoán bí mật"
        env1 = FieldCipherEngine.encrypt_field(msg, self.context, self.dek)
        env2 = FieldCipherEngine.encrypt_field(msg, self.context, self.dek)

        self.assertNotEqual(env1.nonce, env2.nonce, "Fresh CSPRNG nonces must not repeat")
        self.assertNotEqual(env1.ciphertext, env2.ciphertext, "Ciphertexts must differ due to fresh nonce")
        self.assertNotEqual(env1.tag, env2.tag, "Authentication tags must differ")

    def test_canonical_aad_determinism(self):
        """Xác minh AAD tính toán có tính tất định và sắp xếp khóa theo RFC 8785."""
        aad1 = self.context.compute_canonical_aad()
        aad2 = self.context.compute_canonical_aad()
        self.assertEqual(aad1, aad2)
        # Check expected canonical string content
        self.assertIn(b'"domain":"medshare/data/v1"', aad1)
        self.assertIn(b'"tenant_id":"tenant_hospital_a"', aad1)
        self.assertIn(b'"record_id":"rec-1111-2222"', aad1)

    def test_tc24_envelope_serialization_round_trip(self):
        """TC-24: Tuần tự hóa JSON và giải tuần tự hóa phải giữ nguyên 100% dữ liệu nhị phân."""
        envelope = FieldCipherEngine.encrypt_field("Thử nghiệm tuần tự hóa", self.context, self.dek)
        json_str = envelope.to_json()

        restored_env = FieldEnvelope.from_json(json_str)
        self.assertEqual(restored_env.nonce, envelope.nonce)
        self.assertEqual(restored_env.ciphertext, envelope.ciphertext)
        self.assertEqual(restored_env.tag, envelope.tag)
        self.assertEqual(restored_env.tenant_id, envelope.tenant_id)

        # Giải mã envelope đã phục hồi
        dec = FieldCipherEngine.decrypt_field(restored_env, self.context, self.dek)
        self.assertEqual(dec.decode("utf-8"), "Thử nghiệm tuần tự hóa")

    def test_tc24_malformed_envelope_rejections(self):
        """TC-24: Từ chối các envelope bị định dạng sai, invalid base64, sai version."""
        # 1. Invalid format_version
        with self.assertRaises(EnvelopeValidationError):
            FieldEnvelope(
                tenant_id="t1", record_id="r1", field_id="f1", dek_id="d1",
                nonce=b"1" * 12, ciphertext=b"c", tag=b"t" * 16,
                format_version=99  # Invalid version
            )

        # 2. Invalid suite
        with self.assertRaises(EnvelopeValidationError):
            FieldEnvelope(
                tenant_id="t1", record_id="r1", field_id="f1", dek_id="d1",
                nonce=b"1" * 12, ciphertext=b"c", tag=b"t" * 16,
                data_suite_id="DES-INSECURE"
            )

        # 3. Invalid nonce length
        with self.assertRaises(EnvelopeValidationError):
            FieldEnvelope(
                tenant_id="t1", record_id="r1", field_id="f1", dek_id="d1",
                nonce=b"short", ciphertext=b"c", tag=b"t" * 16
            )

        # 4. Invalid key length
        with self.assertRaises(InvalidKeyError):
            FieldCipherEngine.encrypt_field("test", self.context, b"short_key")

    def test_context_validation_failures(self):
        """Kiểm tra từ chối context có các trường rỗng."""
        with self.assertRaises(EnvelopeValidationError):
            CryptoContext(tenant_id="", record_id="r1", field_id="f1", dek_id="d1")
        with self.assertRaises(EnvelopeValidationError):
            CryptoContext(tenant_id="t1", record_id="", field_id="f1", dek_id="d1")


if __name__ == "__main__":
    unittest.main()
