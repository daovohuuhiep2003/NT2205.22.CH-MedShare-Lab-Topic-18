# HE worker — P3 SEAL BFV

Microsoft SEAL 4.1.2 BFV, N = 8192, mức 128-bit; plain modulus 30-bit batching (`seal_bfv_engine.cpp`), 20-bit trong `smoke_test.cpp`. Chỉ SUM/count số nguyên trên cohort được duyệt; không arbitrary encrypted SQL.

- `seal_bfv_engine` (binary, gitignored — build lại từ `seal_bfv_engine.cpp`): chế độ `benchmark`, `aggregate`, `tamper_test`; gọi bởi `src/medshare/crypto/he_client.py`.
- Smoke test container: `docker build -t medshare-he-worker ./workers/he && docker run --rm medshare-he-worker`.
- Kết quả: E7, TC-18, TC-30 PASS; TC-19 = LIMIT (không bảo vệ tính đúng của kết quả trước worker độc hại).
