# Hạ tầng lab (Docker Compose)

`docker-compose.yml` định nghĩa 4 service: `mongo-cloud` (MongoDB 7.0, Z2), `vault-kms` (Vault 1.15.6, Z1), `minio-cloud` (MinIO, Z2), `abe-worker` (CP-ABE AC17, image cục bộ — build trước bằng `docker build -t medshare-abe-worker ./workers/abe`).

- `vault/config.hcl`, `vault/entrypoint.sh`: Vault chạy file storage bền vững, tự init/unseal, tạo token lab và bật Transit. **Chỉ dành cho lab**: unseal key nằm cùng volume.
- `certs/`: chứng chỉ tự ký cho Portal HTTPS (`*.key` gitignored).
- `runtime/`: volume cục bộ (gitignored). Xóa `runtime/vault` đồng nghĩa mất toàn bộ KEK.

Mật khẩu/token trong compose là giá trị **dev mặc định**, không dùng cho môi trường thật. Kết nối nội bộ hiện chưa có TLS/mTLS — xem `plan-mTLS.md` và `TIEN_DO_HIEN_TAI.md` mục 7. Hướng dẫn vận hành đầy đủ: `HUONG_DAN_DICH_VU.md`.
