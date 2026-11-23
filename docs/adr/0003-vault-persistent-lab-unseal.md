# ADR-0003: Vault chạy file storage bền vững + tự unseal (lab), bỏ dev mode

- **Trạng thái:** accepted (23/11/2026)
- **Liên quan:** SR-11, SR-14, SR-16; T-13, T-14, T-16; M-03

## Bối cảnh
Vault chạy `server -dev` lưu toàn bộ trong RAM. Mỗi lần container restart: Transit engine biến mất (test collection lỗi `no handler for route "transit/keys/..."`) và **mọi KEK bị mất**, khiến capsule cũ trong MongoDB không unwrap được — tương đương mất dữ liệu.

## Quyết định
- `infra/vault/config.hcl`: storage `file` tại `/vault/file` (volume `infra/runtime/vault`), listener TCP không TLS (lab).
- `infra/vault/entrypoint.sh` mỗi lần khởi động: init (1 key share) nếu chưa có → unseal → tạo token lab cố định `dev-root-token-topic18` (để không đổi cấu hình client) → bật Transit. Idempotent.
- Healthcheck chỉ `healthy` khi Transit đã mount.

## Alternatives
Giữ dev mode + script bật Transit (vẫn mất KEK); Shamir nhiều share giữ bởi người (đúng chuẩn nhưng cần thao tác tay mỗi lần khởi động); auto-unseal qua Cloud KMS/HSM (ngoài phạm vi lab).

## Ảnh hưởng bảo mật
- Unseal key + initial root token nằm trong `infra/runtime/vault/.lab-init` cùng volume ⇒ **seal không bảo vệ trước người có volume**. Chấp nhận cho lab, ghi trong SECURITY.md; môi trường thật phải dùng auto-unseal HSM/KMS và token theo policy tối thiểu thay cho root.
- Kiểm chứng: tạo KEK → `docker restart` → KEK còn; `pytest tests/` 100 passed.
- Xóa `infra/runtime/vault` = mất toàn bộ KEK (đã ghi trong HUONG_DAN_DICH_VU.md).
