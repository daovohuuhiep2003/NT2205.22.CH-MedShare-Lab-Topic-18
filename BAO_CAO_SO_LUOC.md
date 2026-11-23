# BÁO CÁO SƠ LƯỢC ĐỀ TÀI
## Đề tài 18 – NT2205.11.CH: MedShare-Lab

> **Hệ thống quản lý hồ sơ bệnh án điện tử (EHR) đa thuê bao trên nền tảng Cloud DBMS với bảo mật tầng trường dữ liệu và kiểm soát truy cập thuộc tính**

---

## 1. Bên liên quan (Stakeholders)

| # | Bên liên quan | Vai trò | Quyền lợi / Mối quan tâm | Mức độ tin cậy |
|---|---|---|---|---|
| 1 | **Bệnh nhân** | Chủ thể dữ liệu | Bảo mật thông tin y tế cá nhân; tránh lộ lọt | Không có quyền trực tiếp vào hệ thống |
| 2 | **Bác sĩ / Điều dưỡng** | Người dùng lâm sàng | Truy cập đúng hồ sơ bệnh nhân; tốc độ phản hồi | Tin cậy có điều kiện (theo ABAC) |
| 3 | **Bệnh viện / Tổ chức y tế** | Data Controller (GDPR/HIPAA) | Tuân thủ pháp lý; quản lý chính sách truy cập | Tin cậy trong phạm vi tenant |
| 4 | **Quản trị viên DBMS (DBA)** | Vận hành cơ sở dữ liệu | Duy trì hiệu năng, sao lưu, vá lỗi | **Bán tin cậy** – có quyền DB nhưng KHÔNG được thấy bản rõ |
| 5 | **Nhà cung cấp Cloud DBMS** | Hạ tầng lưu trữ | SLA, uptime, hiệu năng | **Bán tin cậy** – kiểm soát vật lý ổ đĩa |
| 6 | **Nhà cung cấp KMS (Vault)** | Quản lý khoá mã hoá | Tính toàn vẹn dịch vụ khoá | Tin cậy – nằm trong Zone Z1 do bệnh viện kiểm soát |
| 7 | **Kẻ tấn công tiềm năng** | Đối thủ (Adversary) | Lấy cắp dữ liệu bệnh nhân, phá hoại hệ thống | Không tin cậy |
| 8 | **Nhóm nghiên cứu / Đồ án** | Thiết kế & triển khai | Nghiên cứu giải pháp bảo mật tầng trường dữ liệu | N/A |

### Mô hình đối thủ (Adversary Models)

| Ký hiệu | Mô tả |
|---|---|
| **M0** | Kẻ tấn công ngoài mạng, không có credential |
| **M1** | Nhà cung cấp Cloud (có quyền đọc ổ đĩa) |
| **M2** | DBA nội bộ (có quyền `SELECT *` trên DB) |
| **M3** | Bác sĩ từ tenant khác hoặc khoa khác |
| **M4** | Kẻ tấn công replay ciphertext cũ |

---

## 2. Kỹ thuật & Công nghệ Sử dụng

### 2.1 Bảng tổng hợp kỹ thuật

| # | Kỹ thuật / Công nghệ | Mục đích chính | Vấn đề giải quyết | Giai đoạn |
|---|---|---|---|---|
| 1 | **AES-256-GCM** (Field Envelope Encryption) | Mã hoá từng trường dữ liệu lâm sàng riêng lẻ | DBA đọc bản rõ (M2); Cloud snapshot lộ dữ liệu (M1) | P1 |
| 2 | **AAD Context Binding** (Authenticated Additional Data) | Ràng buộc ciphertext vào ngữ cảnh: tenant + record_id + field_name | Tấn công hoán đổi ciphertext giữa các bản ghi (M4) | P1 |
| 3 | **HKDF-SHA256 + HMAC-SHA256** (Blind Index) | Tìm kiếm bình đẳng trên dữ liệu mã hoá mà không giải mã | Frequency inference attack; lộ bản rõ khi query | P1 |
| 4 | **HashiCorp Vault Transit** (Software KMS) | Bọc/giải bọc DEK; xoay vòng KEK; tách biệt vùng tin cậy | DEK bị lộ nếu lưu cùng DB; xoay vòng khoá thủ công | P1 |
| 5 | **ABAC Policy Engine** | Kiểm soát truy cập dựa trên: Role, Dept, Tenant, TimeOfDay | Bác sĩ khoa khác hoặc tenant khác truy cập trái phép (M3) | P1 |
| 6 | **Break-Glass Mechanism** | Truy cập khẩn cấp có kiểm soát (ticket + expiry + audit) | Tình huống cấp cứu không có bác sĩ phụ trách | P1 |
| 7 | **PostgreSQL 16 RLS** | Row-Level Security tại tầng DB | Lọc hàng theo tenant tại DB; phòng thủ nhiều lớp | P1 |
| 8 | **MongoDB 7.0** | Lưu trữ NoSQL mã hoá cho tài liệu lâm sàng bán cấu trúc | Dữ liệu y tế có cấu trúc linh hoạt (notes, imaging metadata) | P1 |
| 9 | **CP-ABE** (Charm-Crypto, AC17) | Chia sẻ dữ liệu tinh tế dựa trên chính sách thuộc tính | Chia sẻ dữ liệu liên tổ chức mà không cần giải mã tập trung | P2 |
| 10 | **Microsoft SEAL (BFV)** | Tính toán đồng hình (SUM thống kê) trên dữ liệu mã hoá | Phân tích dữ liệu mà không giải mã bản rõ | P3 |
| 11 | **ML-KEM-768** (FIPS 203) | Đóng gói khoá kháng lượng tử | Bảo vệ dữ liệu lưu trữ dài hạn trước máy tính lượng tử | P4 |
| 12 | **ML-DSA-65** (FIPS 204) | Chữ ký số kháng lượng tử | Toàn vẹn chính sách ABAC và audit log | P4 |
| 13 | **Docker Compose** | Cô lập container giữa Zone Z1 (KMS) và Zone Z2 (DB) | Tách biệt mạng vật lý giữa vùng tin cậy và bán tin cậy | Hạ tầng |

### 2.2 Giải thích chi tiết các kỹ thuật cốt lõi

#### 🔑 Field Envelope Encryption (AES-256-GCM + Vault KMS)

Mỗi trường dữ liệu nhạy cảm (chẩn đoán, thuốc, ghi chú) được mã hoá riêng bằng **Data Encryption Key (DEK)** ngẫu nhiên 256-bit. DEK sau đó được **Vault Transit** bọc (wrap) thành capsule mã hoá và lưu cùng bản ghi DB. Khi cần đọc, ứng dụng xin Vault giải bọc DEK → giải mã trường.

**Tác dụng:** DBA chỉ thấy chuỗi hex/base64. Vault (Z1) không lưu bản rõ; DB (Z2) không lưu DEK rõ.

#### 🏷️ AAD Context Binding

Mỗi lần mã hoá, AAD = `tenant_id || record_id || field_name || schema_version` được đính kèm vào GCM tag. Nếu kẻ tấn công cắt-dán ciphertext từ bản ghi A sang bản ghi B, GCM authentication tag sẽ **fail** → decryption error.

#### 🔍 Blind Index (HKDF + HMAC)

Để tìm kiếm bình đẳng (`WHERE diagnosis = 'E11'`) mà không lộ bản rõ: hệ thống lưu thêm `blind_token = HMAC-SHA256(HKDF(domain_key, tenant, field), plaintext)`. Query so sánh token, không so sánh bản rõ. Kẻ tấn công thấy DB chỉ thấy chuỗi hash.

#### 🛡️ ABAC Policy Engine

Chính sách deny-by-default: một bác sĩ chỉ được phép đọc hồ sơ khi **đồng thời** thoả mãn: (1) Role ∈ {DOCTOR, NURSE}, (2) Dept khớp dept của hồ sơ, (3) Tenant khớp, (4) Trong giờ hành chính (nếu không phải break-glass).

---

## 3. Kiến trúc Phân vùng Tin cậy (Trust Zones)

```
┌─────────────────────────────────────────────────────────┐
│  Zone Z0 – Internet / Client (Không tin cậy)            │
│  [Bác sĩ] [Điều dưỡng] [API Client]                    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS/mTLS
┌──────────────────────▼──────────────────────────────────┐
│  Zone Z1 – Trusted Application Layer (Bệnh viện QL)     │
│  [API Gateway] [ABAC PDP] [Key Broker] [Vault KMS]      │
└──────────┬───────────────────────────┬───────────────────┘
           │ SQL/TLS (chỉ ciphertext)  │ Vault API
┌──────────▼────────────┐   ┌──────────▼───────────────────┐
│  Zone Z2 – Cloud DBMS │   │  Zone Z3 – Audit Log         │
│  PostgreSQL 16         │   │  (Metadata only, Immutable)  │
│  MongoDB 7.0           │   └──────────────────────────────┘
│  (Bán tin cậy)        │
└────────────────────────┘
```

---

## 4. Hai Trạng thái Hệ thống

### 4.1 Trước khi áp dụng kỹ thuật bảo mật (Baseline B0)

Hệ thống EHR cơ bản: dữ liệu lưu **bản rõ** trong DB, không phân tách vùng tin cậy, không kiểm soát truy cập trường dữ liệu.

**Điểm yếu:**
- 🔴 DBA có thể `SELECT *` đọc toàn bộ hồ sơ bệnh nhân
- 🔴 Snapshot/backup ổ đĩa = lộ toàn bộ dữ liệu
- 🔴 Không phân tách tenant → cross-tenant data leak
- 🔴 Không ABAC → mọi role đều đọc được mọi trường
- 🔴 Không có Blind Index → tìm kiếm lộ bản rõ
- 🔴 Không AAD → ciphertext có thể bị hoán đổi

> Xem sơ đồ: **`so_do_he_thong_truoc.drawio`**

### 4.2 Sau khi áp dụng đầy đủ kỹ thuật (Profile P1)

Hệ thống MedShare-Lab hoàn thiện với bảo mật tầng trường dữ liệu, KMS tách biệt, ABAC deny-by-default, Blind Index, và phân vùng mạng.

**Giải pháp:**
- 🟢 AES-256-GCM → DBA chỉ thấy ciphertext
- 🟢 Vault KMS (Z1) → DEK không bao giờ lộ ra DB
- 🟢 ABAC → chỉ đúng role + dept + tenant mới được đọc
- 🟢 Blind Index → tìm kiếm an toàn không lộ bản rõ
- 🟢 AAD Binding → chống hoán đổi ciphertext
- 🟢 Audit Log (Z3) → mọi truy cập đều được ghi lại

> Xem sơ đồ: **`so_do_he_thong_sau.drawio`**

---

## 5. Tài liệu Tham khảo Liên quan

- `MUC_LUC_DU_AN.md` – Mục lục toàn bộ dự án
- `TIEN_DO_HIEN_TAI.md` – Tiến độ triển khai
- `docs/diagrams/` – Sơ đồ hoạt động hệ thống
- `so_do_he_thong_truoc.drawio` – Sơ đồ hệ thống trước bảo mật
- `so_do_he_thong_sau.drawio` – Sơ đồ hệ thống sau bảo mật

---

*Đề tài 18 – NT2205.11.CH | Học kỳ 1 năm học 2025–2026*

