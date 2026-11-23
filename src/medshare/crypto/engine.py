"""
MedShare-Lab: Field-level Cipher Engine (Topic 18 — NT2205.11.CH).
Hiện thực hóa chuẩn mã hóa AEAD (M-02 AES-256-GCM + Context Binding).

Các đảm bảo an ninh:
1. CSPRNG Nonce Uniqueness: Mỗi trường/phiên sinh một Nonce 12-byte ngẫu nhiên mới hoàn toàn.
2. Immutable Context Binding: Xác thực AAD dựa trên Expected Context tin cậy từ Z1 Gateway/Registry.
3. Tamper Resistance: Phát hiện và từ chối 100% mọi hành vi sửa đổi bit trên Ciphertext, Tag hoặc AAD.
4. Fail-closed: Tuyệt đối không trả về bất kỳ phần plaintext nào khi giải mã lỗi.
"""

import os
from typing import Optional, Union

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from medshare.crypto.context import CryptoContext
from medshare.crypto.envelope import FieldEnvelope, NONCE_LENGTH_BYTES, TAG_LENGTH_BYTES
from medshare.crypto.errors import (
    ContextMismatchError,
    DecryptionIntegrityError,
    InvalidKeyError,
)

AES_256_KEY_BYTES = 32


def generate_dek() -> bytes:
    """Sinh khóa Data Encryption Key (DEK) 256-bit an toàn bằng CSPRNG (os.urandom)."""
    return os.urandom(AES_256_KEY_BYTES)


class FieldCipherEngine:
    """Động cơ mã hóa và giải mã tầng trường sử dụng AES-256-GCM."""

    @staticmethod
    def encrypt_field(
        plaintext: Union[str, bytes, int, None],
        context: CryptoContext,
        dek: bytes,
        capsule_id: Optional[str] = None,
        custom_nonce: Optional[bytes] = None,
    ) -> FieldEnvelope:
        """
        Mã hóa một trường dữ liệu thành FieldEnvelope.
        - dek: Khóa AES-256 (32 bytes).
        - context: Ngữ cảnh ràng buộc AAD (bất biến).
        - custom_nonce: Chỉ sử dụng cho các bài test tái lập nonce replay. Mặc định tự sinh qua CSPRNG.
        """
        if len(dek) != AES_256_KEY_BYTES:
            raise InvalidKeyError(f"DEK length must be exactly {AES_256_KEY_BYTES} bytes, got {len(dek)}")

        # Chuẩn hóa kiểu dữ liệu sang bytes
        if plaintext is None:
            pt_bytes = b""
        elif isinstance(plaintext, str):
            pt_bytes = plaintext.encode("utf-8")
        elif isinstance(plaintext, int):
            pt_bytes = str(plaintext).encode("utf-8")
        elif isinstance(plaintext, bytes):
            pt_bytes = plaintext
        else:
            pt_bytes = str(plaintext).encode("utf-8")

        # Sinh nonce 12 bytes
        nonce = custom_nonce if custom_nonce is not None else os.urandom(NONCE_LENGTH_BYTES)
        if len(nonce) != NONCE_LENGTH_BYTES:
            raise ValueError(f"Nonce must be {NONCE_LENGTH_BYTES} bytes")

        # Tính toán AAD bất biến từ Context
        aad = context.compute_canonical_aad()

        # Thực hiện AES-GCM
        aesgcm = AESGCM(dek)
        ct_with_tag = aesgcm.encrypt(nonce, pt_bytes, aad)

        # GCM xuất ra ciphertext + 16-byte tag ở cuối
        ciphertext = ct_with_tag[:-TAG_LENGTH_BYTES]
        tag = ct_with_tag[-TAG_LENGTH_BYTES:]

        return FieldEnvelope(
            tenant_id=context.tenant_id,
            object_kind=context.object_kind,
            record_id=context.record_id,
            field_id=context.field_id,
            data_version=context.data_version,
            data_policy_version=context.data_policy_version,
            dek_id=context.dek_id,
            capsule_id=capsule_id,
            nonce=nonce,
            ciphertext=ciphertext,
            tag=tag,
            format_version=context.format_version,
            data_suite_id=context.data_suite_id,
        )

    @staticmethod
    def decrypt_field(
        envelope: FieldEnvelope,
        expected_context: CryptoContext,
        dek: bytes,
    ) -> bytes:
        """
        Giải mã FieldEnvelope sang plaintext bytes.
        Bắt buộc đối soát với expected_context từ Trusted Computing Base (TCB).
        Nếu có bất kỳ sai khác nào về context hoặc integrity, ném ngoại lệ và không trả về plaintext.
        """
        if len(dek) != AES_256_KEY_BYTES:
            raise InvalidKeyError(f"DEK length must be exactly {AES_256_KEY_BYTES} bytes, got {len(dek)}")

        # 1. KIỂM SOÁT ĐỐI SOÁT NGỮ CẢNH (Context Binding Verification):
        # Ngăn chặn tấn công Context Swapping / Splicing (Threat T-03 / T-05)
        if envelope.tenant_id != expected_context.tenant_id:
            raise ContextMismatchError(
                f"Tenant ID mismatch: envelope has '{envelope.tenant_id}', expected '{expected_context.tenant_id}'"
            )
        if envelope.record_id != expected_context.record_id:
            raise ContextMismatchError(
                f"Record ID mismatch: envelope has '{envelope.record_id}', expected '{expected_context.record_id}'"
            )
        if envelope.field_id != expected_context.field_id:
            raise ContextMismatchError(
                f"Field ID mismatch: envelope has '{envelope.field_id}', expected '{expected_context.field_id}'"
            )
        if envelope.dek_id != expected_context.dek_id:
            raise ContextMismatchError(
                f"DEK ID mismatch: envelope has '{envelope.dek_id}', expected '{expected_context.dek_id}'"
            )
        if envelope.data_version != expected_context.data_version:
            raise ContextMismatchError(
                f"Data version mismatch: envelope has {envelope.data_version}, expected {expected_context.data_version}"
            )
        if envelope.data_policy_version != expected_context.data_policy_version:
            raise ContextMismatchError(
                f"Policy version mismatch: envelope has {envelope.data_policy_version}, expected {expected_context.data_policy_version}"
            )

        # 2. TÁI TẠO AAD TỪ NGUỒN TIN CẬY EXPECTED CONTEXT
        expected_aad = expected_context.compute_canonical_aad()

        # 3. THỰC HIỆN GIẢI MÃ VÀ KIỂM TRA TOÀN VẸN TAG
        aesgcm = AESGCM(dek)
        ct_with_tag = envelope.ciphertext + envelope.tag

        try:
            pt_bytes = aesgcm.decrypt(envelope.nonce, ct_with_tag, expected_aad)
            return pt_bytes
        except InvalidTag:
            raise DecryptionIntegrityError(
                "Authentication tag verification failed: Ciphertext, Tag, or AAD has been tampered with."
            )

