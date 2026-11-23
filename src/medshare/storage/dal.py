"""
Data Access Layer (DAL) for MedShare-Lab Encrypted Storage.
Interacts with MongoDB 7.0 in Zone Z2.
Stores only FieldEnvelopes, KeyCapsules, and HMAC Blind Index tokens.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Optional
import pymongo
from pymongo.collection import Collection
from pymongo.database import Database

from medshare.broker.capsule import KeyCapsule
from medshare.crypto.envelope import FieldEnvelope


@dataclass
class EncryptedPatientRecord:
    """Data container for an encrypted patient record in storage."""
    record_id: str
    tenant_id: str
    data_version: int
    capsule_id: str
    patient_id_bidx: str
    envelopes: dict[str, FieldEnvelope]
    diagnosis_bidx: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class EncryptedAttachmentMeta:
    """Metadata container for an encrypted medical file attachment (DICOM, CT/MRI, X-ray, Ultrasound, PDF)."""
    attachment_id: str
    tenant_id: str
    record_id: str
    modality: str  # e.g., "XRAY", "CT", "MRI", "ULTRASOUND", "LAB_REPORT"
    filename: str
    content_type: str
    file_size_bytes: int
    s3_bucket: str
    s3_key: str
    capsule_id: str
    plaintext_sha256: str
    ciphertext_sha256: str
    department: str = "GENERAL"
    sensitivity: str = "CONFIDENTIAL"
    created_at: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "attachment_id": self.attachment_id,
            "tenant_id": self.tenant_id,
            "record_id": self.record_id,
            "modality": self.modality,
            "filename": self.filename,
            "content_type": self.content_type,
            "file_size_bytes": self.file_size_bytes,
            "s3_bucket": self.s3_bucket,
            "s3_key": self.s3_key,
            "capsule_id": self.capsule_id,
            "plaintext_sha256": self.plaintext_sha256,
            "ciphertext_sha256": self.ciphertext_sha256,
            "department": self.department,
            "sensitivity": self.sensitivity,
            "created_at": self.created_at or datetime.now(timezone.utc).isoformat(),
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EncryptedAttachmentMeta":
        return cls(
            attachment_id=data["attachment_id"],
            tenant_id=data["tenant_id"],
            record_id=data["record_id"],
            modality=data.get("modality", "OTHER"),
            filename=data.get("filename", "unknown"),
            content_type=data.get("content_type", "application/octet-stream"),
            file_size_bytes=data.get("file_size_bytes", 0),
            s3_bucket=data["s3_bucket"],
            s3_key=data["s3_key"],
            capsule_id=data["capsule_id"],
            plaintext_sha256=data.get("plaintext_sha256", ""),
            ciphertext_sha256=data.get("ciphertext_sha256", ""),
            department=data.get("department", "GENERAL"),
            sensitivity=data.get("sensitivity", "CONFIDENTIAL"),
            created_at=data.get("created_at"),
            metadata=data.get("metadata", {}),
        )


class MongoStorage:
    """MongoDB 7.0 storage implementation for encrypted records."""

    def __init__(
        self,
        uri: str = "mongodb://medshare_dba:dba_secret_dev_pass@localhost:27017/?authSource=admin",
        db_name: str = "medshare_db",
    ):
        self.client = pymongo.MongoClient(uri)
        self.db: Database = self.client[db_name]
        self.capsules_col: Collection = self.db["key_capsules"]
        self.patients_col: Collection = self.db["encrypted_patients"]
        self.search_col: Collection = self.db["search_index"]
        self.attachments_col: Collection = self.db["patient_attachments"]

    def initialize_indexes(self) -> None:
        """Sets up unique and lookup indexes."""
        self.capsules_col.create_index([("capsule_id", pymongo.ASCENDING)], unique=True)
        self.capsules_col.create_index([("tenant_id", pymongo.ASCENDING)])
        self.patients_col.create_index([("record_id", pymongo.ASCENDING)], unique=True)
        self.patients_col.create_index([("tenant_id", pymongo.ASCENDING), ("patient_id_bidx", pymongo.ASCENDING)])
        self.search_col.create_index(
            [
                ("tenant_id", pymongo.ASCENDING),
                ("field_name", pymongo.ASCENDING),
                ("search_epoch", pymongo.ASCENDING),
                ("token", pymongo.ASCENDING),
            ]
        )
        self.attachments_col.create_index([("attachment_id", pymongo.ASCENDING)], unique=True)
        self.attachments_col.create_index([("tenant_id", pymongo.ASCENDING), ("record_id", pymongo.ASCENDING)])

    def save_patient(self, record: EncryptedPatientRecord, capsule: KeyCapsule) -> None:
        """Saves capsule, record, and blind index entries to MongoDB."""
        self.capsules_col.update_one(
            {"capsule_id": capsule.capsule_id},
            {"$set": capsule.to_dict()},
            upsert=True,
        )

        doc = {
            "record_id": record.record_id,
            "tenant_id": record.tenant_id,
            "data_version": record.data_version,
            "capsule_id": capsule.capsule_id,
            "patient_id_bidx": record.patient_id_bidx,
            "diagnosis_bidx": record.diagnosis_bidx,
            "envelopes": {k: v.to_dict() for k, v in record.envelopes.items()},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.patients_col.update_one(
            {"record_id": record.record_id},
            {"$set": doc},
            upsert=True,
        )

        # Upsert search_index entries
        self.search_col.delete_many({"record_id": record.record_id})
        search_docs = [
            {
                "tenant_id": record.tenant_id,
                "field_name": "patient_id",
                "search_epoch": 1,
                "token": record.patient_id_bidx,
                "record_id": record.record_id,
            }
        ]
        if record.diagnosis_bidx:
            search_docs.append({
                "tenant_id": record.tenant_id,
                "field_name": "diagnosis",
                "search_epoch": 1,
                "token": record.diagnosis_bidx,
                "record_id": record.record_id,
            })
        self.search_col.insert_many(search_docs)

    def delete_patient(self, record_id: str, tenant_id: str) -> bool:
        """Deletes record and search entries from MongoDB."""
        self.search_col.delete_many({"record_id": record_id, "tenant_id": tenant_id})
        res = self.patients_col.delete_one({"record_id": record_id, "tenant_id": tenant_id})
        return res.deleted_count > 0

    def search_by_blind_index(
        self, tenant_id: str, field_name: str, token: str, search_epoch: int = 1
    ) -> list[tuple[EncryptedPatientRecord, KeyCapsule]]:
        """Searches matching records in MongoDB via blind index."""
        cursor = self.search_col.find({
            "tenant_id": tenant_id,
            "field_name": field_name.lower().strip(),
            "search_epoch": search_epoch,
            "token": token,
        })
        results = []
        for doc in cursor:
            item = self.get_patient(doc["record_id"], tenant_id)
            if item:
                results.append(item)
        return results

    def get_patient(self, record_id: str, tenant_id: str) -> Optional[tuple[EncryptedPatientRecord, KeyCapsule]]:
        """Retrieves record and capsule from MongoDB."""
        doc = self.patients_col.find_one({"record_id": record_id, "tenant_id": tenant_id})
        if not doc:
            return None
        cap_doc = self.capsules_col.find_one({"capsule_id": doc["capsule_id"]})
        if not cap_doc:
            return None

        capsule = KeyCapsule.from_dict(cap_doc)
        envelopes = {k: FieldEnvelope.from_dict(v) for k, v in doc["envelopes"].items()}
        record = EncryptedPatientRecord(
            record_id=doc["record_id"],
            tenant_id=doc["tenant_id"],
            data_version=doc.get("data_version", 1),
            capsule_id=doc["capsule_id"],
            patient_id_bidx=doc["patient_id_bidx"],
            diagnosis_bidx=doc.get("diagnosis_bidx"),
            envelopes=envelopes,
        )
        return record, capsule

    def count_records(self, tenant_id: Optional[str] = None) -> int:
        """Returns total records in MongoDB."""
        filter_doc = {"tenant_id": tenant_id} if tenant_id else {}
        return self.patients_col.count_documents(filter_doc)

    def get_patient_tenant(self, record_id: str) -> Optional[str]:
        """Looks up the tenant_id of a record across all tenants (e.g. for cross-tenant probe detection)."""
        doc = self.patients_col.find_one({"record_id": record_id}, {"tenant_id": 1})
        return doc["tenant_id"] if doc and "tenant_id" in doc else None

    def save_attachment(self, attachment: EncryptedAttachmentMeta, capsule: KeyCapsule) -> None:
        """Saves encrypted attachment metadata and its associated key capsule."""
        self.capsules_col.update_one(
            {"capsule_id": capsule.capsule_id},
            {"$set": capsule.to_dict()},
            upsert=True,
        )
        self.attachments_col.update_one(
            {"attachment_id": attachment.attachment_id},
            {"$set": attachment.to_dict()},
            upsert=True,
        )

    def get_attachment(
        self, tenant_id: str, attachment_id: str
    ) -> Optional[tuple[EncryptedAttachmentMeta, KeyCapsule]]:
        """Retrieves attachment metadata and capsule from MongoDB."""
        att_doc = self.attachments_col.find_one({
            "attachment_id": attachment_id,
            "tenant_id": tenant_id,
        })
        if not att_doc:
            return None

        cap_doc = self.capsules_col.find_one({"capsule_id": att_doc["capsule_id"]})
        if not cap_doc:
            return None

        capsule = KeyCapsule.from_dict(cap_doc)
        attachment = EncryptedAttachmentMeta.from_dict(att_doc)
        return attachment, capsule

    def list_attachments(self, tenant_id: str, record_id: str) -> list[EncryptedAttachmentMeta]:
        """Lists all attachments for a specific patient record under a tenant."""
        cursor = self.attachments_col.find({
            "tenant_id": tenant_id,
            "record_id": record_id,
        }).sort("created_at", pymongo.DESCENDING)
        return [EncryptedAttachmentMeta.from_dict(doc) for doc in cursor]

    def delete_attachment(self, tenant_id: str, attachment_id: str) -> bool:
        """Deletes an attachment metadata document from MongoDB."""
        res = self.attachments_col.delete_one({
            "attachment_id": attachment_id,
            "tenant_id": tenant_id,
        })
        return res.deleted_count > 0


