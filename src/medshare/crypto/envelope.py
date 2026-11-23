"""
MedShare-Lab: Field-level Envelope Format & Serialization (Topic 18 — NT2205.11.CH).
Định dạng bản mã có cấu trúc cho từng trường dữ liệu nhạy cảm.

Cấu trúc Envelope:
- Header: format_version, data_suite_id, tenant_id, object_kind, record_id,
          field_id, data_version, data_policy_version, dek_id, capsule_id
- Crypto Payload: nonce (12 bytes), ciphertext (N bytes), tag (16 bytes)
"""

import base64
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from medshare.crypto.context import CryptoContext
from medshare.crypto.errors import EnvelopeValidationError

NONCE_LENGTH_BYTES = 12
TAG_LENGTH_BYTES = 16
MAX_CIPHERTEXT_BYTES = 10 * 1024 * 1024  # 10 MB limit chống memory DoS


@dataclass(frozen=True)
class FieldEnvelope:
    tenant_id: str
    record_id: str
    field_id: str
    dek_id: str
    nonce: bytes
    ciphertext: bytes
    tag: bytes
    capsule_id: Optional[str] = None
    object_kind: str = "ehr_record"
    data_version: int = 1
    data_policy_version: int = 1
    format_version: int = 1
    data_suite_id: str = "AES256GCM-v1"

    def __post_init__(self):
        # Kiểm tra tính toàn vẹn và giới hạn kích thước (Bounds checking)
        if self.format_version != 1:
            raise EnvelopeValidationError(f"Invalid format_version: {self.format_version} (Expected: 1)")
        if self.data_suite_id != "AES256GCM-v1":
            raise EnvelopeValidationError(f"Invalid data_suite_id: {self.data_suite_id} (Expected: AES256GCM-v1)")
        if len(self.nonce) != NONCE_LENGTH_BYTES:
            raise EnvelopeValidationError(f"Nonce length must be exactly {NONCE_LENGTH_BYTES} bytes, got {len(self.nonce)}")
        if len(self.tag) != TAG_LENGTH_BYTES:
            raise EnvelopeValidationError(f"Authentication tag must be exactly {TAG_LENGTH_BYTES} bytes, got {len(self.tag)}")
        if len(self.ciphertext) > MAX_CIPHERTEXT_BYTES:
            raise EnvelopeValidationError(f"Ciphertext size exceeds maximum allowable bound ({MAX_CIPHERTEXT_BYTES} bytes)")

    def get_context(self) -> CryptoContext:
        """Trích xuất CryptoContext đại diện cho Envelope này."""
        return CryptoContext(
            tenant_id=self.tenant_id,
            record_id=self.record_id,
            field_id=self.field_id,
            dek_id=self.dek_id,
            object_kind=self.object_kind,
            data_version=self.data_version,
            data_policy_version=self.data_policy_version,
            format_version=self.format_version,
            data_suite_id=self.data_suite_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Tuần tự hóa thành dictionary (mã hóa binary sang Base64 chuẩn)."""
        return {
            "format_version": self.format_version,
            "data_suite_id": self.data_suite_id,
            "tenant_id": self.tenant_id,
            "object_kind": self.object_kind,
            "record_id": self.record_id,
            "field_id": self.field_id,
            "data_version": self.data_version,
            "data_policy_version": self.data_policy_version,
            "dek_id": self.dek_id,
            "capsule_id": self.capsule_id,
            "nonce": base64.b64encode(self.nonce).decode("ascii"),
            "ciphertext": base64.b64encode(self.ciphertext).decode("ascii"),
            "tag": base64.b64encode(self.tag).decode("ascii"),
        }

    def to_json(self) -> str:
        """Tuần tự hóa thành chuỗi JSON nhỏ gọn."""
        return json.dumps(self.to_dict(), separators=(",", ":"), ensure_ascii=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FieldEnvelope":
        """Giải tuần tự hóa từ dictionary với kiểm tra kiểu dữ liệu và giải mã Base64."""
        required_fields = [
            "format_version", "data_suite_id", "tenant_id", "record_id",
            "field_id", "dek_id", "nonce", "ciphertext", "tag"
        ]
        for f in required_fields:
            if f not in data:
                raise EnvelopeValidationError(f"Missing required envelope field: {f}")

        try:
            nonce_bytes = base64.b64decode(data["nonce"], validate=True)
            ct_bytes = base64.b64decode(data["ciphertext"], validate=True)
            tag_bytes = base64.b64decode(data["tag"], validate=True)
        except Exception as e:
            raise EnvelopeValidationError(f"Invalid base64 encoding in crypto payload: {e}")

        return cls(
            format_version=int(data["format_version"]),
            data_suite_id=str(data["data_suite_id"]),
            tenant_id=str(data["tenant_id"]),
            object_kind=str(data.get("object_kind", "ehr_record")),
            record_id=str(data["record_id"]),
            field_id=str(data["field_id"]),
            data_version=int(data.get("data_version", 1)),
            data_policy_version=int(data.get("data_policy_version", 1)),
            dek_id=str(data["dek_id"]),
            capsule_id=data.get("capsule_id"),
            nonce=nonce_bytes,
            ciphertext=ct_bytes,
            tag=tag_bytes,
        )

    @classmethod
    def from_json(cls, raw_json: str) -> "FieldEnvelope":
        """Giải tuần tự hóa từ chuỗi JSON."""
        try:
            d = json.loads(raw_json)
        except Exception as e:
            raise EnvelopeValidationError(f"Malformed JSON envelope: {e}")
        return cls.from_dict(d)
