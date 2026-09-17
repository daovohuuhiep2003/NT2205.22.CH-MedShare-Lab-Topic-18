# MedShare-Lab — Topic 18

Đồ án **Mật mã học và ứng dụng — NT2205.11.CH**, bậc thạc sĩ An toàn thông tin; nhóm 2 học viên, dự kiến 12 tuần.

**Trạng thái:** proposal và thiết kế đã có; repository đang ở giai đoạn khởi tạo. Ứng dụng, DB/KMS và worker mật mã **chưa được triển khai**. Kiểm tra repository không phải bằng chứng an toàn mật mã hay kết quả benchmark.

## Nguồn chuẩn

- **Proposal chuẩn:** [docs/proposal/project-proposal.md](docs/proposal/project-proposal.md). Chỉnh file này trước; không sửa DOCX làm nguồn thiết kế.
- **Bản Word đồng bộ:** [docs/proposal/project-proposal.docx](docs/proposal/project-proposal.docx), sinh bằng `python scripts/render_proposal.py`.
- [Kế hoạch triển khai](docs/planning/implementation-plan.md) và [kế hoạch phối hợp](docs/planning/README.md). Phân công do hai thành viên chốt trong plan.
- [Guideline](docs/requirements/course-guideline.md) và [Topic 18](docs/requirements/topic-18.md) giữ nguyên nội dung, có kiểm tra SHA-256.

## Cấu trúc repository

| Thư mục | Nội dung |
|---|---|
| `docs/` | Proposal, requirements, planning, design, testing, diagrams, ADR, Git workflow |
| `src/medshare/` | Khung package Python; chưa có implementation |
| `workers/` | Runtime độc lập cho CP-ABE, SEAL BFV, PQC |
| `infra/` | Hạ tầng và runbook lab; chưa có stack chạy được |
| `tests/` | Tooling tests hiện tại; unit/integration/security tests khi viết ứng dụng |
| `datasets/` | Generator/config synthetic; output và oracle không commit |
| `benchmarks/`, `analysis/`, `evidence/` | Harness, thống kê và bằng chứng đã rà soát; chưa có số đo |
| `scripts/` | Render DOCX, kiểm tra tài liệu và repository |
| `.github/` | CI và mẫu pull request |

Xem [cây thư mục và quy ước](docs/development/repository-layout.md). Không tạo primitive hoặc service giả để lấp thư mục.

## Bắt đầu làm việc

1. Cài Python 3.12+ và Git. Tooling hiện tại chỉ dùng **thư viện chuẩn Python**; chưa cần cài thư viện mật mã, Docker hoặc Office.
2. Clone repository, đọc proposal và [CONTRIBUTING](CONTRIBUTING.md).
3. Chạy `python -B scripts/check_repo.py`: unit tests/tooling, links, mã, DOCX và đồng bộ Markdown; không chạy service hoặc ghi dữ liệu ứng dụng.
4. Khi sửa proposal: chỉnh Markdown, chạy `python -B scripts/render_proposal.py`, rồi chạy lại `python -B scripts/check_repo.py`. Commit cả Markdown và DOCX.
5. Bắt đầu WP1–WP2: trust model, E5/baseline E8 và feasibility ABE/HE/PQC. Chỉ thêm dependency bằng package manager khi chốt runtime.

## Phạm vi nghiên cứu

Hồ sơ y tế đa tenant trên PostgreSQL/MongoDB với dữ liệu tổng hợp: volume baseline; field envelope + broker/KMS + ABAC; equality blind index có leakage contract; CP-ABE share; BFV SUM/count; PQC key/signature migration. Có 8 thí nghiệm E1–E5/E7–E9, 18 SR, 12 CR và 30 nhóm TC. Không xây DBMS mới, không full FHE SQL, không tuyên bố zero leakage hoặc end-to-end PQ security.

## Chia sẻ với partner

Tạo **remote private**, push nhánh `main`, rồi cấp quyền cộng tác; xem [Git workflow](docs/development/git-workflow.md). Không có remote, tài khoản partner hoặc quyền truy cập nào được cấu hình tự động.

Không commit secret, credentials, session, `.env`, DB dump, dữ liệu thật hoặc raw evidence. `.gitignore` không thay review nội dung trước push. Xem [SECURITY](SECURITY.md).

## Trạng thái kiểm chứng

[Validation và giới hạn](docs/maintenance/validation.md) ghi đã kiểm tra gì. CI chỉ kiểm tra repository; integration/security tests và benchmark ứng dụng vẫn NOT_RUN. Word pagination và URL bên ngoài cần kiểm tra riêng.
