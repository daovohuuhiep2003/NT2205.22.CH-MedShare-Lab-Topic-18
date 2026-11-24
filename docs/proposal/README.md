# Proposal — nguồn chuẩn và bản xuất

- **Nguồn chuẩn:** [project-proposal.md](project-proposal.md) — bản 1.2 (23/11/2026). Bản đăng ký 1.1 (16/09/2026) có trong lịch sử Git; thay đổi liệt kê ở Phụ lục B.
- **Bản Word:** [project-proposal.docx](project-proposal.docx), sinh từ Markdown.
- Render tại root: `python -B scripts/render_proposal.py`.
- Kiểm tra không ghi file: `python -B scripts/render_proposal.py --check` và `python -B scripts/validate_proposal_sync.py`.

Renderer dùng Python chuẩn, offline, hỗ trợ các thành phần Markdown hiện tại. Không đọc nội dung DOCX cũ/template ngoài. Cập nhật PNG khi sơ đồ đổi; render DOCX không tự chạy Mermaid CLI.

Bản DOCX chỉnh riêng để nộp giảng viên trước lần cấu trúc repo được giữ trong archive tại `.local-backups/`, không đưa lên Git. File Word ở đây được đồng bộ theo Markdown đúng yêu cầu chủ dự án.

Trước nộp tiếp: mở Word Print Layout xem ngắt trang/bảng; Markdown không bao hàm mọi chỉnh sửa bố cục riêng của Word.
