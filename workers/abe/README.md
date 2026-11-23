# ABE worker — P2 CP-ABE

AC17 (Agrawal–Chase 2017) trên Charm-Crypto + Stanford PBC 0.5.14; đường cong BN254 (mặc định) và SS512 (~80-bit, chỉ so sánh). KEM/DEM: CP-ABE bọc `share_DEK`, HKDF-SHA-256, AES-256-GCM. Quyết định: [ADR-0002](../../docs/adr/0002-cpabe-ac17.md).

- `engine.py`: lõi scheme; `service.py`: REST `:9002` (`/health`, `/api/v1/setup`, `/keygen`, `/export/package`, `/export/decrypt`, `/collusion/test`); `cli.py`: CLI fallback; `smoke_test.py`.
- Build: `docker build -t medshare-abe-worker ./workers/abe` (bắt buộc trước `docker compose up`).
- Kết quả: E4, TC-11 → TC-14 (TC-14 = LIMIT: không thu hồi dữ liệu đã giải mã offline).
