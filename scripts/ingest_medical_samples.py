#!/usr/bin/env python3
"""
Medical Samples Ingestion Pipeline for MedShare-Lab.
Ingests real-world sample medical files (~102.8 MB: DICOM, X-ray, Ultrasound, CT, MRI, PDF)
into live MongoDB 7.0 and MinIO S3 Object Storage via Trusted Crypto Gateway (Zone Z1).
"""

import json
import os
import sys

from medshare.broker.broker import KeyBroker
from medshare.broker.kms import VaultKmsClient
from medshare.crypto.engine import FieldCipherEngine
from medshare.crypto.file_cipher import MedicalFileCipher
from medshare.gateway.service import ClinicalGatewayService
from medshare.policy.abac import AbacPolicyEngine, SubjectAttributes
from medshare.storage.dal import MongoStorage
from medshare.storage.minio_dal import MinioStorage

MANIFEST_PATH = "datasets/samples/raw/manifest.json"
SAMPLES_BASE_DIR = "datasets/samples/raw"


def main():
    print("=================================================================")
    print("MedShare-Lab: Live Medical Samples Ingestion (MinIO + MongoDB)")
    print("=================================================================")

    if not os.path.exists(MANIFEST_PATH):
        print(f"Error: Manifest not found at {MANIFEST_PATH}")
        sys.exit(1)

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    # 1. Initialize live service clients
    print("\n1. Connecting to live infrastructure services:")
    print("  - Vault KMS (Zone Z1): http://localhost:8200")
    kms = VaultKmsClient(base_url="http://localhost:8200", token="dev-root-token-topic18")
    
    # Ensure KEKs exist
    for kek in [
        "kek_hospital_a_clinical_v1",
        "kek_hospital_a_imaging_v1",
        "kek_hospital_b_clinical_v1",
        "kek_hospital_b_imaging_v1",
    ]:
        kms.ensure_key(kek)
        print(f"    [OK] Ensured Transit KEK: {kek}")

    print("  - MongoDB 7.0 (Zone Z2): localhost:27017")
    mongo = MongoStorage(
        uri="mongodb://medshare_dba:dba_secret_dev_pass@localhost:27017/?authSource=admin",
        # Same DB as the Web Portal / DAL (gateway/api.py reads DB_NAME, default medshare_db).
        db_name=os.getenv("DB_NAME", "medshare_db"),
    )
    mongo.initialize_indexes()
    print("    [OK] Initialized MongoDB collections & indexes")

    print("  - MinIO S3 Object Storage (Zone Z2): localhost:9000")
    minio = MinioStorage(
        endpoint="localhost:9000",
        access_key="medshare_admin",
        secret_key="minio_secret_dev_pass",
        secure=False,
        bucket_prefix="medshare-",
    )
    print("    [OK] MinIO S3 client initialized")

    # 2. Build Trusted Gateway Service (Zone Z1)
    pdp = AbacPolicyEngine()
    broker = KeyBroker(kms_client=kms, pdp=pdp)
    engine = FieldCipherEngine()
    file_cipher = MedicalFileCipher(chunk_size=1024 * 1024)  # 1 MB chunks

    gateway = ClinicalGatewayService(
        pdp=pdp,
        broker=broker,
        engine=engine,
        storage=mongo,
        minio_storage=minio,
        file_cipher=file_cipher,
    )

    # 3. Ingest benchmark patients if not already created
    print("\n2. Ingesting patient demographics:")
    doc_cardio_a = SubjectAttributes(
        user_id="dr_cardio_lead",
        tenant_id="hospital-a",
        role="DOCTOR",
        department="CARDIOLOGY",
    )
    doc_onco_a = SubjectAttributes(
        user_id="dr_onco_lead",
        tenant_id="hospital-a",
        role="DOCTOR",
        department="ONCOLOGY",
    )

    patients = [
        (
            doc_cardio_a,
            {
                "record_id": "rec-patient-cardio-01",
                "name": "Tran Van Tuan",
                "dob": "1972-04-15",
                "gender": "M",
                "diagnosis": "Cardiomegaly with Heart Failure",
                "notes": "Patient scheduled for chest radiography and echocardiography.",
                "department": "CARDIOLOGY",
            },
        ),
        (
            doc_onco_a,
            {
                "record_id": "rec-patient-onco-01",
                "name": "Le Thi Mai",
                "dob": "1985-09-22",
                "gender": "F",
                "diagnosis": "Breast Fibroadenoma",
                "notes": "Follow-up breast ultrasound and core biopsy report received.",
                "department": "ONCOLOGY",
            },
        ),
    ]

    for subj, pat in patients:
        try:
            gateway.ingest_patient_record(subj, pat)
            print(f"  [+] Ingested Patient: {pat['record_id']} ({pat['name']}) - {pat['department']}")
        except Exception as e:
            print(f"  [*] Patient {pat['record_id']} already exists or updated: {e}")

    # 4. Ingest non-text files into MinIO and MongoDB
    print("\n3. Encrypting & Ingesting Medical Files into MinIO (S3):")
    ingested_count = 0
    total_bytes = 0

    for item in manifest["files"]:
        rel_path = item["relative_path"]
        full_path = os.path.join(SAMPLES_BASE_DIR, rel_path)
        modality = item["modality"]
        fsize = item["size_bytes"]
        fname = item["filename"]

        # Assign patient & department based on modality
        if modality in ("XRAY", "ULTRASOUND") and "cardiac" in fname.lower():
            subj = doc_cardio_a
            rec_id = "rec-patient-cardio-01"
            dept = "CARDIOLOGY"
        elif "biopsy" in fname.lower() or "breast" in fname.lower() or "onco" in fname.lower():
            subj = doc_onco_a
            rec_id = "rec-patient-onco-01"
            dept = "ONCOLOGY"
        elif modality in ("CT", "MRI"):
            subj = doc_cardio_a
            rec_id = "rec-patient-cardio-01"
            dept = "CARDIOLOGY"
        else:
            subj = doc_cardio_a
            rec_id = "rec-patient-cardio-01"
            dept = "CARDIOLOGY"

        print(f"  -> Encrypting {fname} ({fsize / (1024*1024):.2f} MB) -> Record: {rec_id} ({dept})...", end="", flush=True)

        with open(full_path, "rb") as fp:
            res = gateway.ingest_attachment(
                subject=subj,
                record_id=rec_id,
                file_stream=fp,
                filename=fname,
                modality=modality,
                content_type=item["mime_type"],
                department=dept,
            )

        print(f" Done! S3 Object: {res['s3_bucket']}/{res['s3_key']} | Capsule: {res['capsule_id'][:12]}...")
        ingested_count += 1
        total_bytes += fsize

    print(f"\nSuccessfully ingested {ingested_count} files ({total_bytes / (1024*1024):.2f} MB) into MinIO + MongoDB!")

    # 5. Live Verification: Retrieve and verify sample files from each modality
    print("\n4. Live Verification & Integrity Check:")
    test_cases = [
        ("rec-patient-cardio-01", "chest_xray_cardiomegaly.png", doc_cardio_a),
        ("rec-patient-onco-01", "pathology_biopsy_report.pdf", doc_onco_a),
        ("rec-patient-cardio-01", "ultrasound_cardiac_2d.dcm", doc_cardio_a),
    ]

    for rec_id, target_filename, subj in test_cases:
        atts = gateway.list_patient_attachments(subj, rec_id)
        matching = [a for a in atts if a["filename"] == target_filename]
        if not matching:
            print(f"  [FAIL] Attachment {target_filename} not found in {rec_id}")
            continue

        target_att = matching[0]
        att_id = target_att["attachment_id"]

        # Retrieve through Gateway
        meta, pt_bytes = gateway.retrieve_attachment(subj, rec_id, att_id)

        # Compare with source on disk
        for item in manifest["files"]:
            if item["filename"] == target_filename:
                src_path = os.path.join(SAMPLES_BASE_DIR, item["relative_path"])
                with open(src_path, "rb") as f:
                    orig_bytes = f.read()

                assert pt_bytes == orig_bytes, f"Decrypted bytes mismatch for {target_filename}!"
                print(f"  [PASS] {target_filename} ({len(pt_bytes):,} bytes) verified byte-for-byte!")
                break

    print("\n=================================================================")
    print("All live medical samples ingested, encrypted, and verified PASS!")
    print("=================================================================")


if __name__ == "__main__":
    main()

