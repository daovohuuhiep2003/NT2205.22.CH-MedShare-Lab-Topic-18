"""
Trusted Crypto Gateway Service (Zone Z1).
Acts as API Entry Point and Gateway Policy Enforcement Point (PEP).
Coordinates ABAC evaluation, Key Broker requests, field envelope encryption/decryption,
storage persistence, and safe field projection.
"""

from datetime import datetime, timezone
import hashlib
import io
from typing import Any, BinaryIO, Optional
import uuid

from medshare.broker.broker import KeyBroker
from medshare.crypto.blind_index import (
    compute_blind_index,
    normalize_field_value,
    validate_equality_query,
)
from medshare.crypto.context import CryptoContext
from medshare.crypto.engine import FieldCipherEngine
from medshare.crypto.file_cipher import MedicalFileCipher
from medshare.crypto.errors import AccessDeniedError, UnsupportedQueryError
from medshare.policy.abac import (
    AbacPolicyEngine,
    Action,
    EnvironmentContext,
    ObjectAttributes,
    PolicyDecision,
    SubjectAttributes,
)
from medshare.storage.dal import EncryptedAttachmentMeta, EncryptedPatientRecord, MongoStorage
from medshare.storage.minio_dal import MinioStorage



class ClinicalGatewayService:
    """
    Gateway Service combining ABAC PEP, Crypto Engine, Key Broker, and DAL.
    Enforces least privilege field projection and immutable audit trail.
    """

    def __init__(
        self,
        pdp: AbacPolicyEngine,
        broker: KeyBroker,
        engine: FieldCipherEngine,
        storage: Any,
        minio_storage: Optional[MinioStorage] = None,
        file_cipher: Optional[MedicalFileCipher] = None,
    ):
        self.pdp = pdp
        self.broker = broker
        self.engine = engine
        self.storage = storage
        self.minio_storage = minio_storage
        self.file_cipher = file_cipher if file_cipher is not None else MedicalFileCipher()
        # Audit log storage in Zone Z1 (F9 metadata only)
        self.audit_log: list[dict[str, Any]] = []

    def _log_audit_event(
        self,
        operation: str,
        subject: SubjectAttributes,
        record_id: str,
        outcome: str,
        reason: str,
        is_break_glass: bool = False,
    ) -> None:
        """Logs metadata-only audit entry conforming to F9 (Zone Z3)."""
        subject_hash = hashlib.sha256(f"{subject.user_id}:{subject.tenant_id}".encode()).hexdigest()
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "subject_hash": subject_hash,
            "subject_role": subject.role,
            "tenant_id": subject.tenant_id,
            "record_id": record_id,
            "outcome": outcome,
            "reason": reason,
            "is_break_glass": is_break_glass,
        }
        self.audit_log.append(event)

    def ingest_patient_record(
        self,
        subject: SubjectAttributes,
        patient_data: dict[str, Any],
        env: Optional[EnvironmentContext] = None,
    ) -> dict[str, Any]:
        """
        Ingests a new patient record (Write Pipeline W1).
        Enforces Gateway PEP WRITE evaluation before key release or encryption.
        """
        if env is None:
            env = EnvironmentContext()

        record_id = patient_data["record_id"]
        tenant_id = subject.tenant_id
        department = patient_data.get("department", subject.department)

        # 1. Gateway PEP: Evaluate WRITE permission
        obj_attrs = ObjectAttributes(
            record_id=record_id,
            tenant_id=tenant_id,
            department=department,
            data_class="clinical",
        )
        decision = self.pdp.evaluate(subject, obj_attrs, Action.WRITE, env=env)
        if not decision.is_permitted:
            self._log_audit_event("WRITE", subject, record_id, "DENIED", decision.reason)
            raise AccessDeniedError(f"Gateway PEP: Access denied for WRITE operation: {decision.reason}")

        # 2. Key Broker: Issue fresh DEK & KeyCapsule
        extra_ctx = {"department": department}
        dek, capsule = self.broker.issue_dek_and_capsule(
            tenant_id=tenant_id,
            record_id=record_id,
            data_class="clinical",
            extra_context=extra_ctx,
        )

        # 3. FieldCipherEngine: Encrypt each clinical field under bound AAD
        envelopes = {}
        for field_name in ["name", "dob", "gender", "diagnosis", "notes"]:
            raw_val = patient_data.get(field_name)
            if raw_val is not None:
                ctx = CryptoContext(
                    tenant_id=tenant_id,
                    record_id=record_id,
                    field_id=field_name,
                    dek_id=capsule.capsule_id,
                )
                envelopes[field_name] = self.engine.encrypt_field(
                    raw_val, ctx, dek, capsule_id=capsule.capsule_id
                )

        # 4. Generate Blind Index Tokens for Equality Search (M-06 / CR-07)
        patient_id_raw = patient_data.get("patient_id", record_id)
        pid_search_key = self.broker.get_search_key(tenant_id, "patient_id", search_epoch=1)
        pid_bidx = compute_blind_index(pid_search_key, tenant_id, "patient_id", patient_id_raw, search_epoch=1)

        diag_bidx = None
        if "diagnosis" in patient_data and patient_data["diagnosis"]:
            diag_search_key = self.broker.get_search_key(tenant_id, "diagnosis", search_epoch=1)
            diag_bidx = compute_blind_index(diag_search_key, tenant_id, "diagnosis", patient_data["diagnosis"], search_epoch=1)


        # 5. Persist Encrypted Record to Zone Z2 Storage
        record = EncryptedPatientRecord(
            record_id=record_id,
            tenant_id=tenant_id,
            data_version=1,
            capsule_id=capsule.capsule_id,
            patient_id_bidx=pid_bidx,
            diagnosis_bidx=diag_bidx,
            envelopes=envelopes,
        )
        self.storage.save_patient(record, capsule)

        # 6. Audit Trail
        self._log_audit_event("WRITE", subject, record_id, "PERMITTED", "Record ingested successfully")

        return {
            "status": "INGESTED",
            "record_id": record_id,
            "capsule_id": capsule.capsule_id,
            "fields_encrypted": list(envelopes.keys()),
        }

    def read_patient_record(
        self,
        subject: SubjectAttributes,
        record_id: str,
        env: Optional[EnvironmentContext] = None,
    ) -> dict[str, Any]:
        """
        Retrieves and decrypts a patient record (Read Pipeline W2).
        Enforces Dual PEP:
        1. Gateway PEP checks ABAC before fetching data.
        2. Broker PEP verifies unwrap request independently.
        3. Field Projection filters unauthorized fields according to PDP decision.
        """
        if env is None:
            env = EnvironmentContext()

        # 1. Fetch encrypted record and capsule from Storage
        loaded = self.storage.get_patient(record_id=record_id, tenant_id=subject.tenant_id)
        if loaded is None:
            # Check if record exists in another tenant (Cross-tenant probe)
            target_tenant = None
            if hasattr(self.storage, "get_patient_tenant"):
                target_tenant = self.storage.get_patient_tenant(record_id)
            elif hasattr(self.storage, "direct_dba_raw_query"):
                raw_check = self.storage.direct_dba_raw_query(
                    "SELECT tenant_id FROM encrypted_patients WHERE record_id = %s;", (record_id,)
                )
                if raw_check:
                    target_tenant = raw_check[0][0]

            if target_tenant:
                self._log_audit_event("READ", subject, record_id, "DENIED", "Cross-tenant access attempted")
                raise AccessDeniedError(
                    f"Gateway PEP: Cross-tenant access blocked. Record belongs to '{target_tenant}' (TC-03)"
                )
            raise ValueError(f"Patient record '{record_id}' not found")

        record, capsule = loaded
        obj_dept = capsule.bound_object_context.get("department", "CARDIOLOGY")

        # 2. Gateway PEP: Evaluate READ permission
        obj_attrs = ObjectAttributes(
            record_id=record_id,
            tenant_id=subject.tenant_id,
            department=obj_dept,
            data_class="clinical",
        )
        decision: PolicyDecision = self.pdp.evaluate(subject, obj_attrs, Action.READ, env=env)
        if not decision.is_permitted:
            self._log_audit_event("READ", subject, record_id, "DENIED", decision.reason)
            raise AccessDeniedError(f"Gateway PEP: Access denied for READ operation: {decision.reason}")

        # 3. Key Broker PEP: Request unwrap DEK
        requesting_context = {
            "tenant_id": subject.tenant_id,
            "record_id": record_id,
            "subject": subject,
            "env": env,
        }
        unwrapped_dek = self.broker.unwrap_dek(capsule, requesting_context)

        # 4. Decrypt allowed fields & Apply Field Projection
        decrypted_fields: dict[str, Any] = {}
        for field_name, env_obj in record.envelopes.items():
            if field_name in decision.allowed_fields:
                ctx = CryptoContext(
                    tenant_id=subject.tenant_id,
                    record_id=record_id,
                    field_id=field_name,
                    dek_id=capsule.capsule_id,
                )
                pt_bytes = self.engine.decrypt_field(env_obj, ctx, unwrapped_dek)
                decrypted_fields[field_name] = pt_bytes.decode("utf-8")
            else:
                # Omit / mask unauthorized field
                decrypted_fields[field_name] = "[REDACTED_BY_POLICY]"

        # 5. Audit Trail
        self._log_audit_event(
            "READ",
            subject,
            record_id,
            "PERMITTED",
            decision.reason,
            is_break_glass=decision.is_break_glass,
        )

        return {
            "record_id": record_id,
            "tenant_id": subject.tenant_id,
            "fields": decrypted_fields,
            "allowed_fields": list(decision.allowed_fields),
            "is_break_glass": decision.is_break_glass,
            "policy_version": decision.policy_version,
        }

    def search_patients_by_equality(
        self,
        subject: SubjectAttributes,
        field_name: str,
        query_expr: Any,
        search_epoch: int = 1,
        env: Optional[EnvironmentContext] = None,
    ) -> list[dict[str, Any]]:
        """
        Executes an exact equality search using HMAC blind index (Pipeline W2 / F4).
        Enforces:
        1. Query validation: Rejects range, pattern, wildcard queries with HTTP 422 (TC-15 Gate).
        2. Gateway PEP: Evaluates READ permission before query execution.
        3. Blind Token Derivation: Uses tenant/field/epoch isolated search key.
        4. DAL Search: Queries search_index in Zone Z2 storage.
        5. Post-Filter Verification: Decrypts candidate records to verify exact match,
           filtering out collisions or active cloud tampering (TC-17).
        6. Field Projection: Redacts unauthorized fields according to PDP decision.
        """
        if env is None:
            env = EnvironmentContext()

        # 1. Validate query expression (Fail-closed on unsupported range/wildcards -> 422)
        target_val = validate_equality_query(field_name, query_expr)

        # 2. Gateway PEP: Evaluate READ permission
        obj_attrs = ObjectAttributes(
            record_id="*",
            tenant_id=subject.tenant_id,
            department=subject.department,
            data_class="clinical",
        )
        decision: PolicyDecision = self.pdp.evaluate(subject, obj_attrs, Action.READ, env=env)
        if not decision.is_permitted:
            self._log_audit_event("SEARCH", subject, f"field:{field_name}", "DENIED", decision.reason)
            raise AccessDeniedError(f"Gateway PEP: Access denied for SEARCH operation: {decision.reason}")

        # 3. Derive search key and compute Blind Index token
        search_key = self.broker.get_search_key(
            tenant_id=subject.tenant_id,
            field_name=field_name,
            search_epoch=search_epoch,
        )
        norm_val = normalize_field_value(field_name, target_val)
        token = compute_blind_index(
            search_key=search_key,
            tenant_id=subject.tenant_id,
            field_name=field_name,
            value=norm_val,
            search_epoch=search_epoch,
        )

        # 4. Storage DAL lookup (Blind index query in Zone Z2)
        candidates = self.storage.search_by_blind_index(
            tenant_id=subject.tenant_id,
            field_name=field_name,
            token=token,
            search_epoch=search_epoch,
        )

        # 5. Post-Filter Verification & Field Projection at Trusted Gateway (TC-17)
        verified_results = []
        for record, capsule in candidates:
            # Check unwrap DEK via Broker PEP
            requesting_context = {
                "tenant_id": subject.tenant_id,
                "record_id": record.record_id,
                "subject": subject,
                "env": env,
            }
            try:
                unwrapped_dek = self.broker.unwrap_dek(capsule, requesting_context)
            except Exception:
                continue

            # Decrypt the queried field to verify candidate authenticity (TC-17)
            field_env = record.envelopes.get(field_name)
            if field_env is not None:
                ctx = CryptoContext(
                    tenant_id=subject.tenant_id,
                    record_id=record.record_id,
                    field_id=field_name,
                    dek_id=capsule.capsule_id,
                )
                try:
                    pt_bytes = self.engine.decrypt_field(field_env, ctx, unwrapped_dek)
                    decrypted_val = pt_bytes.decode("utf-8")
                except Exception:
                    # Decryption integrity failed; reject tampered candidate
                    continue

                # Verify exact normalized equality (Filters collisions or cloud-injected false rows)
                if normalize_field_value(field_name, decrypted_val) != norm_val:
                    # Active server manipulation or collision detected; reject candidate
                    continue
            elif field_name == "patient_id":
                # For patient_id indexed via token column, verify against bound record token
                if record.patient_id_bidx != token:
                    continue
            else:
                # Field cannot be verified; fail-closed
                continue


            # Project allowed fields
            projected_fields: dict[str, Any] = {}
            for fname, env_obj in record.envelopes.items():
                if fname in decision.allowed_fields:
                    f_ctx = CryptoContext(
                        tenant_id=subject.tenant_id,
                        record_id=record.record_id,
                        field_id=fname,
                        dek_id=capsule.capsule_id,
                    )
                    f_pt = self.engine.decrypt_field(env_obj, f_ctx, unwrapped_dek)
                    projected_fields[fname] = f_pt.decode("utf-8")
                else:
                    projected_fields[fname] = "[REDACTED_BY_POLICY]"

            verified_results.append({
                "record_id": record.record_id,
                "tenant_id": subject.tenant_id,
                "fields": projected_fields,
                "allowed_fields": list(decision.allowed_fields),
                "is_break_glass": decision.is_break_glass,
            })

        # 6. Audit Trail (F9 metadata only; no plaintext value or token logged)
        self._log_audit_event(
            "SEARCH",
            subject,
            f"field:{field_name}",
            "PERMITTED",
            f"Found {len(verified_results)} verified records out of {len(candidates)} candidates",
            is_break_glass=decision.is_break_glass,
        )

        return verified_results

    def ingest_attachment(
        self,
        subject: SubjectAttributes,
        record_id: str,
        file_stream: BinaryIO,
        filename: str,
        modality: str,
        content_type: str = "application/octet-stream",
        sensitivity: str = "CONFIDENTIAL",
        department: Optional[str] = None,
        env: Optional[EnvironmentContext] = None,
    ) -> dict[str, Any]:
        """
        Ingests a non-text medical file attachment (DICOM, CT/MRI, X-ray, Ultrasound, PDF).
        Enforces pre-storage validation, Gateway PEP ABAC evaluation, envelope encryption,
        MinIO S3 ciphertext storage, and MongoDB metadata persistence.
        """
        if self.minio_storage is None:
            raise RuntimeError("MinIO storage client is not configured on this Gateway instance")
        if env is None:
            env = EnvironmentContext()

        tenant_id = subject.tenant_id
        att_dept = department or subject.department

        # 1. Pre-storage validation: Verify patient record exists in MongoDB under this tenant
        patient_record = self.storage.get_patient(record_id, tenant_id)
        if not patient_record:
            self._log_audit_event("INGEST_ATTACHMENT", subject, record_id, "DENIED", "Patient record not found in tenant")
            raise AccessDeniedError(f"Patient record '{record_id}' not found in tenant '{tenant_id}'")

        # 2. Gateway PEP: Evaluate WRITE_ATTACHMENT permission
        obj_attrs = ObjectAttributes(
            record_id=record_id,
            tenant_id=tenant_id,
            department=att_dept,
            sensitivity=sensitivity,
            data_class="imaging",
            attachment_type=modality,
        )
        decision = self.pdp.evaluate(subject, obj_attrs, Action.WRITE_ATTACHMENT, env)
        if not decision.is_permitted:
            self._log_audit_event("INGEST_ATTACHMENT", subject, record_id, "DENIED", decision.reason)
            raise AccessDeniedError(f"Gateway PEP: Access denied for WRITE_ATTACHMENT: {decision.reason}")

        # 3. Generate unique attachment ID
        attachment_id = f"att_{uuid.uuid4().hex[:16]}"

        # 4. Request DEK and KeyCapsule from KeyBroker (Zone Z1)
        extra_ctx = {
            "attachment_id": attachment_id,
            "modality": modality,
            "department": att_dept,
            "object_kind": "medical_attachment",
            "sensitivity": sensitivity,
        }
        dek, capsule = self.broker.issue_dek_and_capsule(
            tenant_id=tenant_id,
            record_id=record_id,
            data_class="imaging",
            extra_context=extra_ctx,
        )

        # 5. Encrypt stream chunk-by-chunk using MedicalFileCipher
        ciphertext_buf = io.BytesIO()
        crypto_summary = self.file_cipher.encrypt_stream(
            in_stream=file_stream,
            out_stream=ciphertext_buf,
            dek=dek,
            tenant_id=tenant_id,
            record_id=record_id,
            attachment_id=attachment_id,
            filename=filename,
            content_type=content_type,
            capsule_id=capsule.capsule_id,
        )

        # 6. Upload ciphertext to MinIO S3 Object Storage (Zone Z2)
        ciphertext_bytes = ciphertext_buf.getvalue()
        s3_key = f"records/{record_id}/{attachment_id}.enc"
        bucket_name, object_name = self.minio_storage.put_ciphertext(
            tenant_id=tenant_id,
            object_name=s3_key,
            data_stream=io.BytesIO(ciphertext_bytes),
            length=len(ciphertext_bytes),
            content_type="application/octet-stream",
            metadata={
                "medshare-attachment-id": attachment_id,
                "medshare-capsule-id": capsule.capsule_id,
                "medshare-modality": modality,
            },
        )

        # 7. Persist metadata and capsule in MongoDB (Zone Z2)
        attachment_meta = EncryptedAttachmentMeta(
            attachment_id=attachment_id,
            tenant_id=tenant_id,
            record_id=record_id,
            modality=modality,
            filename=filename,
            content_type=content_type,
            file_size_bytes=crypto_summary["ciphertext_bytes"],
            s3_bucket=bucket_name,
            s3_key=object_name,
            capsule_id=capsule.capsule_id,
            plaintext_sha256=crypto_summary["plaintext_sha256"],
            ciphertext_sha256=crypto_summary["ciphertext_sha256"],
            department=att_dept,
            sensitivity=sensitivity,
        )
        self.storage.save_attachment(attachment_meta, capsule)

        # 8. Immutable Audit Trail (Zone Z3)
        self._log_audit_event(
            "INGEST_ATTACHMENT",
            subject,
            record_id,
            "PERMITTED",
            f"Uploaded and encrypted {modality} attachment {attachment_id} ({len(ciphertext_bytes)} bytes)",
            is_break_glass=decision.is_break_glass,
        )

        return attachment_meta.to_dict()

    def retrieve_attachment(
        self,
        subject: SubjectAttributes,
        record_id: str,
        attachment_id: str,
        env: Optional[EnvironmentContext] = None,
    ) -> tuple[dict[str, Any], bytes]:
        """
        Retrieves, authorizes, and decrypts a medical attachment.
        Enforces Gateway PEP ABAC evaluation, Key Broker DEK unwrapping,
        MinIO ciphertext retrieval, and streaming integrity verification.
        """
        if self.minio_storage is None:
            raise RuntimeError("MinIO storage client is not configured on this Gateway instance")
        if env is None:
            env = EnvironmentContext()

        tenant_id = subject.tenant_id

        # 1. Fetch attachment metadata and key capsule from MongoDB
        lookup = self.storage.get_attachment(tenant_id, attachment_id)
        if not lookup:
            self._log_audit_event("RETRIEVE_ATTACHMENT", subject, record_id, "DENIED", "Attachment not found")
            raise AccessDeniedError(f"Attachment '{attachment_id}' not found in tenant '{tenant_id}'")

        att_meta, capsule = lookup
        if att_meta.record_id != record_id:
            self._log_audit_event("RETRIEVE_ATTACHMENT", subject, record_id, "DENIED", "Cross-record attachment mismatch")
            raise AccessDeniedError(f"Attachment '{attachment_id}' does not belong to record '{record_id}'")

        # 2. Gateway PEP: Evaluate READ_ATTACHMENT permission
        obj_attrs = ObjectAttributes(
            record_id=record_id,
            tenant_id=tenant_id,
            department=att_meta.department,
            sensitivity=att_meta.sensitivity,
            data_class="imaging",
            attachment_id=attachment_id,
            attachment_type=att_meta.modality,
        )
        decision = self.pdp.evaluate(subject, obj_attrs, Action.READ_ATTACHMENT, env)
        if not decision.is_permitted:
            self._log_audit_event("RETRIEVE_ATTACHMENT", subject, record_id, "DENIED", decision.reason)
            raise AccessDeniedError(f"Gateway PEP: Access denied for READ_ATTACHMENT: {decision.reason}")

        # 3. Request KeyBroker to unwrap DEK
        requesting_context = dict(capsule.bound_object_context)
        requesting_context["subject"] = subject
        requesting_context["env"] = env
        dek = self.broker.unwrap_dek(capsule, requesting_context)

        # 4. Fetch ciphertext from MinIO S3 Object Storage
        ciphertext_bytes = self.minio_storage.get_ciphertext_bytes(att_meta.tenant_id, att_meta.s3_key)

        # 5. Decrypt and verify integrity via MedicalFileCipher
        plaintext_buf = io.BytesIO()
        decrypt_summary = self.file_cipher.decrypt_stream(
            in_stream=io.BytesIO(ciphertext_bytes),
            out_stream=plaintext_buf,
            dek=dek,
            expected_tenant_id=tenant_id,
            expected_record_id=record_id,
            expected_attachment_id=attachment_id,
            expected_plaintext_sha256=att_meta.plaintext_sha256,
        )

        # 6. Immutable Audit Trail
        self._log_audit_event(
            "RETRIEVE_ATTACHMENT",
            subject,
            record_id,
            "PERMITTED",
            f"Decrypted {att_meta.modality} attachment {attachment_id} ({decrypt_summary['total_plaintext_bytes']} bytes)",
            is_break_glass=decision.is_break_glass,
        )

        return att_meta.to_dict(), plaintext_buf.getvalue()

    def list_patient_attachments(
        self,
        subject: SubjectAttributes,
        record_id: str,
        env: Optional[EnvironmentContext] = None,
    ) -> list[dict[str, Any]]:
        """
        Lists available medical attachments for a patient with ABAC sensitivity filtering.
        """
        if env is None:
            env = EnvironmentContext()

        tenant_id = subject.tenant_id
        attachments = self.storage.list_attachments(tenant_id, record_id)

        visible = []
        for att in attachments:
            obj_attrs = ObjectAttributes(
                record_id=record_id,
                tenant_id=tenant_id,
                department=att.department,
                sensitivity=att.sensitivity,
                data_class="imaging",
                attachment_id=att.attachment_id,
                attachment_type=att.modality,
            )
            decision = self.pdp.evaluate(subject, obj_attrs, Action.READ_ATTACHMENT, env)
            if decision.is_permitted:
                visible.append(att.to_dict())

        return visible


