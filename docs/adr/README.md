# Architecture Decision Records

Tạo ADR khi đổi trust boundary, scheme/backend, baseline E8, E5 hoặc runtime. Tên `NNNN-ten-quyet-dinh.md`; không coi candidate là quyết định đã duyệt.

Mỗi ADR ghi: proposed/accepted/superseded; bối cảnh và SR/CR; lựa chọn; alternatives; lý do; ảnh hưởng bảo mật/leakage/vận hành; test/evidence cần cập nhật.

| ADR | Quyết định | Trạng thái |
|---|---|---|
| [0001](0001-mongodb-only-storage.md) | Chỉ MongoDB 7.0 + MinIO, bỏ PostgreSQL | accepted |
| [0002](0002-cpabe-ac17.md) | CP-ABE dùng AC17 (BN254/SS512) thay BSW07 | accepted |
| [0003](0003-vault-persistent-lab-unseal.md) | Vault file storage + tự unseal cho lab | accepted |
| 0004 *(chưa có file)* | mTLS nội bộ ECDSA P-256 + SPIFFE ID cho Gateway ↔ Vault/MinIO/abe-worker; chứng chỉ ML-DSA và hybrid KEM chỉ đo trong thí nghiệm E8 mở rộng — chi tiết trong `plan-mTLS.md` v2.0 | proposed |

ADR-0004 sẽ được tạo file và chuyển sang accepted khi bắt đầu triển khai M1 (đánh giá tại `TIEN_DO_HIEN_TAI.md` mục 7). Các quyết định trên đã được đưa vào [proposal bản 1.2](../proposal/project-proposal.md) (Phụ lục B).
