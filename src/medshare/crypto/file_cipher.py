"""
Chunked AES-256-GCM File Cipher for Medical Imaging and Attachments.
Part of MedShare-Lab (Topic 18 — NT2205.11.CH).

Provides streaming encryption and decryption for non-text medical files
(DICOM, CT/MRI, X-ray, Ultrasound, PDF lab results) stored on MinIO Object Storage (Zone Z2).
Enforces:
- Cryptographic binding via AAD (tenant_id, record_id, attachment_id, chunk_index, is_last)
- Constant-memory chunked streaming (e.g. 1MB chunks)
- Full integrity and tamper detection (AES-GCM tag verification + SHA-256 digest validation)
- Prevention of truncation, chunk reordering, and cross-record substitution attacks
"""

import hashlib
import io
import json
import os
import secrets
import struct
from typing import BinaryIO, Generator, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from medshare.crypto.errors import (
    CryptoError,
    GcmAuthTagMismatchError,
    InvalidKeyError,
    RecordTamperedError,
)

FILE_CIPHER_MAGIC = b"MSENC01\x00"  # 8 bytes magic header
DEFAULT_CHUNK_SIZE = 1024 * 1024   # 1 MB chunk size
NONCE_BYTES = 12


class MedicalFileCipher:
    """
    Streaming authenticated encryption engine for large medical binary objects.
    """

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.chunk_size = chunk_size

    @staticmethod
    def _compute_chunk_aad(
        tenant_id: str,
        record_id: str,
        attachment_id: str,
        chunk_index: int,
        is_last: bool,
    ) -> bytes:
        """
        Builds canonical Authenticated Additional Data (AAD) for a specific chunk.
        AAD = JCS-like compact JSON binding tenant, record, attachment, chunk index, and terminal flag.
        """
        aad_dict = {
            "att": attachment_id,
            "chk": chunk_index,
            "lst": 1 if is_last else 0,
            "rec": record_id,
            "ten": tenant_id,
        }
        return json.dumps(aad_dict, separators=(",", ":"), sort_keys=True).encode("utf-8")

    def encrypt_stream(
        self,
        in_stream: BinaryIO,
        out_stream: BinaryIO,
        dek: bytes,
        tenant_id: str,
        record_id: str,
        attachment_id: str,
        filename: str,
        content_type: str,
        capsule_id: str,
        total_size: Optional[int] = None,
    ) -> dict[str, any]:
        """
        Encrypts an input binary stream into an authenticated chunked ciphertext stream.

        Returns metadata summary including plaintext_sha256, ciphertext_sha256,
        total_chunks, and ciphertext_bytes.
        """
        if len(dek) != 32:
            raise InvalidKeyError(f"DEK must be exactly 32 bytes (AES-256), got {len(dek)}")

        aesgcm = AESGCM(dek)
        plaintext_hasher = hashlib.sha256()
        ciphertext_hasher = hashlib.sha256()

        # Buffer initial write to measure header
        # 1. We first prepare header placeholder or read stream to compute total chunks if total_size known
        # In streaming, we can write a variable-length JSON header prefixed by its 4-byte length.
        header_meta = {
            "format_version": 1,
            "data_suite_id": "AES256GCM-Chunked-v1",
            "chunk_size": self.chunk_size,
            "tenant_id": tenant_id,
            "record_id": record_id,
            "attachment_id": attachment_id,
            "filename": filename,
            "content_type": content_type,
            "capsule_id": capsule_id,
        }
        header_bytes = json.dumps(header_meta, separators=(",", ":"), sort_keys=True).encode("utf-8")

        # Write magic bytes + 4-byte header length + header JSON
        header_block = FILE_CIPHER_MAGIC + struct.pack(">I", len(header_bytes)) + header_bytes
        out_stream.write(header_block)
        ciphertext_hasher.update(header_block)
        ciphertext_bytes = len(header_block)

        chunk_index = 0
        current_chunk = in_stream.read(self.chunk_size)

        while current_chunk:
            plaintext_hasher.update(current_chunk)
            # Peek next chunk to see if current chunk is the last one
            next_chunk = in_stream.read(self.chunk_size)
            is_last = (len(next_chunk) == 0)

            # Generate distinct 96-bit nonce for this chunk
            nonce = secrets.token_bytes(NONCE_BYTES)

            aad = self._compute_chunk_aad(
                tenant_id=tenant_id,
                record_id=record_id,
                attachment_id=attachment_id,
                chunk_index=chunk_index,
                is_last=is_last,
            )

            # Encrypt current chunk (produces ciphertext + 16-byte tag)
            encrypted_payload = aesgcm.encrypt(nonce, current_chunk, aad)

            # Chunk block format:
            # [chunk_index: 4 bytes uint32]
            # [is_last: 1 byte uint8]
            # [payload_len: 4 bytes uint32]
            # [nonce: 12 bytes]
            # [encrypted_payload: payload_len bytes]
            chunk_header = struct.pack(
                ">IBI",
                chunk_index,
                1 if is_last else 0,
                len(encrypted_payload),
            )
            block = chunk_header + nonce + encrypted_payload

            out_stream.write(block)
            ciphertext_hasher.update(block)
            ciphertext_bytes += len(block)

            chunk_index += 1
            current_chunk = next_chunk

        # Edge case: empty file (0 bytes)
        if chunk_index == 0:
            nonce = secrets.token_bytes(NONCE_BYTES)
            aad = self._compute_chunk_aad(tenant_id, record_id, attachment_id, 0, True)
            encrypted_payload = aesgcm.encrypt(nonce, b"", aad)
            chunk_header = struct.pack(">IBI", 0, 1, len(encrypted_payload))
            block = chunk_header + nonce + encrypted_payload
            out_stream.write(block)
            ciphertext_hasher.update(block)
            ciphertext_bytes += len(block)
            chunk_index = 1

        return {
            "attachment_id": attachment_id,
            "tenant_id": tenant_id,
            "record_id": record_id,
            "filename": filename,
            "content_type": content_type,
            "capsule_id": capsule_id,
            "total_chunks": chunk_index,
            "plaintext_sha256": plaintext_hasher.hexdigest(),
            "ciphertext_sha256": ciphertext_hasher.hexdigest(),
            "ciphertext_bytes": ciphertext_bytes,
        }

    def decrypt_stream(
        self,
        in_stream: BinaryIO,
        out_stream: BinaryIO,
        dek: bytes,
        expected_tenant_id: str,
        expected_record_id: str,
        expected_attachment_id: str,
        expected_plaintext_sha256: Optional[str] = None,
    ) -> dict[str, any]:
        """
        Decrypts an authenticated chunked ciphertext stream.
        Validates AAD on every chunk, sequence order, terminal flag, and overall SHA-256.

        Raises:
            GcmAuthTagMismatchError: if any chunk's ciphertext, tag, or context was modified.
            RecordTamperedError: if chunk ordering, headers, or plaintext hash do not match.
        """
        if len(dek) != 32:
            raise InvalidKeyError(f"DEK must be exactly 32 bytes (AES-256), got {len(dek)}")

        aesgcm = AESGCM(dek)

        # 1. Read and verify magic header
        magic = in_stream.read(len(FILE_CIPHER_MAGIC))
        if magic != FILE_CIPHER_MAGIC:
            raise RecordTamperedError(f"Invalid file cipher magic: {magic!r}")

        # 2. Read header length and parse metadata
        header_len_raw = in_stream.read(4)
        if len(header_len_raw) < 4:
            raise RecordTamperedError("Truncated file cipher header length")
        (header_len,) = struct.unpack(">I", header_len_raw)

        header_bytes = in_stream.read(header_len)
        if len(header_bytes) < header_len:
            raise RecordTamperedError("Truncated file cipher header payload")

        try:
            header_meta = json.loads(header_bytes.decode("utf-8"))
        except Exception as e:
            raise RecordTamperedError(f"Corrupted file cipher header JSON: {e}")

        # Check tenant, record, and attachment binding in header
        if header_meta.get("tenant_id") != expected_tenant_id:
            raise RecordTamperedError(
                f"Tenant mismatch in header: expected {expected_tenant_id}, got {header_meta.get('tenant_id')}"
            )
        if header_meta.get("record_id") != expected_record_id:
            raise RecordTamperedError(
                f"Record mismatch in header: expected {expected_record_id}, got {header_meta.get('record_id')}"
            )
        if header_meta.get("attachment_id") != expected_attachment_id:
            raise RecordTamperedError(
                f"Attachment mismatch in header: expected {expected_attachment_id}, got {header_meta.get('attachment_id')}"
            )

        plaintext_hasher = hashlib.sha256()
        expected_chunk_index = 0
        saw_last_chunk = False
        total_plaintext_bytes = 0

        # Read chunks until EOF or last chunk
        while True:
            chunk_header = in_stream.read(9)  # 4 (index) + 1 (is_last) + 4 (payload_len)
            if not chunk_header:
                if not saw_last_chunk:
                    raise RecordTamperedError("File stream truncated before terminal chunk")
                break

            if len(chunk_header) < 9:
                raise RecordTamperedError("Truncated chunk header in ciphertext stream")

            chunk_idx, is_last_flag, payload_len = struct.unpack(">IBI", chunk_header)
            is_last = (is_last_flag == 1)

            if chunk_idx != expected_chunk_index:
                raise RecordTamperedError(
                    f"Chunk sequence violation: expected chunk {expected_chunk_index}, got {chunk_idx}"
                )

            nonce = in_stream.read(NONCE_BYTES)
            if len(nonce) < NONCE_BYTES:
                raise RecordTamperedError(f"Truncated nonce in chunk {chunk_idx}")

            encrypted_payload = in_stream.read(payload_len)
            if len(encrypted_payload) < payload_len:
                raise RecordTamperedError(f"Truncated encrypted payload in chunk {chunk_idx}")

            aad = self._compute_chunk_aad(
                tenant_id=expected_tenant_id,
                record_id=expected_record_id,
                attachment_id=expected_attachment_id,
                chunk_index=chunk_idx,
                is_last=is_last,
            )

            try:
                decrypted_chunk = aesgcm.decrypt(nonce, encrypted_payload, aad)
            except Exception as exc:
                raise GcmAuthTagMismatchError(
                    f"Authentication failed for chunk {chunk_idx} of attachment {expected_attachment_id}: {exc}"
                ) from exc

            out_stream.write(decrypted_chunk)
            plaintext_hasher.update(decrypted_chunk)
            total_plaintext_bytes += len(decrypted_chunk)

            expected_chunk_index += 1
            if is_last:
                saw_last_chunk = True
                break

        actual_sha256 = plaintext_hasher.hexdigest()
        if expected_plaintext_sha256 and actual_sha256.lower() != expected_plaintext_sha256.lower():
            raise RecordTamperedError(
                f"Plaintext SHA-256 digest mismatch: expected {expected_plaintext_sha256}, got {actual_sha256}"
            )

        return {
            "attachment_id": expected_attachment_id,
            "tenant_id": expected_tenant_id,
            "record_id": expected_record_id,
            "filename": header_meta.get("filename"),
            "content_type": header_meta.get("content_type"),
            "total_chunks": expected_chunk_index,
            "plaintext_sha256": actual_sha256,
            "total_plaintext_bytes": total_plaintext_bytes,
        }

    def encrypt_file(
        self,
        src_path: str,
        dst_path: str,
        dek: bytes,
        tenant_id: str,
        record_id: str,
        attachment_id: str,
        capsule_id: str,
        content_type: str = "application/octet-stream",
    ) -> dict[str, any]:
        """Convenience method to encrypt a file on disk."""
        filename = os.path.basename(src_path)
        with open(src_path, "rb") as fin, open(dst_path, "wb") as fout:
            return self.encrypt_stream(
                in_stream=fin,
                out_stream=fout,
                dek=dek,
                tenant_id=tenant_id,
                record_id=record_id,
                attachment_id=attachment_id,
                filename=filename,
                content_type=content_type,
                capsule_id=capsule_id,
            )

    def decrypt_file(
        self,
        src_path: str,
        dst_path: str,
        dek: bytes,
        expected_tenant_id: str,
        expected_record_id: str,
        expected_attachment_id: str,
        expected_plaintext_sha256: Optional[str] = None,
    ) -> dict[str, any]:
        """Convenience method to decrypt a file on disk."""
        with open(src_path, "rb") as fin, open(dst_path, "wb") as fout:
            return self.decrypt_stream(
                in_stream=fin,
                out_stream=fout,
                dek=dek,
                expected_tenant_id=expected_tenant_id,
                expected_record_id=expected_record_id,
                expected_attachment_id=expected_attachment_id,
                expected_plaintext_sha256=expected_plaintext_sha256,
            )
