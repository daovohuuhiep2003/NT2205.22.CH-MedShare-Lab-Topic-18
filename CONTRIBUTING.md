# Hướng dẫn cộng tác

## Quy trình

1. Thống nhất đầu việc nhỏ trong [plan](docs/planning/implementation-plan.md); ghi E/SR/CR/TC liên quan.
2. Mỗi người làm trên branch riêng: `feat/`, `test/`, `docs/` hoặc `fix/` cộng tên công việc. Không mặc định phân công người bằng cấu trúc repository.
3. Tạo module cùng test. Không implement primitive mật mã từ đầu; xác minh exact scheme/API/parameters trước dùng thư viện.
4. Chạy `python -B scripts/check_repo.py` và tests ứng dụng liên quan nếu module đã có.
5. Mở PR nhỏ, ghi phạm vi, test đã chạy và giới hạn. Partner review; người dùng tự quyết định merge, không auto-merge.

## Tài liệu

- [Proposal Markdown](docs/proposal/project-proposal.md) là nguồn chuẩn. DOCX là artifact sinh từ Markdown; không merge thủ công hai bản DOCX. Giải quyết conflict ở Markdown rồi render lại.
- Guideline/topic được giữ nguyên byte; không auto-format hoặc sửa hash để làm check pass.
- Thiết kế ở `docs/design/`; quyết định đổi stack hoặc trust boundary ghi ở `docs/adr/`.
- Plan phân công Word hiện có ở `docs/planning/team-work-plan.docx`; tránh hai người sửa cùng lúc. Các lựa chọn trong plan nháp cần đồng bộ proposal trước triển khai.

## Mã nguồn và dependency

- Python core dưới `src/medshare/`; worker ABE/HE/PQC có runtime riêng, không trộn mọi dependency vào gateway.
- Chưa có dependency ứng dụng. Chỉ tạo manifest/lockfile bằng package manager khi chốt runtime; không thêm thư viện chỉ để scaffolding.
- Không hard-code khóa, nonce cố định hoặc public seed cho khóa. Seed dữ liệu synthetic độc lập với CSPRNG mật mã.
- Không coi directory skeleton hay tooling PASS là implementation hoàn thành. Evidence chỉ thêm sau khi thực nghiệm thật.

## Trước push

Kiểm tra staged filenames và diff, đặc biệt `.env`, credentials, dữ liệu và artifact binary. Proposal chứa tên/mã học viên: mặc định dùng remote private; xác nhận quyền chia sẻ trước công bố public.
