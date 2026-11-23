#!/usr/bin/env python3
"""
Prepares balanced real-world medical sample files (~80 - 100 MB total)
across modalities: X-ray, Ultrasound, CT, MRI, and PDF reports.
Generates manifest.json mapping files to modalities and metadata.
"""

import hashlib
import io
import json
import os
import shutil
import zipfile

SAMPLES_DIR = os.path.abspath("datasets/samples/raw")
ZIP_PATH = os.path.abspath("datasets/samples/data.zip")


def create_minimal_pdf(title: str, lines: list[str]) -> bytes:
    """Creates a valid PDF/1.4 document containing medical text lines."""
    content_stream = ["BT", "/F1 16 Tf", "50 750 Td", f"({title}) Tj", "ET"]
    content_stream.append("BT /F2 10 Tf 50 720 Td 14 TL")
    for line in lines:
        sanitized = line.replace("(", "\\(").replace(")", "\\)")
        content_stream.append(f"({sanitized}) '")
    content_stream.append("ET")
    stream_data = "\n".join(content_stream).encode("latin1")

    objects = []
    # 1: Catalog
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    # 2: Pages
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    # 3: Page
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << "
        b"/F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> "
        b"/F2 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>"
    )
    # 4: Stream
    objects.append(
        b"<< /Length " + str(len(stream_data)).encode("ascii") + b" >>\nstream\n" + stream_data + b"\nendstream"
    )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{i} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(b"xref\n0 5\n0000000000 65535 f \n")
    for off in offsets:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    pdf.extend(b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n")
    pdf.extend(f"{xref_offset}\n%%EOF\n".encode("ascii"))
    return bytes(pdf)


def main():
    os.makedirs(os.path.join(SAMPLES_DIR, "xray"), exist_ok=True)
    os.makedirs(os.path.join(SAMPLES_DIR, "ct_mri"), exist_ok=True)
    os.makedirs(os.path.join(SAMPLES_DIR, "ultrasound"), exist_ok=True)
    os.makedirs(os.path.join(SAMPLES_DIR, "reports"), exist_ok=True)

    print("Extracting selected files from Zenodo data.zip...")
    if os.path.exists(ZIP_PATH):
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            # Map of zip entry -> target path
            extract_map = {
                "data/ml/cardiomegaly_cc0.png": "xray/chest_xray_cardiomegaly.png",
                "data/ml/other_op.png": "xray/chest_xray_normal.png",
                "data/ml/rotatechest.png": "xray/chest_xray_pa.png",
                "data/sitk/digital_xray.dcm": "xray/chest_digital_xray.dcm",
                "data/anonym/our_sample_dicom.dcm": "xray/radiograph_sample.dcm",
                "data/sitk/training_001_ct.mha": "ct_mri/abdominal_ct_scan.mha",
                "data/sitk/training_001_mr_T1.mha": "ct_mri/brain_mri_t1.mha",
                "data/mri/OBJECT_phantom_T2W_TSE_Cor_14_1.nii": "ct_mri/mri_phantom_t2w.nii",
                "data/sitk/A1_grayT1.nrrd": "ct_mri/neuro_mri_gray_t1.nrrd",
            }
            for zip_src, rel_dst in extract_map.items():
                target_file = os.path.join(SAMPLES_DIR, rel_dst)
                with zf.open(zip_src) as src_fp, open(target_file, "wb") as dst_fp:
                    shutil.copyfileobj(src_fp, dst_fp)
                print(f"  Extracted: {rel_dst} ({os.path.getsize(target_file):,} bytes)")

    # Generate sample clinical lab report PDFs
    print("Generating clinical lab reports (PDF)...")
    reports = {
        "reports/lab_report_complete_blood_count.pdf": (
            "HOSPITAL CENTRAL LAB - COMPLETE BLOOD COUNT (CBC)",
            [
                "Patient ID: PT-100294 | Order Date: 2026-10-25 | Specimen: Whole Blood EDTA",
                "Physician: Dr. Nguyen Van A (Cardiology Dept)",
                "----------------------------------------------------------------------",
                "TEST NAME                RESULT    UNITS      REFERENCE INTERVAL  STATUS",
                "White Blood Cells (WBC)  7.2       x10^3/uL   4.5 - 11.0          NORMAL",
                "Red Blood Cells (RBC)    4.85      x10^6/uL   4.30 - 5.90         NORMAL",
                "Hemoglobin (Hgb)         14.6      g/dL       13.5 - 17.5         NORMAL",
                "Hematocrit (Hct)         43.2      %          41.0 - 50.0         NORMAL",
                "Platelet Count           245       x10^3/uL   150 - 450           NORMAL",
                "Mean Corpuscular Vol     89.1      fL         80.0 - 100.0        NORMAL",
                "----------------------------------------------------------------------",
                "Clinical Notes: Patient stable, no signs of acute infection or anemia.",
                "Verified by: Dr. Le Thi B, Chief Hematopathologist",
            ]
        ),
        "reports/radiology_findings_cxr.pdf": (
            "DEPARTMENT OF DIAGNOSTIC RADIOLOGY - CONSULTATION REPORT",
            [
                "Patient ID: PT-100294 | Modality: Chest PA & Lateral | Date: 2026-10-26",
                "Referring Physician: Dr. Nguyen Van A | Radiologist: Dr. Tran C",
                "----------------------------------------------------------------------",
                "CLINICAL INDICATION: Cough and shortness of breath upon exertion.",
                "FINDINGS:",
                "  Lungs: Lungs are clear without focal consolidation, pneumothorax,",
                "         or pleural effusion. Normal vascular markings.",
                "  Heart: Cardiothoracic ratio is within normal limits (< 0.50).",
                "  Mediastinum: Mediastinal contours and hilar structures unremarkable.",
                "  Bones & Soft Tissue: Intact osseous framework, no acute fractures.",
                "IMPRESSION: No acute cardiopulmonary abnormality identified.",
                "RECOMMENDATION: Routine follow-up as clinically indicated.",
            ]
        ),
        "reports/pathology_biopsy_report.pdf": (
            "SURGICAL PATHOLOGY & HISTOPATHOLOGY REPORT",
            [
                "Patient ID: PT-200812 | Specimen: Ultrasound-Guided Core Needle Biopsy",
                "Department: Oncology / Pathology | Date Received: 2026-10-28",
                "----------------------------------------------------------------------",
                "GROSS EXAMINATION: 4 core biopsy tissue fragments, tan-white, measuring",
                "                   1.2 cm in aggregate length. Entirely submitted.",
                "MICROSCOPIC DESCRIPTION:",
                "  Sections show breast parenchyma with dense fibromyxoid stroma.",
                "  Proliferation of compressed ducts lined by bland epithelial and",
                "  myoepithelial cells. No cytologic atypia or necrosis seen.",
                "DIAGNOSIS: Consistent with Benign Fibroadenoma.",
                "FINAL STATUS: NEGATIVE FOR MALIGNANCY (BI-RADS Category 2 equivalent).",
            ]
        ),
    }

    for rel_path, (title, lines) in reports.items():
        full_path = os.path.join(SAMPLES_DIR, rel_path)
        pdf_bytes = create_minimal_pdf(title, lines)
        with open(full_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"  Generated: {rel_path} ({len(pdf_bytes):,} bytes)")

    # Scan all files and build manifest
    total_size = 0
    manifest = []
    for root, _, files in os.walk(SAMPLES_DIR):
        for fname in sorted(files):
            if fname == "manifest.json":
                continue
            fpath = os.path.join(root, fname)
            fsize = os.path.getsize(fpath)
            total_size += fsize
            rel_path = os.path.relpath(fpath, SAMPLES_DIR)

            with open(fpath, "rb") as f:
                content = f.read()
                sha256 = hashlib.sha256(content).hexdigest()

            # Determine modality and mime type
            ext = os.path.splitext(fname)[1].lower()
            if rel_path.startswith("xray"):
                modality = "XRAY"
            elif rel_path.startswith("ultrasound"):
                modality = "ULTRASOUND"
            elif rel_path.startswith("ct_mri"):
                modality = "CT" if "ct" in fname.lower() else "MRI"
            elif rel_path.startswith("reports"):
                modality = "LAB_REPORT"
            else:
                modality = "OTHER"

            mime_types = {
                ".dcm": "application/dicom",
                ".png": "image/png",
                ".pdf": "application/pdf",
                ".mha": "application/octet-stream; modality=metaimage",
                ".nii": "application/octet-stream; modality=nifti",
                ".nrrd": "application/octet-stream; modality=nrrd",
            }

            manifest.append({
                "filename": fname,
                "relative_path": rel_path,
                "modality": modality,
                "mime_type": mime_types.get(ext, "application/octet-stream"),
                "size_bytes": fsize,
                "sha256": sha256,
            })

    manifest_path = os.path.join(SAMPLES_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump({"total_files": len(manifest), "total_size_bytes": total_size, "files": manifest}, f, indent=2)

    print(f"\nSuccessfully prepared {len(manifest)} sample files!")
    print(f"Total Size: {total_size / (1024 * 1024):.2f} MB ({total_size:,} bytes)")
    print(f"Manifest written to: {manifest_path}")


if __name__ == "__main__":
    main()
