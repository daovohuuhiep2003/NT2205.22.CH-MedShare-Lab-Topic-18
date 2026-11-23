"""
Key Capsule representation for MedShare-Lab.
Wraps Data Encryption Keys (DEK) under Key Encryption Keys (KEK) with cryptographic context binding.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import uuid
from typing import Any, Optional
from medshare.crypto.context import canonicalize_jcs
from medshare.crypto.errors import EnvelopeBoundsExceededError, InvalidEnvelopeError


MAX_CAPSULE_SIZE_BYTES = 64 * 1024  # 64 KB bounds limit for capsules


@dataclass(frozen=True)
class KeyCapsule:
    """
    Cryptographic capsule holding wrapped DEK and metadata.
    Enforces domain separation medshare/wrap/v1 and bound object context.
    """
    capsule_id: str
    capsule_version: int
    tenant_id: str
    kek_id: str
    kek_version: int
    wrapped_dek: str
    bound_object_context: dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.capsule_id or not isinstance(self.capsule_id, str):
            raise InvalidEnvelopeError("capsule_id must be a non-empty string")
        if not isinstance(self.capsule_version, int) or self.capsule_version < 1:
            raise InvalidEnvelopeError("capsule_version must be a positive integer")
        if not self.tenant_id or not isinstance(self.tenant_id, str):
            raise InvalidEnvelopeError("tenant_id must be a non-empty string")
        if not self.kek_id or not isinstance(self.kek_id, str):
            raise InvalidEnvelopeError("kek_id must be a non-empty string")
        if not isinstance(self.kek_version, int) or self.kek_version < 1:
            raise InvalidEnvelopeError("kek_version must be a positive integer")
        if not self.wrapped_dek or not isinstance(self.wrapped_dek, str):
            raise InvalidEnvelopeError("wrapped_dek must be a non-empty string")
        if not isinstance(self.bound_object_context, dict):
            raise InvalidEnvelopeError("bound_object_context must be a dictionary")

    def compute_wrap_context_bytes(self) -> bytes:
        """
        Computes canonical RFC 8785 (JCS) representation of bound context
        to use as authenticated context (AAD) for KMS wrapping/unwrapping.
        """
        # Ensure domain tag is bound
        context_copy = dict(self.bound_object_context)
        if "domain" not in context_copy:
            context_copy["domain"] = "medshare/wrap/v1"
        if "tenant_id" not in context_copy:
            context_copy["tenant_id"] = self.tenant_id
        return canonicalize_jcs(context_copy)

    def to_dict(self) -> dict[str, Any]:
        """Convert capsule to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize capsule to compact JSON with bounds check."""
        data_str = json.dumps(self.to_dict(), separators=(",", ":"), ensure_ascii=True)
        if len(data_str.encode("utf-8")) > MAX_CAPSULE_SIZE_BYTES:
            raise EnvelopeBoundsExceededError(
                f"Serialized KeyCapsule exceeds maximum size limit ({MAX_CAPSULE_SIZE_BYTES} bytes)"
            )
        return data_str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KeyCapsule":
        """Reconstruct KeyCapsule from dictionary."""
        required_keys = {
            "capsule_id", "capsule_version", "tenant_id",
            "kek_id", "kek_version", "wrapped_dek", "bound_object_context"
        }
        missing = required_keys - set(data.keys())
        if missing:
            raise InvalidEnvelopeError(f"Missing required fields for KeyCapsule: {missing}")

        return cls(
            capsule_id=str(data["capsule_id"]),
            capsule_version=int(data["capsule_version"]),
            tenant_id=str(data["tenant_id"]),
            kek_id=str(data["kek_id"]),
            kek_version=int(data["kek_version"]),
            wrapped_dek=str(data["wrapped_dek"]),
            bound_object_context=dict(data["bound_object_context"]),
            created_at=str(data.get("created_at", datetime.now(timezone.utc).isoformat())),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "KeyCapsule":
        """Parse KeyCapsule from JSON string with size bounds checking."""
        if not json_str:
            raise InvalidEnvelopeError("JSON string cannot be empty")
        raw_bytes = json_str.encode("utf-8")
        if len(raw_bytes) > MAX_CAPSULE_SIZE_BYTES:
            raise EnvelopeBoundsExceededError(
                f"KeyCapsule JSON size ({len(raw_bytes)} bytes) exceeds limit ({MAX_CAPSULE_SIZE_BYTES} bytes)"
            )
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as ex:
            raise InvalidEnvelopeError(f"Malformed KeyCapsule JSON: {ex}") from ex
        if not isinstance(data, dict):
            raise InvalidEnvelopeError("Parsed KeyCapsule JSON must be an object")
        return cls.from_dict(data)

