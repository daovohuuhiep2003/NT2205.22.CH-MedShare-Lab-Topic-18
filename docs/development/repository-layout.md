# Cây thư mục và quy ước

## Root

Root chỉ giữ README, CONTRIBUTING, SECURITY, cấu hình Git/editor/CI và các thư mục theo trách nhiệm. Không đặt proposal/plan/version-copy rải rác ở root.

## Cây tổng quan

- MedShare-Lab/
  - .github/ — workflows và PR template
  - docs/
    - proposal/ — project-proposal.md, project-proposal.docx
    - requirements/ — course-guideline.md, topic-18.md, source-analysis.md
    - planning/ — implementation-plan.md, team-work-plan.docx
    - design/, testing/, diagrams/, adr/, development/, maintenance/
  - src/medshare/ — gateway/, crypto/, broker/, policy/, storage/
  - workers/ — abe/, he/, pqc/
  - infra/ — cấu hình lab khi triển khai
  - tests/ — tooling/, unit/, integration/, security/
  - datasets/, benchmarks/, analysis/, evidence/
  - scripts/ — render_proposal.py, validate_docs.py, validate_proposal_sync.py, check_repo.py
  - README.md, CONTRIBUTING.md, SECURITY.md, .gitignore, .gitattributes, .editorconfig
  - .local-backups/ — chỉ local, không push

## Tài liệu

- `docs/proposal/`: Markdown chuẩn và DOCX sinh tự động.
- `docs/requirements/`: tài liệu gốc học phần bất biến và phân tích nguồn.
- `docs/planning/`: implementation plan và team work plan hiện có.
- `docs/design/`: protocol, key lifecycle và thiết kế mật mã.
- `docs/testing/`: kế hoạch thí nghiệm, test catalog, traceability.
- `docs/diagrams/`: Mermaid source và PNG proposal đã review.
- `docs/adr/`: quyết định kiến trúc có lý do, trạng thái và ảnh hưởng.
- `docs/development/`: cấu trúc, workflow Git và hướng dẫn phát triển.
- `docs/maintenance/`: kết quả validation và thay đổi cấu trúc.

## Source và runtime

- `src/medshare/{gateway,crypto,broker,policy,storage}/`: package Python core; storage có adapter SQL/NoSQL khi implement.
- `workers/{abe,he,pqc}/`: thí nghiệm nâng cao độc lập; chọn runtime/dependency trong feasibility spike.
- `infra/`: DB, network, KMS/PDP, lab-volume và runbook. Chưa tạo Compose giả với credentials mặc định hoặc service placeholder.
- `tests/{tooling,unit,integration,security}/`: tooling có tests thật; ba nhóm ứng dụng sẽ được tạo theo module.

## Dữ liệu và bằng chứng

- `datasets/`: generator và config; `generated/`, `oracle/`, `raw/` chỉ local và bị ignore.
- `benchmarks/`: workload harness/config; `results/` local.
- `analysis/`: notebook/script thống kê; `output/` local.
- `evidence/`: schema, manifest mẫu không secret và báo cáo đã sanitize; `runs/` local cho raw evidence.

Không commit chỉ để lấp thư mục. README trong các vùng chưa triển khai mô tả mục đích và điều kiện bắt đầu. Không tuyên bố có API, encryption hoặc benchmark khi mới có namespace.

## Chính sách file

Dùng tên ASCII, kebab-case cho tài liệu, snake_case cho Python. Dependency manifest/lockfile được tạo bằng package manager khi thực sự có dependency đã duyệt; không có manifest giả trong scaffold. Markdown UTF-8/LF, DOCX/PNG binary. Hai source requirements có `-text` trong gitattributes để giữ hash qua Windows/Linux.

`.local-backups/` chứa archive khôi phục trước cấu trúc, không dùng làm lịch sử dự án và không push. Sau khi xác nhận remote backup và không cần bản nộp cũ, chủ dự án có thể tự xóa archive này.
