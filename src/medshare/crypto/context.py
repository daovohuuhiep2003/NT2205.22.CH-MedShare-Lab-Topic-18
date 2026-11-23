"""
MedShare-Lab: Crypto Context & Immutable AAD Binding (Topic 18 — NT2205.11.CH).
Đảm bảo tính gắn kết ngữ cảnh bất biến (M-02 Data AEAD + Context Binding).

Công thức AAD:
AAD = CanonicalJSON(domain, format_version, data_suite_id, tenant_id, object_kind,
                    record_id, field_id, data_version, data_policy_version, dek_id)
"""

import json
from dataclasses import dataclass
from typing import Dict

from medshare.crypto.errors import EnvelopeValidationError

SUPPORTED_DOMAINS = {"medshare/data/v1"}
SUPPORTED_SUITES = {"AES256GCM-v1"}
SUPPORTED_VERSIONS = {1}


def canonicalize_jcs(data: dict) -> bytes:
    """
    JSON Canonicalization Scheme (RFC 8785 subset):
    - Sorted keys
    - Compact separators without whitespace
    - UTF-8 encoding
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


@dataclass(frozen=True)
class CryptoContext:
    tenant_id: str
    record_id: str
    field_id: str
    dek_id: str
    object_kind: str = "ehr_record"
    data_version: int = 1
    data_policy_version: int = 1
    domain: str = "medshare/data/v1"
    format_version: int = 1
    data_suite_id: str = "AES256GCM-v1"

    def __post_init__(self):
        # Kiểm tra tính hợp lệ của ngữ cảnh
        if self.domain not in SUPPORTED_DOMAINS:
            raise EnvelopeValidationError(f"Unsupported domain: {self.domain}")
        if self.format_version not in SUPPORTED_VERSIONS:
            raise EnvelopeValidationError(f"Unsupported format_version: {self.format_version}")
        if self.data_suite_id not in SUPPORTED_SUITES:
            raise EnvelopeValidationError(f"Unsupported data_suite_id: {self.data_suite_id}")
        if not self.tenant_id or not isinstance(self.tenant_id, str):
            raise EnvelopeValidationError("tenant_id must be a non-empty string")
        if not self.record_id or not isinstance(self.record_id, str):
            raise EnvelopeValidationError("record_id must be a non-empty string")
        if not self.field_id or not isinstance(self.field_id, str):
            raise EnvelopeValidationError("field_id must be a non-empty string")
        if not self.dek_id or not isinstance(self.dek_id, str):
            raise EnvelopeValidationError("dek_id must be a non-empty string")

    def to_canonical_dict(self) -> Dict[str, any]:
        """Chuyển thành dictionary với khóa chuẩn hóa."""
        return {
            "data_policy_version": self.data_policy_version,
            "data_suite_id": self.data_suite_id,
            "data_version": self.data_version,
            "dek_id": self.dek_id,
            "domain": self.domain,
            "field_id": self.field_id,
            "format_version": self.format_version,
            "object_kind": self.object_kind,
            "record_id": self.record_id,
            "tenant_id": self.tenant_id,
        }

    def compute_canonical_aad(self) -> bytes:
        """
        Sinh ra mảng byte AAD xác thực (Additional Authenticated Data).
        Sử dụng JCS (JSON Canonicalization Scheme - RFC 8785):
        - Sorted keys
        - Compact separators (',', ':')
        - UTF-8 encoding
        """
        canonical_str = json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return canonical_str.encode("utf-8")

