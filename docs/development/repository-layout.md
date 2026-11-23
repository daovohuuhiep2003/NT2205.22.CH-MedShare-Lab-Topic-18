# Cây thư mục và quy ước

## Root

Root giữ README, CONTRIBUTING, SECURITY, LICENSE, cấu hình Git/editor/CI, các thư mục theo trách nhiệm và bộ tài liệu tiếng Việt cho nhóm/giảng viên (`TIEN_DO_HIEN_TAI.md`, `HUONG_DAN_DICH_VU.md`, `MUC_LUC_DU_AN.md`, báo cáo sơ lược, kịch bản thuyết trình, slide, sơ đồ Draw.io, `plan-mTLS.md`). Danh sách đầy đủ: [MUC_LUC_DU_AN.md](../../MUC_LUC_DU_AN.md).

## Cây tổng quan

- MedShare-Lab/
  - .github/ — workflows và PR template
  - docs/
    - proposal/ — project-proposal.md, project-proposal.docx
    - requirements/ — course-guideline.md, topic-18.md, source-analysis.md
    - planning/ — implementation-plan.md, team-work-plan.docx
    - design/, testing/, diagrams/, adr/, development/, maintenance/
  - src/medshare/ — auth/, gateway/, crypto/, broker/, policy/, storage/
  - frontend/ — Web Portal Vue 3 (Vite, TailwindCSS)
  - workers/ — abe/, he/, pqc/
  - infra/ — docker-compose.yml, vault/, certs/, runtime/ (local)
  - tests/ — tooling/, unit/, integration/, security/
  - datasets/, benchmarks/, analysis/, evidence/
  - scripts/ — tooling tài liệu + setup, portal, ingest, pptx
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

- `src/medshare/{auth,gateway,crypto,broker,policy,storage}/`: package Python core đã triển khai; storage dùng MongoDB + MinIO ([ADR-0001](../adr/0001-mongodb-only-storage.md)).
- `workers/{abe,he,pqc}/`: worker mật mã nâng cao trong container riêng (ABE REST, HE CLI, PQC smoke test).
- `infra/`: Compose 4 service (MongoDB, Vault, MinIO, abe-worker) với **credentials dev mặc định công khai** (xem SECURITY.md), cấu hình Vault bền vững, cert Portal.
- `tests/{tooling,unit,integration,security}/`: tooling, unit và security đã có test (100 tests); integration chưa có.

## Dữ liệu và bằng chứng

- `datasets/`: generator và config; `generated/`, `oracle/`, `raw/` chỉ local và bị ignore.
- `benchmarks/`: workload harness/config; `results/` local.
- `analysis/`: notebook/script thống kê; `output/` local.
- `evidence/`: schema, manifest mẫu không secret và báo cáo đã sanitize; `runs/` local cho raw evidence.

Không commit chỉ để lấp thư mục. README trong mỗi vùng ghi trạng thái thực tế; không tuyên bố có API, encryption hoặc benchmark khi chưa có code và test tương ứng.

## Chính sách file

Dùng tên ASCII, kebab-case cho tài liệu, snake_case cho Python. Python core chưa có manifest/lockfile (dependency được cài bởi `scripts/setup_ubuntu.sh`, liệt kê ở [environment-setup](environment-setup.md)); frontend có `package.json` + `package-lock.json`. Markdown UTF-8/LF, DOCX/PNG binary. Hai source requirements có `-text` trong gitattributes để giữ hash qua Windows/Linux.

`.local-backups/` chứa archive khôi phục trước cấu trúc, không dùng làm lịch sử dự án và không push. Sau khi xác nhận remote backup và không cần bản nộp cũ, chủ dự án có thể tự xóa archive này.
