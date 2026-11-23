"""
MedShare-Lab: Cryptography Module Exports (Topic 18 — NT2205.11.CH).
"""

from medshare.crypto.blind_index import (
    compute_blind_index,
    derive_search_key,
    normalize_field_value,
    validate_equality_query,
)
from medshare.crypto.context import CryptoContext
from medshare.crypto.engine import FieldCipherEngine, generate_dek
from medshare.crypto.envelope import FieldEnvelope
from medshare.crypto.file_cipher import FILE_CIPHER_MAGIC, MedicalFileCipher
from medshare.crypto.he_client import (
    DifferencingAttackError,
    HeBfvClient,
    HomomorphicEncryptionError,
)
from medshare.crypto.abe_client import (
    AbeClient,
    CpAbeError,
    PolicyNotSatisfiedError,
    CollusionVulnerabilityError,
)
from medshare.crypto.errors import (
    AccessDeniedError,
    ContextMismatchError,
    CryptoError,
    DecryptionIntegrityError,
    EnvelopeValidationError,
    InvalidKeyError,
    UnsupportedQueryError,
)

__all__ = [
    "CryptoContext",
    "FieldEnvelope",
    "FieldCipherEngine",
    "MedicalFileCipher",
    "HeBfvClient",
    "HomomorphicEncryptionError",
    "DifferencingAttackError",
    "AbeClient",
    "CpAbeError",
    "PolicyNotSatisfiedError",
    "CollusionVulnerabilityError",
    "FILE_CIPHER_MAGIC",
    "generate_dek",
    "compute_blind_index",
    "derive_search_key",
    "normalize_field_value",
    "validate_equality_query",
    "CryptoError",
    "InvalidKeyError",
    "EnvelopeValidationError",
    "ContextMismatchError",
    "DecryptionIntegrityError",
    "AccessDeniedError",
    "UnsupportedQueryError",
]

