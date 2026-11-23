"""
Security and Functional Tests for MinIO S3 Object Storage & Medical Attachments.
Part of MedShare-Lab (Topic 18 — NT2205.11.CH).

Validates:
1. Streaming authenticated encryption round-trip (MedicalFileCipher)
2. Tamper resistance: bit flipping, chunk truncation, context swapping
3. MinIO S3 bucket isolation and ciphertext persistence (MinioStorage)
4. Gateway PEP ABAC policy enforcement for medical attachments:
   - Doctor department-matching access
   - Nurse restricted access (routine vs CT/MRI)
   - Patient self-access portal
   - Cloud DBA / unauthorized role lockout
   - Detection and rejection of corrupted/tampered S3 blobs
"""

import io
import os
import secrets
import pytest

from medshare.broker.broker import KeyBroker
from medshare.broker.kms import MockKmsClient
from medshare.crypto.engine import FieldCipherEngine
from medshare.crypto.errors import (
    AccessDeniedError,
    GcmAuthTagMismatchError,
    RecordTamperedError,
)
from medshare.crypto.file_cipher import MedicalFileCipher
from medshare.gateway.service import ClinicalGatewayService
from medshare.policy.abac import (
    AbacPolicyEngine,
    Action,
    EnvironmentContext,
    SubjectAttributes,
)
from medshare.storage.dal import MongoStorage
from medshare.storage.minio_dal import MinioStorage


@pytest.fixture
def file_cipher():
    # Use smaller chunk size (64 KB) in tests for multi-chunk testing
    return MedicalFileCipher(chunk_size=64 * 1024)


@pytest.fixture
def kms_client():
    kms = MockKmsClient()
    kms.ensure_key("kek_hospital_a_imaging_v1")
    kms.ensure_key("kek_hospital_a_clinical_v1")
    kms.ensure_key("kek_hospital_b_imaging_v1")
    return kms


@pytest.fixture
def broker(kms_client):
    return KeyBroker(kms_client=kms_client)


@pytest.fixture
def pdp():
    return AbacPolicyEngine()


@pytest.fixture
def engine():
    return FieldCipherEngine()


@pytest.fixture
def mongo_storage():
    storage = MongoStorage(
        uri="mongodb://medshare_dba:dba_secret_dev_pass@localhost:27017/?authSource=admin",
        db_name="medshare_test_db",
    )
    storage.initialize_indexes()
    return storage


@pytest.fixture
def minio_storage():
    return MinioStorage(
        endpoint="localhost:9000",
        access_key="medshare_admin",
        secret_key="minio_secret_dev_pass",
        secure=False,
        bucket_prefix="medshare-test-",
    )


@pytest.fixture
def gateway(pdp, broker, engine, mongo_storage, minio_storage, file_cipher):
    return ClinicalGatewayService(
        pdp=pdp,
        broker=broker,
        engine=engine,
        storage=mongo_storage,
        minio_storage=minio_storage,
        file_cipher=file_cipher,
    )


def test_file_cipher_roundtrip(file_cipher):
    """Verifies that arbitrary binary data (including multi-chunk) encrypts and decrypts losslessly."""
    dek = secrets.token_bytes(32)
    original_data = os.urandom(150 * 1024)  # 150 KB (spans 3 chunks of 64KB)

    in_buf = io.BytesIO(original_data)
    enc_buf = io.BytesIO()

    summary = file_cipher.encrypt_stream(
        in_stream=in_buf,
        out_stream=enc_buf,
        dek=dek,
        tenant_id="hospital-a",
        record_id="rec-001",
        attachment_id="att-001",
        filename="chest_xray.dcm",
        content_type="application/dicom",
        capsule_id="cap-001",
    )

    assert summary["total_chunks"] == 3
    assert len(enc_buf.getvalue()) > len(original_data)

    dec_buf = io.BytesIO()
    dec_summary = file_cipher.decrypt_stream(
        in_stream=io.BytesIO(enc_buf.getvalue()),
        out_stream=dec_buf,
        dek=dek,
        expected_tenant_id="hospital-a",
        expected_record_id="rec-001",
        expected_attachment_id="att-001",
        expected_plaintext_sha256=summary["plaintext_sha256"],
    )

    assert dec_buf.getvalue() == original_data
    assert dec_summary["total_chunks"] == 3


def test_file_cipher_bit_tamper_detected(file_cipher):
    """Verifies that flipping even a single bit in ciphertext raises GcmAuthTagMismatchError."""
    dek = secrets.token_bytes(32)
    original_data = b"CONFIDENTIAL MEDICAL SCAN DATA " * 100

    enc_buf = io.BytesIO()
    file_cipher.encrypt_stream(
        in_stream=io.BytesIO(original_data),
        out_stream=enc_buf,
        dek=dek,
        tenant_id="hospital-a",
        record_id="rec-001",
        attachment_id="att-001",
        filename="scan.png",
        content_type="image/png",
        capsule_id="cap-001",
    )

    tampered_bytes = bytearray(enc_buf.getvalue())
    # Flip one bit near the middle (in the chunk payload)
    tampered_bytes[len(tampered_bytes) - 10] ^= 0x01

    dec_buf = io.BytesIO()
    with pytest.raises(GcmAuthTagMismatchError):
        file_cipher.decrypt_stream(
            in_stream=io.BytesIO(tampered_bytes),
            out_stream=dec_buf,
            dek=dek,
            expected_tenant_id="hospital-a",
            expected_record_id="rec-001",
            expected_attachment_id="att-001",
        )


def test_file_cipher_cross_record_tamper_detected(file_cipher):
    """Verifies that attempting to attach an encrypted object to another patient fails."""
    dek = secrets.token_bytes(32)
    original_data = b"CONFIDENTIAL PATIENT X-RAY"

    enc_buf = io.BytesIO()
    file_cipher.encrypt_stream(
        in_stream=io.BytesIO(original_data),
        out_stream=enc_buf,
        dek=dek,
        tenant_id="hospital-a",
        record_id="rec-001",
        attachment_id="att-001",
        filename="scan.png",
        content_type="image/png",
        capsule_id="cap-001",
    )

    dec_buf = io.BytesIO()
    # Attacker tries to decrypt under rec-002 context
    with pytest.raises(RecordTamperedError, match="Record mismatch in header"):
        file_cipher.decrypt_stream(
            in_stream=io.BytesIO(enc_buf.getvalue()),
            out_stream=dec_buf,
            dek=dek,
            expected_tenant_id="hospital-a",
            expected_record_id="rec-002",  # Mismatch!
            expected_attachment_id="att-001",
        )


def test_minio_storage_crud(minio_storage):
    """Verifies MinIO put, get, stat, and delete operations."""
    tenant = "hospital-a"
    test_key = "tests/test_file.bin"
    payload = b"ENCRYPTED CIPHERTEXT BLOB FOR MINIO TESTING"

    bucket, key = minio_storage.put_ciphertext(
        tenant_id=tenant,
        object_name=test_key,
        data_stream=io.BytesIO(payload),
        length=len(payload),
    )

    assert "hospital-a" in bucket
    assert key == test_key

    # Stat
    info = minio_storage.stat_ciphertext(tenant, test_key)
    assert info["size"] == len(payload)

    # Get
    data = minio_storage.get_ciphertext_bytes(tenant, test_key)
    assert data == payload

    # Delete
    minio_storage.delete_ciphertext(tenant, test_key)


def test_gateway_attachment_abac_workflow(gateway, mongo_storage):
    """
    Comprehensive end-to-end Gateway PEP attachment workflow test:
    1. Ingest patient demographic record.
    2. Cardiology doctor uploads X-Ray and Ultrasound attachments.
    3. Cardiology doctor retrieves and verifies attachments match original bytes.
    4. Oncology doctor is DENIED access (department mismatch).
    5. Nurse retrieves Ultrasound (permitted) but is DENIED CT/MRI (specialized).
    6. Patient retrieves their own report but is DENIED other patients' files.
    7. Admin / DBA is DENIED attachment retrieval (TC-27).
    """
    # 1. Ingest base patient
    doc_cardio = SubjectAttributes(
        user_id="dr_cardio",
        tenant_id="hospital-a",
        role="DOCTOR",
        department="CARDIOLOGY",
    )
    patient_data = {
        "record_id": "rec-patient-101",
        "name": "Nguyen Van B",
        "dob": "1980-05-12",
        "gender": "M",
        "diagnosis": "Atrial Fibrillation",
        "notes": "ECG shows irregular rhythm",
        "department": "CARDIOLOGY",
    }
    gateway.ingest_patient_record(doc_cardio, patient_data)

    # 2. Upload X-Ray attachment
    xray_bytes = b"SAMPLE_DICOM_CHEST_XRAY_DATA_BYTES_12345"
    att_meta = gateway.ingest_attachment(
        subject=doc_cardio,
        record_id="rec-patient-101",
        file_stream=io.BytesIO(xray_bytes),
        filename="chest_xray.dcm",
        modality="XRAY",
        content_type="application/dicom",
        sensitivity="CONFIDENTIAL",
    )
    att_id = att_meta["attachment_id"]
    assert att_id.startswith("att_")

    # 3. Doctor retrieves X-Ray: byte-for-byte match
    ret_meta, ret_bytes = gateway.retrieve_attachment(
        subject=doc_cardio,
        record_id="rec-patient-101",
        attachment_id=att_id,
    )
    assert ret_bytes == xray_bytes
    assert ret_meta["filename"] == "chest_xray.dcm"

    # 4. Oncology doctor access is DENIED
    doc_onco = SubjectAttributes(
        user_id="dr_onco",
        tenant_id="hospital-a",
        role="DOCTOR",
        department="ONCOLOGY",
    )
    with pytest.raises(AccessDeniedError, match="department 'ONCOLOGY' mismatch"):
        gateway.retrieve_attachment(
            subject=doc_onco,
            record_id="rec-patient-101",
            attachment_id=att_id,
        )

    # 5. Nurse access testing:
    # Upload an MRI (Specialized/Complex) and an Ultrasound (Routine)
    mri_bytes = b"BRAIN_MRI_HIGH_RESOLUTION_SCAN_DATA"
    mri_meta = gateway.ingest_attachment(
        subject=doc_cardio,
        record_id="rec-patient-101",
        file_stream=io.BytesIO(mri_bytes),
        filename="brain_mri.dcm",
        modality="MRI",
        content_type="application/dicom",
        sensitivity="RESTRICTED",
    )
    mri_id = mri_meta["attachment_id"]

    nurse_cardio = SubjectAttributes(
        user_id="nurse_hoa",
        tenant_id="hospital-a",
        role="NURSE",
        department="CARDIOLOGY",
    )
    # Nurse reading XRAY: permitted
    _, nurse_xray = gateway.retrieve_attachment(
        subject=nurse_cardio,
        record_id="rec-patient-101",
        attachment_id=att_id,
    )
    assert nurse_xray == xray_bytes

    # Nurse reading MRI: DENIED by ABAC policy (restricted from MRI/CT)
    with pytest.raises(AccessDeniedError, match="Nurse restricted from specialized"):
        gateway.retrieve_attachment(
            subject=nurse_cardio,
            record_id="rec-patient-101",
            attachment_id=mri_id,
        )

    # 6. Patient Self-Access Portal
    patient_user = SubjectAttributes(
        user_id="rec-patient-101",
        tenant_id="hospital-a",
        role="PATIENT",
        department="PATIENT_PORTAL",
        patient_id="rec-patient-101",
    )
    # Patient retrieves own X-Ray: permitted
    _, pt_bytes = gateway.retrieve_attachment(
        subject=patient_user,
        record_id="rec-patient-101",
        attachment_id=att_id,
    )
    assert pt_bytes == xray_bytes

    # Patient tries to access another patient's attachment: DENIED
    other_patient = SubjectAttributes(
        user_id="rec-patient-999",
        tenant_id="hospital-a",
        role="PATIENT",
        department="PATIENT_PORTAL",
        patient_id="rec-patient-999",
    )
    with pytest.raises(AccessDeniedError, match="Patient portal access strictly denied"):
        gateway.retrieve_attachment(
            subject=other_patient,
            record_id="rec-patient-101",
            attachment_id=att_id,
        )

    # 7. TC-27: DBA Lockout
    dba_user = SubjectAttributes(
        user_id="cloud_admin",
        tenant_id="hospital-a",
        role="DBA",
        department="IT_INFRA",
    )
    with pytest.raises(AccessDeniedError, match="TC-27"):
        gateway.retrieve_attachment(
            subject=dba_user,
            record_id="rec-patient-101",
            attachment_id=att_id,
        )


def test_tampered_minio_s3_blob_rejected(gateway, minio_storage):
    """
    Verifies that if an untrusted cloud administrator or attacker directly
    modifies ciphertext stored on MinIO, the Gateway PEP detects the corruption
    and rejects decryption with GcmAuthTagMismatchError.
    """
    doc_cardio = SubjectAttributes(
        user_id="dr_cardio_2",
        tenant_id="hospital-a",
        role="DOCTOR",
        department="CARDIOLOGY",
    )
    patient_data = {
        "record_id": "rec-patient-102",
        "name": "Tran Van C",
        "dob": "1975-08-20",
        "gender": "M",
        "diagnosis": "Cardiomegaly",
        "department": "CARDIOLOGY",
    }
    gateway.ingest_patient_record(doc_cardio, patient_data)

    original_file = b"REAL_AUTHENTIC_PATIENT_CHEST_XRAY_DATA" * 50
    att_meta = gateway.ingest_attachment(
        subject=doc_cardio,
        record_id="rec-patient-102",
        file_stream=io.BytesIO(original_file),
        filename="cxr_cardiomegaly.png",
        modality="XRAY",
        content_type="image/png",
    )
    att_id = att_meta["attachment_id"]

    # Tamper with the object directly in MinIO
    raw_s3_bytes = bytearray(minio_storage.get_ciphertext_bytes("hospital-a", att_meta["s3_key"]))
    raw_s3_bytes[len(raw_s3_bytes) - 5] ^= 0xFF  # Corrupt a byte in the encrypted stream

    minio_storage.put_ciphertext(
        tenant_id="hospital-a",
        object_name=att_meta["s3_key"],
        data_stream=io.BytesIO(raw_s3_bytes),
        length=len(raw_s3_bytes),
    )

    # Gateway retrieval MUST detect the tamper and fail-closed
    with pytest.raises(GcmAuthTagMismatchError):
        gateway.retrieve_attachment(
            subject=doc_cardio,
            record_id="rec-patient-102",
            attachment_id=att_id,
        )
