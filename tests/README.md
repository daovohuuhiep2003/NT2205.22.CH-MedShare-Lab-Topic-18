# Tests

- tooling/: parser/renderer, đồng bộ proposal và cấu trúc repository — tests đang chạy được.
- unit/: pure application modules khi implement.
- integration/: DB/KMS/PDP/workers; cần lab, không tự chạy trong CI hiện tại.
- security/: negative/adversarial cases TC-01–TC-30, không dùng secrets thật trong fixture.

Chạy tất cả tooling và docs checks bằng python -B scripts/check_repo.py. Không coi kiểm tra thư mục/package import là kiểm thử bảo mật ứng dụng.
