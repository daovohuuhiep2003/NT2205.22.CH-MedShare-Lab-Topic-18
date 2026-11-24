# ADR-0001: Chỉ dùng MongoDB 7.0 + MinIO, bỏ PostgreSQL

- **Trạng thái:** accepted (11/2026)
- **Liên quan:** SR-01, SR-02, SR-03; T-01, T-02; E1, E2; TC-02, TC-27

## Bối cảnh
Proposal và implementation plan v1.1 dự kiến chạy P1 trên cả PostgreSQL 16 và MongoDB 7.0 để so sánh SQL/NoSQL. Duy trì hai DAL, hai bộ schema và hai bộ test làm phân tán công sức trong khi câu hỏi nghiên cứu chính (DBA đọc được gì) không phụ thuộc loại DBMS. Dữ liệu ảnh y tế (DICOM/X-quang/PDF) lại cần object storage.

## Quyết định
- Văn bản/JSON: **MongoDB 7.0**, collections `encrypted_patients`, `key_capsules`, `search_index`, `patient_attachments`, `z1_identity_accounts`.
- Tệp nhị phân: **MinIO** (S3), mã hóa chunked AES-256-GCM trước khi upload; MongoDB chỉ giữ metadata.
- Xóa `PostgresStorage`, DDL SQL, container `postgres-cloud`.

## Alternatives
Giữ cả hai DBMS (tốn công, không thêm insight bảo mật chính); chỉ PostgreSQL + RLS (RLS không chống superuser/BYPASSRLS, xem source-analysis); lưu file dưới dạng GridFS (gộp blob với DB của DBA).

## Ảnh hưởng
- Mất phần so sánh SQL vs NoSQL và kiểm thử RLS trong E1/E2/TC-27; TC-27 được kiểm chứng ở Broker PEP thay cho RLS.
- Proposal đã cập nhật lên bản 1.2 (Phụ lục B). Yêu cầu Master "comparison SQL vs NoSQL" chuyển thành phân tích kiến trúc Pattern A–D, không có số đo PostgreSQL — **cần giảng viên phê duyệt**.
- `docs/development/environment-setup.md`, `MUC_LUC_DU_AN.md`, `implementation-plan.md` §8.1 đã cập nhật.
