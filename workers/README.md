# Independent crypto workers

P2 CP-ABE, P3 BFV và P4 PQC chạy trong container riêng, tách khỏi Python core.

| Worker | Trạng thái | Giao tiếp |
|---|---|---|
| `abe/` | Đã tích hợp (WP8, E4) — AC17 BN254/SS512 | REST FastAPI `:9002`, service `abe-worker` trong compose |
| `he/` | Đã tích hợp (WP7, E7) — SEAL 4.1.2 BFV | Binary CLI `seal_bfv_engine`, gọi bởi `crypto/he_client.py` |
| `pqc/` | Smoke test — ML-KEM-768, ML-DSA-65 (liboqs) | CLI; tích hợp là WP9 (Tuần 11) |
