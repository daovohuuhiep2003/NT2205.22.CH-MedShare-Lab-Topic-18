# SỔ TAY VẬN HÀNH DỊCH VỤ & THÔNG SỐ XÁC THỰC
## MedShare-Lab — Topic 18 (NT2205.11.CH)
### Hệ thống Bảo vệ Hồ sơ Y tế Đa Tenant trên Cloud DBMS

Tài liệu này cung cấp toàn bộ thông tin vận hành, thông số kết nối, tài khoản, mật khẩu và quy trình khởi động các dịch vụ hạ tầng (MongoDB, HashiCorp Vault KMS, MinIO S3) và các worker mật mã của dự án.

---

## 1. BẢNG TỔNG HỢP DỊCH VỤ & THÔNG TIN ĐĂNG NHẬP (QUICK REFERENCE)

| Dịch vụ | Tên Container | Cổng (Port) | Tài khoản / Token | Mật khẩu / Khóa bí mật | Vai trò / Miền bảo mật |
|---|---|:---:|---|---|---|
| **MongoDB 7.0** | `medshare-mongo` | `27017` | `medshare_dba` | `dba_secret_dev_pass` | **Zone Z2 (Untrusted):** Lưu trữ Document hồ sơ lâm sàng bán cấu trúc (BSON Envelope) & Index tìm kiếm mù |
| **HashiCorp Vault KMS** | `medshare-vault-kms` | `8200` | Token: `dev-root-token-topic18` | *(Dùng Token)* | **Zone Z1 (Trusted TCB):** Quản trị Master Key, Tenant KEKs, bọc/mở bọc DEK qua Transit Secret Engine |
| **MinIO S3 API** | `medshare-minio` | `9000` | `medshare_admin` | `minio_secret_dev_pass` | **Zone Z2 (Untrusted):** S3 Object Storage API lưu trữ ciphertext tệp nhị phân (DICOM, CT/MRI, X-quang, PDF) |
| **MinIO Web Console** | `medshare-minio` | `9001` | `medshare_admin` | `minio_secret_dev_pass` | Giao diện đồ họa (Web UI) quản lý Buckets và Objects |
| **CP-ABE Worker API** | `medshare-abe-worker` | `9002` | REST API | *(Nội bộ TCB)* | **Zone Z1 (Trusted TCB):** Dịch vụ mã hóa thuộc tính Scheme AC17 (BN254 & SS512), bọc/giải bọc gói chia sẻ Profile P2 |
| **Web Portal (HTTPS / TLS 1.3)** | Host process | `8443` (TLS) / `8000` (HTTP) | Đăng nhập tài khoản Zone Z1 | *(Xem bảng tài khoản bên dưới)* | **Zone Z0 / Z1 Portal:** Cổng thông tin Y tế đa vai trò (Vue 3 SPA + FastAPI), xác thực Argon2id + HS256 JWT + Z1 HMAC, TLS 1.3, ABAC, MinIO, CP-ABE, BFV |

> **Lưu ý bảo mật:** Các thông số xác thực trên được cấu hình mặc định cho môi trường phát triển (Development / Lab Testbench). Hiện mọi kết nối nội bộ Gateway ↔ Vault/MinIO/abe-worker là **HTTP không mã hóa, không xác thực lẫn nhau** (chỉ Portal ↔ trình duyệt dùng TLS 1.3). Đề xuất bổ sung mTLS nằm trong `plan-mTLS.md` (chưa triển khai — xem đánh giá tại `TIEN_DO_HIEN_TAI.md` mục 7).

> **Hai database MongoDB:** Portal/DAL và `scripts/ingest_medical_samples.py` dùng **`medshare_db`** (đổi được qua biến môi trường `DB_NAME`); riêng `datasets/loader.py` ghi bản ghi plaintext baseline B0 (`ehr_records`) vào **`medshare_records`** để tách bạch có chủ đích.

---

## 2. QUY TRÌNH KHỞI ĐỘNG NHANH HẠ TẦNG (QUICK START)

### Bước 0 (chỉ lần đầu): Build image CP-ABE worker
Service `abe-worker` trong compose dùng image cục bộ `medshare-abe-worker:latest` (không có khối `build:`), nên phải build trước, nếu không `docker compose up` sẽ báo không pull được image:
```bash
docker build -t medshare-abe-worker ./workers/abe
```

### Bước 1: Khởi động toàn bộ container qua Docker Compose
```bash
# Di chuyển vào thư mục hạ tầng và khởi động container ngầm
cd infra
docker compose up -d
cd ..
```

### Bước 2: Kiểm tra Vault KMS đã sẵn sàng (tự động)
Vault **không còn chạy dev mode**. Container dùng file storage bền vững (`infra/runtime/vault`) và script [`infra/vault/entrypoint.sh`](infra/vault/entrypoint.sh) tự **init → unseal → tạo token `dev-root-token-topic18` → bật Transit** mỗi lần khởi động. KEK được giữ nguyên qua các lần restart. Chỉ cần kiểm tra:
```bash
docker logs medshare-vault-kms 2>&1 | grep vault-lab      # kỳ vọng: "[vault-lab] Ready ..."
docker exec -e VAULT_TOKEN=dev-root-token-topic18 medshare-vault-kms vault list transit/keys
```
> **Lab only:** unseal key và root token ban đầu lưu tại `infra/runtime/vault/.lab-init` (gitignored, quyền root 600). Xóa thư mục `infra/runtime/vault` = xóa toàn bộ KEK ⇒ mọi capsule cũ không giải mã được nữa.

### Bước 3: Phân quyền thư mục lưu trữ MinIO (tránh lỗi Permission Denied)
```bash
# MinIO chạy dưới user non-root trong container, cần cấp quyền ghi cho thư mục volume host
chmod -R 777 infra/runtime/minio
```

### Bước 4: Kiểm tra trạng thái các container
```bash
docker compose -f infra/docker-compose.yml ps
```
*Các service `medshare-mongo`, `medshare-vault-kms`, `medshare-minio`, `medshare-abe-worker` phải ở trạng thái `Up` (hoặc `healthy`).*
*Healthcheck của Vault chỉ báo `healthy` khi đã unseal và Transit đã mount; MinIO dùng `wget` (BusyBox) gọi `/minio/health/live`.*

### Bước 5: Khởi động Web Portal (Tuần 10 — WP10)

```bash
# Cách 1: Khởi động với mã hóa bảo vệ đường truyền TLS 1.3 (Khuyến nghị cho demo/bảo vệ)
./scripts/run_portal.sh https 8443
# Truy cập: https://127.0.0.1:8443 (Giao thức TLSv1.3, Cipher: TLS_AES_256_GCM_SHA384)

# Cách 2: Khởi động chế độ HTTP thông thường
./scripts/run_portal.sh http 8000
# Truy cập: http://127.0.0.1:8000
```

---

## 3. CHI TIẾT TỪNG DỊCH VỤ & LỆNH TRUY CẬP

### 3.1. MongoDB 7.0 (NoSQL Cloud DBMS — Zone Z2)
* **Loại dữ liệu:** JSON / BSON Documents (Thông tin hành chính, chẩn đoán, toa thuốc được mã hóa cấp trường AES-256-GCM `FieldEnvelope`).
* **Chuỗi kết nối (Connection URI):**
  ```text
  mongodb://medshare_dba:dba_secret_dev_pass@localhost:27017/?authSource=admin
  ```
* **Database:** `medshare_db` (Portal/DAL/ingest — hồ sơ mã hóa, tệp đính kèm, tài khoản Z1 `z1_identity_accounts`, `z1_revoked_tokens`) và `medshare_records` (chỉ bản ghi plaintext baseline B0 `ehr_records` từ `datasets/loader.py`).
* **Các Collections cốt lõi:**
  * `encrypted_patients`: Lưu trữ hồ sơ bệnh nhân mã hóa dạng Field Envelope.
  * `key_capsules`: Lưu trữ các khóa DEK đã bọc (wrapped) bởi Vault KMS.
  * `search_index`: Lưu trữ HMAC token phục vụ tìm kiếm mù (Blind Index).
  * `patient_attachments`: Lưu trữ metadata tệp đính kèm nhị phân trên MinIO.
* **Lệnh kết nối CLI từ Terminal:**
  ```bash
  # Kết nối trực tiếp vào container qua mongosh
  docker exec -it medshare-mongo mongosh -u medshare_dba -p dba_secret_dev_pass --authenticationDatabase admin

  # Hoặc kết nối từ host (nếu máy đã cài mongosh)
  mongosh "mongodb://medshare_dba:dba_secret_dev_pass@localhost:27017/?authSource=admin"
  ```
* **Các lệnh thao tác nhanh trong mongosh:**
  ```javascript
  use medshare_db;          // DB mà Web Portal đang dùng
  show collections;
  db.encrypted_patients.find().limit(2).pretty();
  db.patient_attachments.find().limit(2).pretty();
  ```

---

### 3.2. HashiCorp Vault KMS (Software KMS — Zone Z1)
* **Chế độ chạy:** Server thường với file storage bền vững + auto-unseal lab (không phải `-dev`). Cấu hình: [`infra/vault/config.hcl`](infra/vault/config.hcl).
* **Vai trò:** Quản trị Key Encryption Keys (KEK) theo từng cơ sở y tế (tenant), thực hiện cơ chế Envelope Encryption bọc Data Encryption Keys (DEK) mà không bao giờ để lộ KEK ra ngoài vùng tin cậy.
* **Giao diện Web UI:** [http://localhost:8200](http://localhost:8200)
  * Đăng nhập: Chọn Method **Token**, nhập `dev-root-token-topic18`.
* **API Endpoint:** `http://localhost:8200` (hoặc `http://127.0.0.1:8200`)
* **Kiểm tra trạng thái & danh sách khóa KEK từ CLI:**
  ```bash
  # Kiểm tra trạng thái Vault
  docker exec -e VAULT_TOKEN=dev-root-token-topic18 medshare-vault-kms vault status

  # Liệt kê các Transit KEK hiện có
  docker exec -e VAULT_TOKEN=dev-root-token-topic18 medshare-vault-kms vault list transit/keys
  ```
* **Các KEK chuẩn của hệ thống:**
  * `kek_hospital_a_clinical_v1`: Khóa KEK bọc DEK hồ sơ bệnh án Bệnh viện A.
  * `kek_hospital_a_imaging_v1`: Khóa KEK bọc DEK tệp chẩn đoán hình ảnh Bệnh viện A.
  * `kek_hospital_b_clinical_v1`: Khóa KEK Bệnh viện B.
  * `kek_hospital_b_imaging_v1`: Khóa KEK tệp hình ảnh Bệnh viện B.

---

### 3.3. MinIO S3 Object Storage (Zone Z2)
* **Vai trò:** Lưu trữ tệp nhị phân phi cấu trúc dung lượng lớn (DICOM X-quang, CT, MRI, Siêu âm, PDF) dưới dạng **Ciphertext thuần túy** (`.enc`). MinIO nằm ở Untrusted Cloud, không có quyền truy cập Vault KMS nên không thể giải mã dữ liệu.
* **Giao diện Web Console:** [http://localhost:9001](http://localhost:9001)
  * **Username:** `medshare_admin`
  * **Password:** `minio_secret_dev_pass`
* **S3 API Endpoint:** `http://localhost:9000`
* **Các S3 Buckets chuẩn:**
  * `medshare-hospital-a`: Bucket dành riêng cho Bệnh viện A.
  * `medshare-hospital-b`: Bucket dành riêng cho Bệnh viện B.
* **Định dạng khóa đối tượng (Object Key):**
  ```text
  records/{record_id}/{attachment_id}.enc
  ```
* **Kiểm tra kết nối S3 qua Python SDK:**
  ```bash
  PYTHONPATH=src:. .venv/bin/python -c "
  from minio import Minio
  client = Minio('localhost:9000', access_key='medshare_admin', secret_key='minio_secret_dev_pass', secure=False)
  print('Danh sách Buckets:', [b.name for b in client.list_buckets()])
  "
  ```

---

### 3.4. Các Worker Mật mã Nâng cao (Docker Microservices)

Các worker mật mã chuyên dụng chạy độc lập trong môi trường container để tránh xung đột thư viện:

| Worker | Image Name | Cổng (Port) | Công nghệ & Chuẩn | Lệnh Khởi động & Kiểm tra |
|---|---|:---:|---|---|
| **CP-ABE** | `medshare-abe-worker` | `9002` | Thuật toán AC17 (BN254 & SS512), Stanford PBC 0.5.14, Charm-Crypto, FastAPI | `docker compose -f infra/docker-compose.yml up -d abe-worker`<br>`curl -s http://localhost:9002/health` |
| **PQC** | `medshare-pqc-worker` | *(CLI)* | FIPS 203 (ML-KEM-768), FIPS 204 (ML-DSA-65), liboqs | `docker build -t medshare-pqc-worker ./workers/pqc`<br>`docker run --rm medshare-pqc-worker` |
| **HE (BFV)** | `medshare-he-worker` | *(CLI/Native)* | Microsoft SEAL v4.1.2 BFV Homomorphic Encryption | Smoke test: `docker build -t medshare-he-worker ./workers/he && docker run --rm medshare-he-worker`<br>Engine dùng bởi E7/Portal: binary `workers/he/seal_bfv_engine` |

---

### 3.5. Tài khoản Đăng nhập Web Portal (Zone Z1 Personalized Accounts & 1:1 Database Mapping)

Vai trò của từng bên liên quan được xác định bắt buộc thông qua đăng nhập tài khoản tại **Zone Z1 Identity & Auth Service** ([`src/medshare/auth/service.py`](src/medshare/auth/service.py)). Hệ thống băm mật khẩu bằng **Argon2id**, bảo vệ thuộc tính vai trò trên MongoDB bằng **Zone Z1 HMAC-SHA-256** (`record_mac`) để phát hiện giả mạo DB, và phát hành **RFC 7519 HS256 JWT** qua `Authorization: Bearer <token>`.

#### Quy ước đặt tên tài khoản cá thể hóa (Personalized Username Rule)
Tên tài khoản tuân thủ quy tắc: `<tên><chữ cái đầu họ và đệm><mã/số thứ tự>` (chữ thường, không dấu, viết liền):
- Ví dụ:
  - Bác sĩ **Đào Võ Hữu Hiệp** $\rightarrow$ `hiepdvh01`
  - Bác sĩ **Nguyễn Đạo Ga Đô** $\rightarrow$ `dondg01`
  - Điều dưỡng **Lê Thị Mai** $\rightarrow$ `mailt01`
  - Quản trị viên **Vũ Bảo An** $\rightarrow$ `anvb01`
  - Bệnh nhân **Luong Thanh Hai** (hồ sơ 001) $\rightarrow$ `hailt001`
  - Bệnh nhân **Ly Bao Binh** (hồ sơ 002) $\rightarrow$ `binhlb002`

#### Khớp nối 1:1 giữa Tài khoản Bệnh nhân và Dữ liệu Database
- **Dữ liệu Database:** Nạp toàn bộ **1.000 hồ sơ bệnh nhân** từ dataset chuẩn `datasets/generated/ehr_1000_uniform_seed1801.json` vào MongoDB `medshare_db.encrypted_patients` (`rec-pat-001` $\rightarrow$ `rec-pat-1000`).
- **Tài khoản PATIENT:** Hệ thống tự động cấp phát đúng **1.000 tài khoản bệnh nhân** tương ứng 1:1 (`hailt001` $\rightarrow$ `rec-pat-001`, `binhlb002` $\rightarrow$ `rec-pat-002`, ...). Tỷ lệ khớp nối đạt **100% (1.000 / 1.000, 0 hồ sơ mồ côi)**.
- **Tổng số tài khoản trong hệ thống:** **1.012 tài khoản** (1.000 bệnh nhân + 12 cán bộ y tế, quản trị và người nhà).

#### Bảng tài khoản mẫu các bên liên quan (Core Staff & Sample Patients)

| Username | Mật khẩu mặc định | Vai trò (`role`) | Khoa / Đơn vị | Cá thể & Phạm vi quyền truy cập |
|---|---|---|---|---|
| `anvb01` | `Admin@MedShare2026!` | `ADMIN` | `SECURITY` | **Vũ Bảo An** (Quản trị Z1): cấp phát/thu hồi tài khoản (`TC-07`), xem thống kê map 1:1, kiểm tra Z2 raw-ciphertext. Bị chặn đọc EHR (`TC-27`). |
| `dondg01` | `Staff@MedShare2026!` | `DOCTOR` | `CARDIOLOGY` | **BS. Nguyễn Đạo Ga Đô** (BV A): xem/tạo hồ sơ Tim mạch, xem ảnh DICOM `rec-pat-002`, thực thi CP-ABE & BFV SUM. Bị chặn hồ sơ Ung bướu (`TC-03`). |
| `hiepdvh01` | `Staff@MedShare2026!` | `DOCTOR` | `ONCOLOGY` | **BS. Đào Võ Hữu Hiệp** (BV A): xem/tạo/tìm kiếm hồ sơ Ung bướu BV A. Bị chặn hồ sơ Tim mạch (`TC-03`). |
| `linhnt02` | `Staff@MedShare2026!` | `DOCTOR` | `PEDIATRICS` | **BS. Nguyễn Thùy Linh** (BV A): phụ trách hồ sơ Nhi khoa (`rec-pat-001` Luong Thanh Hai). |
| `khangtv03` | `Staff@MedShare2026!` | `DOCTOR` | `NEUROLOGY` | **BS. Trần Văn Khang** (BV A): phụ trách hồ sơ chuyên khoa Thần kinh. |
| `cuongnv04` | `Staff@MedShare2026!` | `DOCTOR` | `GENERAL` | **BS. Nguyễn Văn Cường** (BV A): phụ trách khám Đa khoa tổng quát. |
| `hunglm05` | `Staff@MedShare2026!` | `DOCTOR` | `CARDIOLOGY` | **BS. Lê Mạnh Hùng** (BV B): phụ trách Tim mạch tại `hospital-b` (kiểm tra phân tách đa cơ sở - Multi-tenant). |
| `thaopt06` | `Staff@MedShare2026!` | `DOCTOR` | `ONCOLOGY` | **BS. Phạm Thu Thảo** (BV B): phụ trách Ung bướu tại `hospital-b`. |
| `mailt01` | `Staff@MedShare2026!` | `NURSE` | `CARDIOLOGY` | **ĐD. Lê Thị Mai** (BV A): xem thông tin hành chính (`name`, `dob`, `gender`); trường `diagnosis` & `notes` tự động che `[REDACTED_BY_POLICY]`. |
| `hailt001` | `Patient@2026!` | `PATIENT` | `PATIENT_PORTAL` | **Luong Thanh Hai**: map 1:1 với hồ sơ `rec-pat-001`. Chỉ xem hồ sơ của mình; bị chặn xem hồ sơ khác (`403`). |
| `binhlb002` | `Patient@2026!` | `PATIENT` | `PATIENT_PORTAL` | **Ly Bao Binh**: map 1:1 với hồ sơ `rec-pat-002` (kèm ảnh DICOM/X-Quang). |
| `ngoclb002` | `Staff@MedShare2026!` | `PATIENT_FAMILY` | `PATIENT_PORTAL` | **Lý Bảo Ngọc**: người nhà/giám hộ bệnh nhân `rec-pat-002` (Ly Bao Binh). |
| `tamtm01` | `Staff@MedShare2026!` | `ANALYST` | `RESEARCH` | **ThS. Trần Minh Tâm**: thực thi tính toán tổng hợp đồng cấu **SEAL BFV SUM** trên 1.000 hồ sơ. Bị chặn xem chi tiết từng ca bệnh. |
| `tuanpm01` | `Staff@MedShare2026!` | `DBA` | `INFRASTRUCTURE` | **Phạm Minh Tuấn**: chỉ xem bản ghi mã hóa Envelope trên Zone Z2 (`/api/v1/dba/raw-records`). Bị chặn đọc bản rõ lâm sàng (`TC-27`). |
| `...` *(998 tài khoản khác)* | `Patient@2026!` | `PATIENT` | `PATIENT_PORTAL` | **998 bệnh nhân còn lại** (`rec-pat-003` $\rightarrow$ `rec-pat-1000`): nạp từ 1.000 hồ sơ EHR. Mỗi bệnh nhân sở hữu 1 tài khoản cá thể hóa tương ứng. |

> **Quản lý & Cấp thêm tài khoản:** Đăng nhập bằng `anvb01` $\rightarrow$ chọn tab **Cấp Tài khoản (`Admin Z1`)** để xem thẻ thống kê map 1:1, lọc theo vai trò, tìm kiếm theo tên/username/mã hồ sơ, phân trang 25 bản ghi/trang, hoặc cấp phát tài khoản mới/thu hồi tức thời (`TC-07`). Người dùng đã đăng nhập có thể tự đổi mật khẩu tại nút **Đổi mật khẩu** trên thanh điều hướng (tự động nâng `attr_epoch` và vô hiệu hóa token cũ).

---

### 3.6. Giao diện Bệnh án Điện tử (EHR) & Hệ thống PACS Chuẩn Bệnh viện

Web Portal được chuẩn hóa theo mô hình hệ thống Bệnh án Điện tử (EMR/EHR) và Hệ thống Lưu trữ & Truyền hình ảnh Y tế (PACS) thực tế của các bệnh viện đa khoa hạng 1:

1. **Hỗ trợ Giao diện Sáng (Light Mode) và Tối (Dark Mode):**
   * **Chế độ Sáng (☀️ Mặc định):** Thiết kế theo màu nhận diện y tế chuẩn (Slate `#f8fafc` + Teal `#0d9488` + Border `#e2e8f0`), tối ưu hóa độ tương phản cho bàn làm việc lâm sàng, phòng khám ngoại trú và khu hành chính bệnh viện vào ban ngày.
   * **Chế độ Tối (🌙 Chuyên dụng):** Nền tối sâu Slate-950/900 giúp giảm mỏi mắt cho bác sĩ trực ca đêm và bác sĩ chẩn đoán hình ảnh khi đọc phim X-Quang/CT/MRI trong phòng tối PACS.
   * **Nút chuyển đổi Theme:** Bố trí trực quan tại góc phải màn hình Đăng nhập và trên thanh điều hướng (Navbar) chính, lưu trữ lựa chọn người dùng vào `localStorage`.

2. **Tờ Bệnh án Điện tử Lâm sàng Chuẩn Bộ Y tế (Hospital Chart Modal):**
   * Bấm nút **"Bệnh án EHR"** tại bất kỳ dòng bệnh nhân nào trên tab Sổ Bệnh Án.
   * Bố cục đầy đủ 5 phần chuyên môn:
     * **Phần 1: Hành chính bệnh nhân:** Họ tên, Mã hồ sơ, Giới tính, Tuổi, Ngày sinh, Số thẻ BHYT, Địa chỉ thường trú, Ngày nhập viện, Bác sĩ điều trị.
     * **Phần 2: Bảng Chỉ số sinh tồn (Vital Signs 6 thông số):** Mạch (lần/phút), Huyết áp tâm thu/tâm trương (mmHg), Thân nhiệt (°C), Nhịp thở (lần/phút), Nồng độ Oxy SpO2 (%), Chiều cao / Cân nặng / Chỉ số khối BMI.
     * **Phần 3: Khám lâm sàng & Chẩn đoán ICD-10:** Triệu chứng lúc vào viện, Tiền sử bệnh, Diễn biến bệnh hàng ngày, Mã chẩn đoán ICD-10 chính & bệnh kèm theo.
     * **Phần 4: PACS Chẩn đoán hình ảnh & Xét nghiệm PDF:** Xem trực tiếp ảnh phim X-Quang / CT / MRI và tệp PDF phiếu kết quả xét nghiệm được gắn liền với hồ sơ bệnh án.
     * **Phần 5: Kế hoạch điều trị, Toa thuốc & Chữ ký số:** Hướng xử trí, chế độ dinh dưỡng, điều dưỡng chăm sóc cấp 1/2/3 và con dấu xác thực điện tử của Bác sĩ điều trị.
   * **In Bệnh án (`window.print()`):** Hỗ trợ nút **"In Bệnh án"** để xuất bản in sạch đẹp, ẩn toàn bộ thanh điều hướng và nút bấm (class `no-print`), định dạng chuẩn khổ giấy A4 y tế.

3. **Trình hiển thị Tệp Y tế Trực tiếp (Medical Viewers):**
   * **Medical Image Viewer (X-Quang, CT, MRI, Siêu âm):** Tải và giải mã trực tiếp từ MinIO qua Gateway API, hỗ trợ thanh công cụ chuyên dụng: Phóng to (Zoom In), Thu nhỏ (Zoom Out), Xoay ảnh 90° (Rotate), Đảo ngược màu phim / Âm bản (Negative / Invert Mode), Toàn màn hình (Fullscreen) và Tải về (Download).
   * **Embedded PDF Report Viewer (Phiếu xét nghiệm, Báo cáo giải phẫu bệnh):** Nhúng trực tiếp tài liệu PDF vào giao diện web qua `<iframe>` chuẩn W3C, hỗ trợ cuộn xem đa trang, mở trong tab trình duyệt mới và tải tệp bản rõ.

---

## 4. LỆNH VẬN HÀNH & KIỂM THỬ THƯỜNG DÙNG

### 4.1. Khởi động và Dừng dịch vụ
```bash
# Khởi động dịch vụ nền
cd infra && docker compose up -d && cd ..

# Xem nhật ký (logs) thời gian thực
docker compose -f infra/docker-compose.yml logs -f

# Dừng toàn bộ dịch vụ (dữ liệu volume runtime được giữ nguyên)
cd infra && docker compose down && cd ..

# Dừng và xóa sạch toàn bộ volume (Reset database)
cd infra && docker compose down -v && cd ..
```

### 4.2. Nạp dữ liệu vào hệ thống
```bash
# 1. Nạp dữ liệu hồ sơ lâm sàng cơ sở (1.000 bản ghi mẫu) vào MongoDB
PYTHONPATH=src:. .venv/bin/python datasets/loader.py --file datasets/generated/ehr_1000_uniform_seed1801.json --reset

# 2. Mã hóa phân đoạn AES-GCM và nạp 15 tệp y tế mẫu thực tế (~102.8 MB) vào MinIO + MongoDB
PYTHONPATH=src:. .venv/bin/python scripts/ingest_medical_samples.py
```

### 4.3. Chạy các thí nghiệm đo lường (Benchmarks)
```bash
# Thí nghiệm E1: Đo Baseline B0 vs B1 (Throughput & Latency)
PYTHONPATH=src:. .venv/bin/python benchmarks/run_e1_baseline.py

# Thí nghiệm E2: Chi phí mã hóa Envelope từng trường
PYTHONPATH=src:. .venv/bin/python benchmarks/run_e2_field_overhead.py

# Thí nghiệm E3: Đo lường và chặn đứng DBA Bypass (ABAC Policy Enforcement)
PYTHONPATH=src:. .venv/bin/python benchmarks/run_e3_abac_bypass.py

# Thí nghiệm E4: Chia sẻ CP-ABE AC17 (cần abe-worker :9002 đang chạy)
PYTHONPATH=src:. .venv/bin/python benchmarks/run_e4_cpabe_sharing.py

# Thí nghiệm E5: Phân tích rò rỉ tần suất mẫu truy vấn Blind Index
PYTHONPATH=src:. .venv/bin/python benchmarks/run_e5_leakage_analysis.py

# Thí nghiệm E7: Tổng đồng cấu SEAL BFV SUM
PYTHONPATH=src:. .venv/bin/python benchmarks/run_e7_homomorphic_sum.py
```

### 4.4. Kiểm thử chất lượng (Test Suite)
```bash
# Chạy bộ test chuyên biệt cho MinIO S3 & Medical Attachments (6 tests)
PYTHONPATH=src:. .venv/bin/python -m pytest tests/security/test_minio_attachments.py -v

# Chạy toàn bộ 100 bài test kiểm thử tự động của dự án
# (Yêu cầu Mongo + Vault đã mount Transit + MinIO + abe-worker. Kết quả 23/11/2026: 100 passed)
PYTHONPATH=src:. .venv/bin/python -m pytest tests/

# Chạy công cụ đối soát tính nhất quán tài liệu & cấu trúc repository (16 checks)
python3 -B scripts/check_repo.py
```

---

## 5. XỬ LÝ SỰ CỐ THƯỜNG GẶP (TROUBLESHOOTING)

### Sự cố 1: Lỗi Vault `no handler for route "transit/keys/..."` hoặc Vault `sealed`
* **Bối cảnh:** Lỗi này xảy ra thường xuyên khi Vault còn chạy dev mode (in-memory). **Đã khắc phục từ 23/11/2026** bằng file storage + `infra/vault/entrypoint.sh`; nếu vẫn gặp, nguyên nhân thường là container đang chạy bản cấu hình cũ hoặc script bootstrap lỗi.
* **Dấu hiệu:** `pytest tests/` dừng ở collection `tests/unit/test_portal_api.py` với `KmsError: Failed to create Vault key ...`.
* **Cách khắc phục:**
  ```bash
  docker logs medshare-vault-kms 2>&1 | grep vault-lab          # xem bước bootstrap nào lỗi
  docker rm -f medshare-vault-kms && docker compose -f infra/docker-compose.yml up -d vault-kms
  ```
* **Lưu ý:** nếu `infra/runtime/vault` bị xóa, Vault khởi tạo lại từ đầu với KEK mới; Portal tự seed lại 1.000 hồ sơ khi khởi động, còn tệp mẫu cần chạy lại `scripts/ingest_medical_samples.py`.

### Sự cố 2: Lỗi MinIO `FATAL Unable to initialize backend: file access denied`
* **Nguyên nhân:** Thư mục `infra/runtime/minio` tạo bởi user root nhưng tiến trình MinIO trong container chạy dưới user UID 10001.
* **Cách khắc phục:**
  ```bash
  sudo chmod -R 777 infra/runtime/minio
  docker restart medshare-minio
  ```

### Sự cố 3: Lỗi `ServerSelectionTimeoutError: localhost:27017` khi chạy test
* **Nguyên nhân:** Container MongoDB chưa bật hoặc môi trường sandbox chặn kết nối localhost.
* **Cách khắc phục:**
  * Kiểm tra `docker ps` xem `medshare-mongo` có đang chạy hay không.
  * Nếu chạy test trong môi trường cách ly (sandbox), đảm bảo lệnh test có quyền truy cập mạng cục bộ.

### Sự cố 4: Lỗi `ModuleNotFoundError: No module named 'medshare'`
* **Nguyên nhân:** Thiếu biến môi trường `PYTHONPATH` trỏ tới thư mục mã nguồn `src`.
* **Cách khắc phục:**
  Luôn thêm tiền tố `PYTHONPATH=src:.` trước lệnh python, ví dụ:
  ```bash
  PYTHONPATH=src:. .venv/bin/python -m pytest tests/
  ```

### Sự cố 5: `medshare-minio` ở trạng thái `(unhealthy)` — đã khắc phục
* **Nguyên nhân cũ:** Healthcheck gọi `curl`, nhưng image `minio/minio` không có `curl`.
* **Đã sửa:** healthcheck dùng BusyBox `wget -q --spider http://127.0.0.1:9000/minio/health/live`. Nếu vẫn `unhealthy`, container đang chạy cấu hình cũ: `docker compose -f infra/docker-compose.yml up -d minio-cloud` để tạo lại.

### Sự cố 6: `docker compose up` báo không pull được `medshare-abe-worker:latest`
* **Nguyên nhân:** Image này chỉ tồn tại cục bộ.
* **Cách khắc phục:** `docker build -t medshare-abe-worker ./workers/abe` rồi chạy lại compose.

### Sự cố 7: Portal không hiển thị 15 tệp mẫu đã ingest — đã khắc phục
* **Nguyên nhân cũ:** script ingest ghi metadata vào DB `medshare_records`, còn Portal đọc `medshare_db`.
* **Đã sửa:** script dùng `DB_NAME` (mặc định `medshare_db`). Nếu dữ liệu được ingest trước 23/11/2026, chạy lại `PYTHONPATH=src:. .venv/bin/python scripts/ingest_medical_samples.py`.
