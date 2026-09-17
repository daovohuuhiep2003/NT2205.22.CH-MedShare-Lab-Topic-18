# An toàn dữ liệu và báo lỗi bảo mật

MedShare-Lab là đồ án nghiên cứu, chưa có bảo đảm production. Chỉ dùng dữ liệu tổng hợp hoặc được phép; không đưa hồ sơ bệnh nhân thật, khóa production hoặc credentials cloud thật vào repository.

## Không được commit

- Private keys, AA master secret, KMS material, bearer token, cookie/session, mật khẩu và credential files.
- `.env`, dump/backup DB, raw request/response hoặc log chứa plaintext/khóa.
- Generated dataset, oracle, raw benchmark và run artifacts chưa rà soát.

Các output directory và `.local-backups/` được ignore. Không dùng `git add -f` để bỏ qua quy tắc. File đã track không được bảo vệ chỉ bằng việc thêm `.gitignore`.

## Khi phát hiện lộ secret

Ngừng chia sẻ artifact, báo trực tiếp partner/giảng viên qua kênh riêng, thu hồi/rotate credential liên quan trước; không dán secret vào issue/PR. Xóa file hiện tại không xóa lịch sử Git. Xử lý history cần thống nhất cộng tác viên.

## Báo lỗi và quyền chia sẻ

Chưa cấu hình email tiếp nhận hoặc maintainer handle. Liên hệ nhóm qua kênh riêng đã thống nhất; không công khai exploit kèm thông tin truy cập lab.

Không tự gán license nguồn mở cho tài liệu học phần/bên thứ ba. Nhóm cần xác nhận quyền chia sẻ trước khi đổi remote sang public.
