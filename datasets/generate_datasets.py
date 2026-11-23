#!/usr/bin/env python3
"""
MedShare-Lab: Synthetic EHR Dataset Generator (Topic 18 — NT2205.11.CH)
Tuần 3 — WP2: Sinh tập dữ liệu hồ sơ y tế điện tử tổng hợp chuẩn khoa học.

Đặc tính kỹ thuật:
- Hỗ trợ kích thước: 1.000 và 10.000 bản ghi.
- 5 seeds độc lập cho benchmark và thống kê: 1801, 1802, 1803, 1804, 1805.
- 2 phân bố dữ liệu:
  * 'uniform': Phân bố đều các mã chẩn đoán ICD-10 và chuyên khoa.
  * 'skewed': Phân bố lệch theo luật Zipf/Power-law (phản ánh tần suất bệnh thực tế,
              phục vụ thực nghiệm rò rỉ suy luận tần suất E5).
- Định dạng dữ liệu tách bạch:
  * datasets/generated/: File dataset tổng hợp (JSON / JSON Lines).
  * datasets/oracle/: Plaintext Ground Truth phục vụ kiểm chứng Differential Oracle (TC-15).
- Không dùng seed dataset để sinh khóa mật mã (Tuân thủ nguyên tắc AS-12 / Cryptographic Hygiene).
"""

import argparse
import json
import math
import os
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Cấu hình danh mục chuẩn theo đề tài MedShare-Lab
TENANTS = [
    ("tenant_hospital_a", 0.60),  # Bệnh viện A: 60% dữ liệu
    ("tenant_hospital_b", 0.40),  # Bệnh viện B: 40% dữ liệu
]

DEPARTMENTS = ["CARDIOLOGY", "ONCOLOGY", "PEDIATRICS", "NEUROLOGY", "GENERAL"]

CLASSIFICATIONS = [
    ("CONFIDENTIAL", 0.85),
    ("RESTRICTED", 0.15),
]

# 10 mã chẩn đoán ICD-10 phổ biến cho hồ sơ nội/ngoại trú
ICD10_CODES = [
    ("I25.1", "Benh tim thieu mau cuc bo man tinh (Atherosclerotic heart disease)"),
    ("E11.9", "Dai thao duong type 2 khong bien chung (Type 2 diabetes mellitus)"),
    ("J45.0", "Hen phe quan di ung chu yeu (Predominantly allergic asthma)"),
    ("C34.9", "U ac tinh phe quan va phoi (Malignant neoplasm of bronchus and lung)"),
    ("K21.9", "Trao nguoc da day thuc quan (Gastro-esophageal reflux disease)"),
    ("M54.5", "Dau that lung co nang (Low back pain)"),
    ("F41.1", "Roi loan lo au lan toa (Generalized anxiety disorder)"),
    ("N18.9", "Benh than man tinh giai doan khong xac dinh (Chronic kidney disease)"),
    ("G43.9", "Dau nua dau Migraine khong bien chung (Migraine, unspecified)"),
    ("H52.1", "Can thi hoc duong (Myopia)"),
]

HO_VIETNAM = [
    "Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Phan", "Vu", "Vo", "Dang",
    "Bui", "Do", "Ho", "Ngo", "Duong", "Ly", "Dinh", "Dao", "Doan", "Luong"
]

DEM_VIETNAM = ["Van", "Thi", "Duc", "Huu", "Ngoc", "Thanh", "Minh", "Quang", "Dinh", "Bao"]

TEN_VIETNAM = [
    "An", "Binh", "Cuong", "Dung", "Em", "Giang", "Hai", "Hung", "Khang", "Linh",
    "Minh", "Nam", "Phong", "Quan", "Son", "Tam", "Thao", "Tuan", "Vy", "Yen"
]

SAMPLE_NOTES = [
    "Benh nhan tinh tao, tiep xuc tot. Dau nguc trai thoang qua khi gang suc. Huyet ap 130/80 mmHg.",
    "Kham dinh ky: Duong huyet luc doi 6.8 mmol/L, HbA1c 6.5%. Tiep tuc duy tri phac do thuoc hien tai.",
    "Kho khe nhe ve dem, con hen xuat hien sau khi tiep xuc voi bui lanh. SpO2 97%.",
    "Ket qua chup CT phoi phat hien ton thuong dang not o thuy tren phoi phai, kich thuoc 12mm.",
    "O nong, thuong vi day tuc sau an. Noi soi da day: viem troot niem mac hang vi.",
    "Dau am i vung cot song that lung lan xuong mong phai, van dong han che nhe.",
    "Mat ngu keo dai, hoi hop trong nguc, lo au ve tinh trang suc khoe.",
    "Do thanh thai Creatinine 52 mL/min, eGFR giai doan 3a. Khuyen cao giam dam trong che do an.",
    "Dau nua dau ben trai giat theo nhip mach, kem buon non va so anh sang.",
    "Thi luc hai mat giam, mat trai -2.5D, mat phai -2.25D. Da ke don kinh dieu chinh.",
]


def weighted_choice(items_weights: List[Tuple[Any, float]], rng: random.Random) -> Any:
    """Chọn phần tử dựa theo trọng số xác suất."""
    items, weights = zip(*items_weights)
    return rng.choices(items, weights=weights, k=1)[0]


def get_diagnosis_weights(distribution: str, num_codes: int) -> List[float]:
    """
    Xác định phân bố trọng số cho các mã ICD-10.
    - 'uniform': Xác suất bằng nhau (1/N).
    - 'skewed': Phân bố Zipfian s=1.1 (tần suất mã 1 >> mã 2 >> mã N).
    """
    if distribution == "uniform":
        return [1.0 / num_codes] * num_codes
    elif distribution == "skewed":
        s = 1.15
        weights = [1.0 / math.pow(i + 1, s) for i in range(num_codes)]
        total = sum(weights)
        return [w / total for w in weights]
    else:
        raise ValueError(f"Unknown distribution: {distribution}")


def generate_synthetic_record(idx: int, seed: int, dist_type: str, rng: random.Random) -> Dict[str, Any]:
    """Sinh một bản ghi hồ sơ bệnh án tổng hợp theo schema chuẩn của Topic 18."""
    tenant_id = weighted_choice(TENANTS, rng)
    department = rng.choice(DEPARTMENTS)
    classification = weighted_choice(CLASSIFICATIONS, rng)

    # Patient identifiers
    patient_num = idx + 1
    external_patient_id = f"PAT-{seed}-{patient_num:06d}"
    
    # Deterministic UUIDv4 based on pseudo-random bytes
    record_uuid = str(uuid.UUID(bytes=rng.randbytes(16), version=4))

    # Name and email
    ho = rng.choice(HO_VIETNAM)
    dem = rng.choice(DEM_VIETNAM)
    ten = rng.choice(TEN_VIETNAM)
    full_name = f"{ho} {dem} {ten}"
    email = f"patient.{seed}.{patient_num:06d}@medshare-synth.vn"

    # Diagnosis code
    weights = get_diagnosis_weights(dist_type, len(ICD10_CODES))
    code_idx = rng.choices(range(len(ICD10_CODES)), weights=weights, k=1)[0]
    diag_code, diag_desc = ICD10_CODES[code_idx]

    # Clinical note
    base_note = SAMPLE_NOTES[code_idx % len(SAMPLE_NOTES)]
    note = f"[{diag_desc}] {base_note} (BS dieu tri: Dr.{rng.choice(TEN_VIETNAM)})"

    # Treatment cost in integer amount units (50..1000) for SEAL BFV integer exactness
    amount_units = rng.randint(50, 1000)

    # Timestamp
    created_at = datetime(2026, 9, 1, 8, 0, 0, tzinfo=timezone.utc).isoformat()

    return {
        "record_id": record_uuid,
        "tenant_id": tenant_id,
        "department": department,
        "classification": classification,
        "external_patient_id": external_patient_id,
        "name": full_name,
        "email": email,
        "diagnosis_code": diag_code,
        "note": note,
        "amount_units": amount_units,
        "created_at": created_at,
        "version": 1,
    }


def generate_dataset(size: int, seed: int, distribution: str) -> List[Dict[str, Any]]:
    """Tạo toàn bộ tập dữ liệu với kích thước và seed xác định."""
    rng = random.Random(seed)
    records = []
    for i in range(size):
        records.append(generate_synthetic_record(i, seed, distribution, rng))
    return records


def build_oracle(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Xây dựng Plaintext Ground Truth Oracle:
    Cho phép kiểm chứng tính toàn vẹn độc lập (Differential Oracle Verification).
    Bao gồm index tra cứu nhanh theo record_id, external_patient_id và diagnosis_code.
    """
    by_record_id = {}
    by_patient_id = {}
    by_diag_code = {}
    total_amount = 0

    for r in records:
        rec_id = r["record_id"]
        tenant = r["tenant_id"]
        pat_id = r["external_patient_id"]
        diag = r["diagnosis_code"]
        amount = r["amount_units"]

        by_record_id[rec_id] = r

        key_pat = f"{tenant}:{pat_id}"
        by_patient_id[key_pat] = rec_id

        key_diag = f"{tenant}:{diag}"
        if key_diag not in by_diag_code:
            by_diag_code[key_diag] = []
        by_diag_code[key_diag].append(rec_id)

        total_amount += amount

    return {
        "record_count": len(records),
        "total_amount_units": total_amount,
        "by_record_id": by_record_id,
        "by_tenant_patient_id": by_patient_id,
        "diagnosis_counts": {k: len(v) for k, v in by_diag_code.items()},
    }


def main():
    parser = argparse.ArgumentParser(description="MedShare-Lab Synthetic EHR Dataset Generator")
    parser.add_argument("--size", type=int, default=1000, help="Số bản ghi cần sinh (ví dụ: 1000, 10000)")
    parser.add_argument("--seed", type=int, default=1801, help="Seed độc lập (1801, 1802, 1803, 1804, 1805)")
    parser.add_argument("--distribution", choices=["uniform", "skewed"], default="uniform", help="Phân bố mã chẩn đoán")
    parser.add_argument("--out-dir", type=str, default="datasets/generated", help="Thư mục xuất file dataset")
    parser.add_argument("--oracle-dir", type=str, default="datasets/oracle", help="Thư mục xuất file oracle")
    parser.add_argument("--all-seeds", action="store_true", help="Tự động sinh toàn bộ 5 seeds chuẩn (1801..1805)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    out_path = repo_root / args.out_dir
    oracle_path = repo_root / args.oracle_dir
    out_path.mkdir(parents=True, exist_ok=True)
    oracle_path.mkdir(parents=True, exist_ok=True)

    seeds = [1801, 1802, 1803, 1804, 1805] if args.all_seeds else [args.seed]

    print("=================================================================")
    print("   MEDSHARE-LAB: SYNTHETIC DATASET GENERATOR (TOPIC 18 — WP2)    ")
    print("=================================================================")
    print(f"[*] Quy mô (Size):       {args.size} bản ghi")
    print(f"[*] Phân bố:             {args.distribution}")
    print(f"[*] Danh sách Seeds:     {seeds}")
    print(f"[*] Thư mục Dataset:     {out_path}")
    print(f"[*] Thư mục Oracle:      {oracle_path}")
    print("-----------------------------------------------------------------")

    for s in seeds:
        records = generate_dataset(args.size, s, args.distribution)
        filename = f"ehr_{args.size}_{args.distribution}_seed{s}.json"
        filepath = out_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        print(f"[+] [Seed {s}] Đã tạo {len(records)} bản ghi -> {filepath.name}")

        # Tạo file Oracle tương ứng
        oracle = build_oracle(records)
        oracle_file = oracle_path / f"oracle_{args.size}_{args.distribution}_seed{s}.json"
        with open(oracle_file, "w", encoding="utf-8") as f:
            json.dump(oracle, f, ensure_ascii=False, indent=2)
        print(f"    --> Đã lưu Plaintext Oracle -> {oracle_file.name}")

    print("=================================================================")
    print("   [OK] SINH DỮ LIỆU SYNTHETIC HOÀN TẤT THÀNH CÔNG!              ")
    print("=================================================================")


if __name__ == "__main__":
    main()

