# Scripts

**Repository tooling** (Python standard library, offline):
- `render_proposal.py`: sinh DOCX từ `docs/proposal/project-proposal.md`; `--check` chỉ so sánh.
- `validate_proposal_sync.py`, `validate_docs.py`: kiểm tra DOCX↔Markdown, links, IDs, Mermaid, SHA-256 nguồn.
- `check_repo.py`: chạy toàn bộ checks + tooling tests (dùng trong CI).

**Vận hành lab** (cần `.venv` và Docker):
- `setup_ubuntu.sh`: cài môi trường Ubuntu từ đầu.
- `run_portal.sh [http|https] [port]`: chạy Web Portal.
- `prepare_medical_samples.py`, `ingest_medical_samples.py`: chuẩn bị và nạp 15 tệp y tế mẫu (DB `DB_NAME`, mặc định `medshare_db`).
- `gen_proposal_pptx.py`: sinh slide proposal.

Chạy từ root, ví dụ `python -B scripts/check_repo.py`.
