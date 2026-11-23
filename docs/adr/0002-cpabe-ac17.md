# ADR-0002: CP-ABE dùng AC17 (Charm-Crypto) thay ứng viên BSW07

- **Trạng thái:** accepted (11/2026)
- **Liên quan:** SR-07, SR-08; T-07, T-08; M-07; E4; TC-11 → TC-14

## Bối cảnh
M-07 ghi "Candidate BSW07, exact scheme/backend/parameters được pin sau spike". Spike Tuần 2 tái sử dụng mã của thành viên B (`daovohuuhiep2003/Project-MMH-CP-ABE`, đánh giá tại `docs/design/cpabe-source-evaluation.md`) vốn hiện thực AC17.

## Quyết định
- Scheme: **AC17 (Agrawal–Chase 2017)** qua Charm-Crypto + Stanford PBC 0.5.14, container `workers/abe/`.
- Đường cong: **BN254** (Type-3, mặc định cho báo cáo) và **SS512** (Type-1, ~80-bit, chỉ để so sánh nghiên cứu).
- KEM/DEM: CP-ABE bọc `share_DEK` 32 byte; HKDF-SHA-256 với context `tenant_id`, `epoch_id`, `policy_hash`; dữ liệu mã hóa AES-256-GCM.
- Dịch vụ REST FastAPI `:9002`, có CLI fallback.

## Ảnh hưởng
- Không claim mức an toàn 128-bit cho SS512; không claim CCA hay PQ cho CP-ABE.
- Thu hồi theo epoch (TC-13) PASS; dữ liệu đã giải mã offline không thu hồi được (TC-14 = LIMIT).
- Proposal vẫn nêu BSW07 là ứng viên; báo cáo cuối dẫn ADR này.
