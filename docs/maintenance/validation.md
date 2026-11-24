# Validation và thay đổi cấu trúc repository

## Cập nhật 23/11/2026

- `python -B scripts/check_repo.py`: PASS, 16 tooling tests.
- `PYTHONPATH=src:. .venv/bin/python -m pytest tests/ -q`: **100 passed** trên lab đang chạy (MongoDB, Vault, MinIO, abe-worker). Lần đầu thất bại ở collection `tests/unit/test_portal_api.py` vì Vault dev mode mất Transit sau restart; đã sửa bằng [ADR-0003](../adr/0003-vault-persistent-lab-unseal.md) và kiểm chứng KEK còn sau `docker restart`.
- Sửa thêm: healthcheck MinIO (dùng `wget` thay `curl`), script ingest ghi đúng DB `medshare_db`.
- `validate_docs.py` chỉ kiểm tra link tới file được track: các báo cáo trong `benchmarks/results/` và `evidence/runs/` bị gitignore nên tài liệu ghi chúng dạng đường dẫn text, không dạng link.
- Proposal nâng lên **bản 1.2** (MongoDB + MinIO, AC17, Vault, lịch tuần 10–11, thêm tham khảo [16], Phụ lục B). DOCX sinh lại bằng renderer; `validate_proposal_sync.py` khớp 216/216 đơn vị nội dung, 12 bảng, 2 hình, 18 mục tham khảo (validator nới từ 15 lên 16 tài liệu đánh số). Hình 1 PNG được sửa nhãn "Cloud PostgreSQL / MongoDB" thành "Cloud MongoDB 7.0 + MinIO". Chưa kiểm tra phân trang trong Word.
- CI vẫn chỉ chạy tooling checks; unit/security tests cần lab nên chạy thủ công. Mục bên dưới là bản ghi lần tái cấu trúc 16/09/2026, giữ nguyên làm lịch sử.

## Bản ghi 16/09/2026

Ngày: 16/09/2026. Đây là kiểm tra repository/tài liệu, không phải chứng nhận an toàn mật mã.

## Nguồn chuẩn

[Proposal Markdown](../proposal/project-proposal.md) là nguồn nội dung. [DOCX](../proposal/project-proposal.docx) được sinh bằng [renderer](../../scripts/render_proposal.py) từ Markdown, không nhập ngược các sửa riêng trong Word. Nội dung proposal chỉ đổi đường dẫn liên kết để phù hợp vị trí mới.

Renderer chuẩn Python có ZIP metadata cố định, dùng hình local, không cần Word/Office/dependency ngoài và không truy cập mạng. `--check` so sánh artifact mà không ghi file; validator đồng bộ so nội dung đoạn, hàng/ô bảng, hình và links riêng với renderer.

## Tái cấu trúc và dọn dẹp

- Di chuyển/đổi tên 10 tài liệu theo proposal/requirements/planning/design/testing; cập nhật liên kết. Hai yêu cầu gốc giữ nguyên hash.
- DOCX người dùng đã sửa được sao lưu trước khi sinh lại. Plan phân công Word được giữ nguyên nội dung tại `docs/planning/team-work-plan.docx`.
- Gộp hai ghi chú validation cũ thành tài liệu này; bỏ bản cũ `docs/documentation-validation.md` và `docs/proposal-revision-validation.md` vì chứa trạng thái/đường dẫn không còn đúng.
- Xóa hai file bytecode cache Python có thể tái tạo. Không xóa source, proposal Markdown, thiết kế hay plan phân công.
- Archive khôi phục có 26 file trước thao tác tại `.local-backups/before-restructure-20260916-232105.zip`, đã đối chiếu hash từng file, không đưa lên Git.
- Không còn PDF ở workspace khi bắt đầu lần cấu trúc này; không xóa thêm PDF nào.

## Kiểm tra tái lập

Chạy `python -B scripts/check_repo.py`: syntax, validator self-tests, bundle validation, proposal sync, deterministic DOCX check và tooling tests. Kết quả lệnh hiện tại là căn cứ chính xác cho số tests/files/links; không dựa số đếm cũ khi repo thay đổi.

Các kiểm tra bao gồm nguồn G/T không đổi byte, 10 phase, SR/CR/T/TC/M, E/F, local links, DOCX XML/CRC, nội dung/bảng/hình khớp Markdown, negative parser/path cases và Git ignore rules. Các test tooling mới đặt tại [tests/tooling](../../tests/tooling/test_render_proposal.py).

## Kết quả chạy cuối

- python -B scripts/check_repo.py: PASS, exit code 0; 6 + 8 + 16 = 30 tests, không skip ở máy kiểm tra.
- 12 Python files parse được; 32 Markdown files, 83 local links và 7 Mermaid sources được kiểm tra cấu trúc.
- 206/206 đơn vị nội dung DOCX/Markdown khớp; 11 bảng, 2 hình, 17 mục tham khảo. DOCX dựng lại có 7 XML/rels parts và đọc lại được bằng thư viện tài liệu.
- So sánh Markdown với bản trước di chuyển: nội dung không đổi ngoài link targets. Plan phân công DOCX giữ nguyên SHA-256.
- Git ignore tests đã kiểm tra secrets/local backup/runtime output bị loại trừ và canonical docs/source không bị ignore.
- 61 file ứng viên Git, khoảng 1,9 MB; không có backup/cache/secrets path trong danh sách. Pattern scan văn bản chỉ in tên file, không phát hiện mẫu private key/token/credential URL thông dụng; không thay kiểm tra bí mật toàn diện.
- Git local main đã khởi tạo lại dưới tài khoản Windows của người dùng để tránh dubious ownership. git status chạy bình thường; không tạo global safe.directory exception. Metadata Git rỗng trước đó giữ tại .local-backups/sandbox-git-metadata/.
- Chưa có commit/index/remote; không cấp quyền cộng tác từ xa. Lỗi Windows CRLF trong stdin Git test đã được sửa bằng NUL-delimited binary I/O.

## Giới hạn

- DOCX đã kiểm tra XML/package và có thể đọc lại bằng thư viện tài liệu; không có Office/LibreOffice renderer khả dụng để xác nhận phân trang/in ấn thực tế. Xem Print Layout trước nộp.
- PNG proposal đã được review ở lần trước; Mermaid chỉ kiểm tra cấu trúc, không chạy parser/renderer CLI.
- Web tooling chưa khả dụng; không tuyên bố xác minh lại URL/errata hoặc GitHub Actions latest. CI dùng các major actions đã phổ biến, không khẳng định là bản mới nhất; cần quan sát lần chạy remote đầu tiên.
- Không thêm dependency ứng dụng, không deploy/start DB hoặc worker, không có benchmark/security test ứng dụng. Các namespace mới chỉ là scaffold.
- Không push, tạo remote, commit, mời partner hoặc thay quyền tài khoản. Những việc đó do chủ repository thực hiện theo Git workflow.
