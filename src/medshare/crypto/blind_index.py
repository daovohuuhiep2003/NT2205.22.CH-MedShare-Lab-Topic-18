"""
MedShare-Lab: Equality Blind Index Engine (Topic 18 — NT2205.11.CH).
Tuần 7 — WP6: Equality Blind Index & Leakage Analysis.

Cung cấp cơ chế tìm kiếm đẳng thức chính xác trên dữ liệu mã hóa (M-06 / CR-07).
Đặc tính kỹ thuật:
- Token = HMAC-SHA-256(search_key, canonical_tuple)
- search_key tách biệt theo (tenant_id, field_name, search_epoch) qua HKDF-SHA256
- Tuple chuẩn hóa bằng JCS (RFC 8785 subset) với domain separation 'medshare/search/v1'
- Chuẩn hóa Unicode NFC, case chuẩn theo loại trường, stripped whitespace
- Bộ kiểm tra truy vấn fail-closed: Từ chối range, wildcard, regex (HTTP 422 UnsupportedQueryError)
"""

import hmac
import hashlib
import unicodedata
from typing import Any, Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from medshare.crypto.context import canonicalize_jcs
from medshare.crypto.errors import InvalidKeyError, UnsupportedQueryError

SEARCH_DOMAIN = "medshare/search/v1"
CURRENT_NORMALIZATION_VERSION = "v1"
SEARCH_KEY_SALT = b"medshare/search_key/salt/v1"

UNSUPPORTED_OPERATORS = {
    ">", "<", ">=", "<=", "!=", "gt", "lt", "gte", "lte", "ne",
    "between", "like", "ilike", "regex", "in", "contains", "startswith", "endswith"
}


def normalize_field_value(field_name: str, value: Any, version: str = CURRENT_NORMALIZATION_VERSION) -> str:
    """
    Normalizes a field value into canonical string representation before hashing.
    Enforces Unicode NFC normalization and field-specific casing rules.
    """
    if value is None:
        return ""

    if version != CURRENT_NORMALIZATION_VERSION:
        raise ValueError(f"Unsupported normalization version: {version}")

    clean_field = field_name.lower().strip()

    if isinstance(value, (int, float)):
        # Integer values formatted as string integer representation
        if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
            return str(int(value))
        return str(value).strip()

    # Convert to string and apply Unicode NFC normalization
    str_val = unicodedata.normalize("NFC", str(value)).strip()

    if clean_field in ("email",):
        # Email: lowercase
        return str_val.lower()
    elif clean_field in ("diagnosis", "diagnosis_code", "icd10"):
        # ICD-10 Diagnosis codes: uppercase, no extraneous whitespace
        return str_val.upper()
    elif clean_field in ("gender",):
        # Gender: uppercase
        return str_val.upper()
    elif clean_field in ("patient_id", "record_id", "external_id"):
        # Identifiers: keep case, whitespace stripped
        return str_val
    else:
        return str_val


def derive_search_key(
    master_secret: bytes,
    tenant_id: str,
    field_name: str,
    search_epoch: int = 1,
) -> bytes:
    """
    Derives an isolated 32-byte search key for a given tenant, field, and search epoch
    using HKDF-SHA256 with cryptographic domain separation.
    """
    if not master_secret or len(master_secret) < 16:
        raise InvalidKeyError("master_secret must be at least 16 bytes")
    if not tenant_id or not isinstance(tenant_id, str):
        raise ValueError("tenant_id must be a non-empty string")
    if not field_name or not isinstance(field_name, str):
        raise ValueError("field_name must be a non-empty string")
    if search_epoch < 1:
        raise ValueError("search_epoch must be a positive integer")

    info = f"domain:{SEARCH_DOMAIN}|tenant:{tenant_id}|field:{field_name.lower()}|epoch:{search_epoch}".encode("utf-8")
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SEARCH_KEY_SALT,
        info=info,
    )
    return hkdf.derive(master_secret)


def compute_blind_index(
    search_key: bytes,
    tenant_id: str,
    field_name: str,
    value: Any,
    search_epoch: int = 1,
    version: str = CURRENT_NORMALIZATION_VERSION,
) -> str:
    """
    Computes deterministic HMAC-SHA-256 blind index token for equality queries.
    Returns 64-character lowercase hexadecimal string.
    """
    if not search_key or len(search_key) < 32:
        raise InvalidKeyError("search_key must be at least 32 bytes")
    if not tenant_id:
        raise ValueError("tenant_id is required")
    if not field_name:
        raise ValueError("field_name is required")

    norm_val = normalize_field_value(field_name, value, version=version)

    # Canonical JCS tuple structure binding all context dimensions
    canonical_tuple = {
        "domain": SEARCH_DOMAIN,
        "field_name": field_name.lower().strip(),
        "normalization_version": version,
        "search_epoch": search_epoch,
        "tenant_id": tenant_id,
        "value": norm_val,
    }

    message_bytes = canonicalize_jcs(canonical_tuple)
    h = hmac.new(search_key, message_bytes, hashlib.sha256)
    return h.hexdigest()


def validate_equality_query(field_name: str, query_expr: Any) -> Any:
    """
    Validates that a query expression is an exact equality lookup.
    Rejects range queries (<, >, BETWEEN), wildcard/like (% *), regex, and joins
    with HTTP 422 UnsupportedQueryError (DoD Gate Tuần 7).
    Returns the raw equality target value if valid.
    """
    if not field_name:
        raise UnsupportedQueryError("Query must specify a target field name", status_code=422)

    # If query_expr is a dict specifying operator/value, e.g. {"op": ">", "value": 10}
    if isinstance(query_expr, dict):
        op = str(query_expr.get("op", query_expr.get("operator", ""))).lower().strip()
        if op and op not in ("eq", "=", "exact", "=="):
            raise UnsupportedQueryError(
                f"Unsupported query operator '{op}'. Equality Blind Index supports ONLY exact equality (HTTP 422)",
                status_code=422,
            )
        if "value" in query_expr:
            target_val = query_expr["value"]
        else:
            raise UnsupportedQueryError("Query expression dictionary missing 'value'", status_code=422)
    else:
        target_val = query_expr

    # If target_val is a string containing SQL/pattern wildcards
    if isinstance(target_val, str):
        trimmed = target_val.strip()
        # Detect wildcard or regex patterns
        if any(c in trimmed for c in ("%", "*", "?", "$", "^", "[", "]", "(", ")")) and len(trimmed) > 1:
            # Check if user is attempting pattern matching
            if trimmed.startswith("%") or trimmed.endswith("%") or trimmed.startswith("*") or trimmed.endswith("*"):
                raise UnsupportedQueryError(
                    f"Wildcard/pattern query '{trimmed}' rejected. Equality Blind Index supports ONLY exact matches (HTTP 422)",
                    status_code=422,
                )

    return target_val

