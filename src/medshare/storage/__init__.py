"""
MedShare-Lab: Encrypted Storage & Data Access Layer (Topic 18 — NT2205.11.CH).
Zone Z2 Untrusted Storage Tier (MongoDB 7.0).
"""

from medshare.storage.dal import (
    EncryptedAttachmentMeta,
    EncryptedPatientRecord,
    MongoStorage,
)
from medshare.storage.minio_dal import (
    MinioStorage,
    MinioStorageError,
    ObjectNotFoundError,
)

__all__ = [
    "EncryptedAttachmentMeta",
    "EncryptedPatientRecord",
    "MongoStorage",
    "MinioStorage",
    "MinioStorageError",
    "ObjectNotFoundError",
]
