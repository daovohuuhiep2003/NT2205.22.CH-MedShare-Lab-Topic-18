# Repository tooling

Tất cả scripts hiện tại dùng Python standard library, offline, không phụ thuộc Office/crypto packages.

- render_proposal.py: sinh DOCX từ docs/proposal/project-proposal.md; --check chỉ so sánh, không ghi file.
- validate_proposal_sync.py: so đoạn/bảng/images/links của DOCX với Markdown; --self-test kiểm thử validator.
- validate_docs.py: links, phases, IDs, Mermaid structural checks và SHA-256 source requirements; --self-test.
- check_repo.py: chạy toàn bộ checks và tooling tests, không deploy/build ứng dụng.

Chạy từ root bằng python -B scripts/check_repo.py. Không dùng renderer cho Markdown tổng quát ngoài cú pháp được hỗ trợ. Không thêm dependency để phục vụ skeleton.
