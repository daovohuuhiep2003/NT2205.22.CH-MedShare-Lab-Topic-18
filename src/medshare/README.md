# Python core (Zone Z1)

Đã triển khai (WP3–WP6, WP10). Chạy trên host trong `.venv`, Python 3.12.

- `auth/`: IdP Zone Z1 — Argon2id, JWT HS256, HMAC `record_mac`, cấp/thu hồi tài khoản.
- `gateway/`: `service.py` (Dual PEP, field projection, ingest/read, attachments) và `api.py` (FastAPI cho Web Portal).
- `crypto/`: field envelope AES-256-GCM + AAD RFC 8785, blind index HMAC, file cipher chunked, adapter CP-ABE/BFV. Không tự viết primitive.
- `broker/`: KeyBroker (PEP độc lập), KeyCapsule, client Vault Transit + Mock KMS.
- `policy/`: ABAC PDP deny-by-default, break-glass, revocation.
- `storage/`: `MongoStorage` (MongoDB 7.0) và `MinioStorage`.

Chưa có: PQC migration (WP9), audit checkpoint Z3. Bản đồ chi tiết: [MUC_LUC_DU_AN.md](../../MUC_LUC_DU_AN.md); thiết kế: [crypto design](../../docs/design/crypto-and-protocol-design.md).
