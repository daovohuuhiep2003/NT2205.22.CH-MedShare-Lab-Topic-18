#!/usr/bin/env python3
"""
MedShare-Lab: Database Loader for Baseline B0 (Topic 18 — NT2205.11.CH)
Tuần 3 — WP2: Nạp dữ liệu tổng hợp vào MongoDB 7.0 (Baseline Plaintext).

Cung cấp:
- Collection và Indexes cho MongoDB (collection ehr_records).
- Batch loading hiệu năng cao (sử dụng pymongo).
- Đo lường dung lượng lưu trữ (Data size, Index size, Storage size).
- Cơ chế reset collection sạch sẽ trước mỗi lần chạy benchmark.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymongo

# Cấu hình mặc định cho môi trường Lab
DEFAULT_MONGO_URL = "mongodb://medshare_dba:dba_secret_dev_pass@localhost:27017/medshare_records?authSource=admin"


class DatabaseLoader:
    """Loader chuyên dụng cho MongoDB 7.0 trong dự án MedShare-Lab."""

    def __init__(self, mongo_url: str = DEFAULT_MONGO_URL):
        self.mongo_url = mongo_url

    # --------------------------------------------------------------------------
    # MongoDB Operations
    # --------------------------------------------------------------------------
    def init_mongo(self, drop_existing: bool = False):
        """Khởi tạo collection ehr_records và compound indexes trên MongoDB."""
        client = pymongo.MongoClient(self.mongo_url)
        db = client.get_default_database()
        if drop_existing:
            db.drop_collection("ehr_records")

        col = db["ehr_records"]
        col.create_index([(("tenant_id", pymongo.ASCENDING)), ("record_id", pymongo.ASCENDING)], unique=True)
        col.create_index([("tenant_id", pymongo.ASCENDING), ("external_patient_id", pymongo.ASCENDING)])
        col.create_index([("tenant_id", pymongo.ASCENDING), ("diagnosis_code", pymongo.ASCENDING)])
        client.close()

    def load_mongo(self, records: List[Dict[str, Any]], batch_size: int = 500) -> float:
        """Nạp dữ liệu vào MongoDB theo batch insert_many. Trả về thời gian thực thi (giây)."""
        start_time = time.perf_counter()
        client = pymongo.MongoClient(self.mongo_url)
        db = client.get_default_database()
        col = db["ehr_records"]

        # Sao chép và dùng record_id làm _id của Mongo để đảm bảo tính bất biến
        mongo_docs = []
        for r in records:
            doc = dict(r)
            doc["_id"] = r["record_id"]
            mongo_docs.append(doc)

        for i in range(0, len(mongo_docs), batch_size):
            batch = mongo_docs[i:i + batch_size]
            try:
                col.insert_many(batch, ordered=False)
            except pymongo.errors.BulkWriteError:
                pass  # Bỏ qua trùng lặp nếu nạp lại

        client.close()
        return time.perf_counter() - start_time

    def get_mongo_stats(self) -> Dict[str, Any]:
        """Lấy số lượng document và kích thước lưu trữ trên MongoDB."""
        client = pymongo.MongoClient(self.mongo_url)
        db = client.get_default_database()
        stats = db.command("collstats", "ehr_records")
        client.close()

        count = stats.get("count", 0)
        data_size = stats.get("size", 0)
        storage_size = stats.get("storageSize", 0)
        total_index_size = stats.get("totalIndexSize", 0)

        return {
            "record_count": count,
            "data_bytes": data_size,
            "storage_bytes": storage_size,
            "index_bytes": total_index_size,
            "total_bytes": storage_size + total_index_size,
            "data_size_kb": round(data_size / 1024, 2),
            "storage_size_kb": round(storage_size / 1024, 2),
        }

    def reset_all(self):
        """Xóa sạch collection trên MongoDB."""
        self.init_mongo(drop_existing=True)


def main():
    parser = argparse.ArgumentParser(description="MedShare-Lab Dataset Loader for Baseline B0")
    parser.add_argument("--file", type=str, required=True, help="Đường dẫn file dataset JSON cần nạp")
    parser.add_argument("--reset", action="store_true", help="Xóa sạch dữ liệu cũ trước khi nạp")
    args = parser.parse_args()

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"[LỖI] Không tìm thấy file: {filepath}")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        records = json.load(f)

    print("=================================================================")
    print("   MEDSHARE-LAB: DATABASE LOADER (BASELINE B0 — PLAINTEXT)       ")
    print("=================================================================")
    print(f"[*] File dataset:     {filepath.name} ({len(records)} bản ghi)")
    print(f"[*] Reset bảng cũ:    {args.reset}")
    print("-----------------------------------------------------------------")

    loader = DatabaseLoader()

    if args.reset:
        print("[*] Đang khởi tạo lại schema và xóa dữ liệu cũ...")
        loader.init_mongo(drop_existing=True)

    print("[*] Đang nạp dữ liệu vào MongoDB 7.0...")
    mongo_duration = loader.load_mongo(records)
    mongo_stats = loader.get_mongo_stats()
    print(f"    --> Hoàn tất trong {mongo_duration:.3f}s (Throughput: {len(records)/mongo_duration:.1f} rec/s)")
    print(f"    --> Tổng documents: {mongo_stats['record_count']}, Dung lượng dữ liệu: {mongo_stats['data_size_kb']} KB, Lưu trữ: {mongo_stats['storage_size_kb']} KB")

    print("=================================================================")
    print("   [OK] NẠP DỮ LIỆU BASELINE THÀNH CÔNG!                         ")
    print("=================================================================")


if __name__ == "__main__":
    main()
