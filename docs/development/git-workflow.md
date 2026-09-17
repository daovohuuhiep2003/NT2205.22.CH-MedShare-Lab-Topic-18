# Git workflow cho nhóm hai người

## Khởi tạo và chia sẻ

Repository local dùng nhánh `main`. Chưa có commit/remote được tạo thay người dùng. Nếu thư mục copy chưa có Git, chạy `git init -b main`.

1. Tạo remote **private, trống** trên GitHub/GitLab; không bật tạo README/license để tránh history không liên quan. Không đặt token trong URL.
2. Tại root, chạy `python -B scripts/check_repo.py`, đọc `git status --short` và kiểm tra nội dung sẽ commit.
3. Stage bằng `git add .`; kiểm tra `git diff --cached --stat`, `git diff --cached --check` và diff nội dung an toàn. Không stage `.local-backups`, runtime data hay secrets.
4. Tạo commit với `git commit -m "chore: initialize MedShare-Lab repository"`. Git identity do mỗi người tự cấu hình; không dùng thông tin người khác.
5. Thêm origin bằng `git remote add origin <REMOTE_URL>` với SSH/HTTPS URL không chứa credential; push `git push -u origin main`. Thay placeholder bằng remote thực tế.
6. Trên remote, chủ repo mời partner với quyền Write/Developer phù hợp. Partner clone bằng tài khoản của họ; không share token/password.

Trên GitHub, workflow có sẵn tại `.github/workflows/ci.yml`; GitLab hoặc nền tảng khác dùng cùng lệnh kiểm tra nhưng cần cấu hình CI tương ứng. Việc mời cộng tác viên và push không được thực hiện tự động.

## Làm việc hằng ngày

- Trước mở nhánh: `git switch main`, `git pull --ff-only`, rồi `git switch -c feat/ten-cong-viec`.
- Giữ commit nhỏ; gắn E/SR/CR/TC trong mô tả khi phù hợp.
- Push branch, mở PR, partner review và người dùng merge thủ công. Không force-push main; không bật auto-merge.
- Bảo vệ main bằng yêu cầu CI pass và một reviewer nếu remote/plan cho phép. CODEOWNERS chưa tạo vì chưa có handle thực tế.

## Tránh conflict tài liệu

Proposal Markdown là nguồn chuẩn. Khi conflict DOCX, hợp nhất Markdown trước, chạy renderer rồi commit artifact mới; không cố ghép binary Word. Plan phân công Word do một người sửa mỗi lượt hoặc chuyển sang Markdown trong một đầu việc được thống nhất.

## Quyền và dữ liệu

Tên/mã học viên trong proposal và tài liệu giảng viên có thể không phù hợp repo public. Không tự cấp license hoặc mở public. Xem [SECURITY](../../SECURITY.md) và [CONTRIBUTING](../../CONTRIBUTING.md).
