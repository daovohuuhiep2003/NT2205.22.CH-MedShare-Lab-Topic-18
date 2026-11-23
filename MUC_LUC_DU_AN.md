# MỤC LỤC VÀ HƯỚNG DẪN CẤU TRÚC DỰ ÁN (PROJECT DIRECTORY MAP)
## Đề tài: MedShare-Lab — Topic 18 (NT2205.11.CH)
### Bảo vệ hồ sơ y tế đa tenant trên Cloud DBMS: kiến trúc phân lớp, kiểm soát truy cập và bằng chứng an toàn

* **Môn học:** Mật mã học và ứng dụng (NT2205.11.CH) — Chương trình Thạc sĩ An toàn thông tin, Trường Đại học Công nghệ Thông tin (ĐHQG-HCM).
* **Mục đích tài liệu:** Cung cấp bản đồ điều hướng chi tiết toàn bộ repository, giải thích ý nghĩa, chức năng và vai trò của từng thư mục, từng tệp tin trong đề tài.

---

## 1. SƠ ĐỒ CÂY THƯ MỤC TỔNG QUAN (REPOSITORY TREE OVERVIEW)

```text
NT2205.11.CH_Project/
├── .github/                      # GitHub Actions CI (ci.yml chạy scripts/check_repo.py) & PR template
├── analysis/                     # Phân tích số liệu thống kê CI 95% & Đồ thị rò rỉ
│   └── output/                   # Nơi xuất biểu đồ và báo cáo phân tích (gitignored)
├── benchmarks/                   # Harness đo lường hiệu năng & thực nghiệm
│   ├── results/                  # Báo cáo JSON E1, E2, E3, E4, E5, E7 (gitignored)
│   ├── run_e1_baseline.py        # E1: Baseline B0 vs B1 (LUKS)
│   ├── run_e2_field_overhead.py  # E2: Overhead mã hóa tầng trường + Vault KMS
│   ├── run_e3_abac_bypass.py     # E3: ABAC, Break-glass, DBA bypass
│   ├── run_e4_cpabe_sharing.py   # E4: CP-ABE AC17 sharing (BN254 & SS512)
│   ├── run_e5_leakage_analysis.py # E5: Blind Index & tấn công suy luận tần suất
│   └── run_e7_homomorphic_sum.py # E7: SEAL BFV SUM
├── datasets/                     # Bộ sinh dữ liệu y tế tổng hợp & bộ nạp DB (WP2)
│   ├── generated/                # Tập dữ liệu synthetic 1k, 10k bản ghi (gitignored)
│   ├── oracle/                   # Plaintext Ground Truth Oracle (gitignored)
│   ├── samples/raw/              # 15 tệp y tế mẫu (xray, ultrasound, ct_mri, reports) + manifest.json
│   ├── generate_datasets.py      # Script sinh dữ liệu (5 seeds, uniform & skewed)
│   └── loader.py                 # Nạp dữ liệu baseline B0 vào MongoDB 7.0 (DB medshare_records)
├── docs/                         # Tài liệu khoa học, kiến trúc, thiết kế, quy trình
│   ├── adr/                      # Architecture Decision Records
│   ├── design/                   # Đặc tả mật mã, format bản mã, đánh giá mã nguồn CP-ABE
│   ├── development/              # Thiết lập môi trường, quy ước Git và layout
│   ├── diagrams/                 # Sơ đồ Mermaid (.mmd), PNG và Draw.io
│   ├── maintenance/              # validation.md — trạng thái kiểm chứng tài liệu
│   ├── planning/                 # Kế hoạch 12 tuần, step-by-step, RACI
│   ├── proposal/                 # Đề cương (Markdown chuẩn & DOCX đồng bộ)
│   ├── requirements/             # Đề bài Topic 18, Course Guideline, Rubric
│   └── testing/                  # Đặc tả thí nghiệm E1–E9, 30 TC, ma trận truy vết
├── evidence/runs/                # Bằng chứng E1, E2, E3, E4, E5, E7 (*.md)
├── frontend/                     # Web Portal Vue 3 + Vite + TailwindCSS (WP10)
│   ├── src/App.vue, main.js      # Khung SPA
│   ├── src/components/           # 8 component: LoginView, Navbar, PatientsTab, AccountsTab,
│   │                             #   AttachmentsTab, CryptoTab, DbaAuditTab, AuditLogTab
│   └── dist/                     # Bản build `npm run build`, được FastAPI phục vụ tại "/"
├── infra/                        # Hạ tầng Lab
│   ├── certs/                    # server.crt / server.key tự ký cho Portal TLS 1.3 (*.key gitignored)
│   ├── runtime/                  # Volume cục bộ MongoDB, MinIO & Vault (gitignored)
│   ├── vault/                    # config.hcl + entrypoint.sh: Vault bền vững, tự unseal & bật Transit
│   └── docker-compose.yml        # 4 service: mongo-cloud, vault-kms, minio-cloud, abe-worker
├── scratch/                      # Bản nháp script sinh Draw.io (không thuộc sản phẩm chính)
├── scripts/                      # Công cụ tự động hóa
│   ├── check_repo.py             # Đối soát toàn diện repository (16 checks)
│   ├── gen_proposal_pptx.py      # Sinh slide PROPOSAL_MedShare_Lab.pptx
│   ├── ingest_medical_samples.py # Mã hóa chunked AES-GCM & nạp 15 tệp mẫu vào MinIO + DB medshare_db
│   ├── prepare_medical_samples.py # Chuẩn bị bộ tệp mẫu + manifest.json
│   ├── render_proposal.py        # Proposal Markdown → DOCX
│   ├── run_portal.sh             # Chạy Web Portal (http 8000 / https TLS 1.3 8443)
│   ├── setup_ubuntu.sh           # Thiết lập môi trường Ubuntu từ A–Z
│   ├── validate_docs.py          # Kiểm tra liên kết Markdown & Mermaid
│   └── validate_proposal_sync.py # Kiểm tra đồng bộ Markdown ↔ DOCX
├── src/medshare/                 # Mã nguồn Python Core (chạy trên host, .venv)
│   ├── auth/service.py           # Zone Z1 IdP: Argon2id, HS256 JWT, HMAC record_mac (WP10)
│   ├── broker/                   # KeyBroker, KeyCapsule, Vault KMS client (WP4)
│   ├── crypto/                   # Field envelope AES-GCM, blind index, file cipher, ABE/HE clients
│   ├── gateway/                  # service.py (Dual PEP) + api.py (FastAPI REST cho Portal)
│   ├── policy/abac.py            # ABAC PDP Deny-by-default, Break-glass (WP5)
│   └── storage/                  # dal.py (MongoStorage), minio_dal.py, schema.py
├── tests/                        # 100 test tự động (unit, security, tooling)
├── workers/                      # Worker mật mã chạy container cô lập
│   ├── abe/                      # CP-ABE AC17 — FastAPI :9002 (engine, service, cli)
│   ├── he/                       # SEAL v4.1.2 BFV — binary seal_bfv_engine (CLI)
│   └── pqc/                      # liboqs ML-KEM-768 / ML-DSA-65 — smoke test CLI
├── BAO_CAO_SO_LUOC.md            # Báo cáo sơ lược đề tài
├── CONTRIBUTING.md               # Quy định đóng góp mã nguồn
├── HUONG_DAN_DICH_VU.md          # Sổ tay vận hành dịch vụ, tài khoản, troubleshooting
├── MUC_LUC_DU_AN.md              # [FILE HIỆN TẠI] Mục lục repository
├── PROPOSAL_MedShare_Lab.pptx    # Slide đề cương (sinh bởi scripts/gen_proposal_pptx.py)
├── README.md                     # Giới thiệu tổng quan
├── SCRIPT_THUYET_TRINH.md        # Kịch bản thuyết trình proposal 20–25 phút
├── SECURITY.md                   # Chính sách an toàn, cấm commit secret
├── TIEN_DO_HIEN_TAI.md           # Báo cáo tiến độ & nhật ký lệnh
├── generate_drawio.py            # Sinh sơ đồ Draw.io hệ thống
├── plan-mTLS.md                  # [ĐỀ XUẤT] Kế hoạch mTLS + SPIFFE + PQC PKI (xem đánh giá ở TIEN_DO_HIEN_TAI.md §7)
├── so_do_he_thong_truoc.drawio / so_do_he_thong_sau.drawio # Sơ đồ hệ thống trước/sau khi áp dụng bảo vệ
├── so_do_hoat_dong_he_thong.drawio # Sơ đồ hoạt động toàn diện (Draw.io)
└── srcFile.md                    # Danh mục nguồn dataset ảnh y khoa công khai
```

---

## 2. CHI TIẾT TỪNG THƯ MỤC VÀ TẬP TIN

### 2.1. Thư mục gốc (Root Files)
* [**`so_do_hoat_dong_he_thong.drawio`**](so_do_hoat_dong_he_thong.drawio): Sơ đồ hoạt động và kiến trúc toàn diện của hệ thống MedShare-Lab theo định dạng XML Draw.io (`.drawio`). Thể hiện 4 vùng tin cậy Z0 $\to$ Z3, các thành phần xử lý (Gateway, Broker, Vault KMS, Cloud DB, Workers) và 4 nhóm luồng hoạt động chính: Luồng Ghi hồ sơ (W1 $\to$ W7), Luồng Đọc/Tra cứu bảo mật (R1 $\to$ R8), Luồng Chia sẻ liên viện CP-ABE (P2) & Tính toán đồng cấu BFV (P3), và Mô hình kiểm chứng đối kháng an toàn (TC-02, TC-05, TC-08). Có thể mở trực tiếp bằng Draw.io Desktop hoặc tiện ích mở rộng Diagrams.net trên VS Code.
* [**`README.md`**](README.md): Điểm khởi đầu của dự án. Trình bày tổng quan Topic 18, mục tiêu nghiên cứu, ranh giới phạm vi đề tài, cấu trúc nguồn chuẩn và hướng dẫn kiểm tra nhanh repository.
* [**`TIEN_DO_HIEN_TAI.md`**](TIEN_DO_HIEN_TAI.md): Báo cáo tiến độ kỹ thuật chi tiết nhất. Ghi lại kết quả từng cột mốc, bảng số liệu hiệu năng thực nghiệm E1, giải thích các sự cố kỹ thuật và giải pháp, toàn bộ Command Runbook từ lúc cài đặt đến nay.
* [**`MUC_LUC_DU_AN.md`**](MUC_LUC_DU_AN.md): Tập tin mục lục điều hướng, phân tích ý nghĩa và vai trò của từng folder/file trong repository.
* [**`CONTRIBUTING.md`**](CONTRIBUTING.md): Hướng dẫn dành cho hai học viên tham gia phát triển: Quy ước đặt tên nhánh Git, thông điệp commit, tiêu chuẩn code style (PEP 8), định dạng tài liệu và quy trình tạo Pull Request.
* [**`SECURITY.md`**](SECURITY.md): Quy định bảo mật nghiêm ngặt của đồ án: Tuyệt đối cấm commit credentials, khóa private, secret tokens, mật khẩu DB, dữ liệu bệnh nhân thật; quy tắc kiểm toán mã nguồn trước khi push.
* [**`HUONG_DAN_DICH_VU.md`**](HUONG_DAN_DICH_VU.md): Sổ tay vận hành: cổng, tài khoản dev, Quick Start, lệnh nạp dữ liệu/benchmark/test, xử lý sự cố.
* [**`BAO_CAO_SO_LUOC.md`**](BAO_CAO_SO_LUOC.md), [**`SCRIPT_THUYET_TRINH.md`**](SCRIPT_THUYET_TRINH.md), **`PROPOSAL_MedShare_Lab.pptx`**: Bộ tài liệu trình bày đề cương (báo cáo sơ lược, kịch bản nói, slide).
* [**`plan-mTLS.md`**](plan-mTLS.md): Bản đề xuất kênh truyền nội bộ mTLS + SPIFFE + PKI ML-DSA. **Chưa triển khai**; đánh giá khả thi và phạm vi rút gọn tại `TIEN_DO_HIEN_TAI.md` mục 7.
* [**`srcFile.md`**](srcFile.md): Danh mục nguồn dataset ảnh y khoa công khai (X-quang, CT/MRI, siêu âm) dùng làm tệp mẫu.
* **`generate_drawio.py`**, **`so_do_he_thong_truoc.drawio`**, **`so_do_he_thong_sau.drawio`**: Script sinh sơ đồ và hai sơ đồ so sánh hệ thống trước/sau khi áp dụng các lớp bảo vệ.
* **`.gitignore`**: Danh sách loại trừ các tệp nhạy cảm hoặc tệp sinh tự động: Môi trường ảo `.venv/`, dữ liệu database runtime `infra/runtime/`, dataset đã sinh `datasets/generated/`, file oracle `datasets/oracle/`, báo cáo kết quả `benchmarks/results/` và chứng tích `evidence/runs/`.
* **`.gitattributes`** & **`.editorconfig`**: Chuẩn hóa mã hóa ký tự UTF-8, quy chuẩn xuống dòng LF trên Linux để chống lỗi xung đột giữa các máy trạm.

---

### 2.2. Thư mục Tài liệu Nghiên cứu & Thiết kế (`docs/`)
Thư mục chứa toàn bộ tri thức khoa học, cơ sở lý luận và đặc tả kỹ thuật của đề tài:

#### A. Yêu cầu & Phân tích Đề tài (`docs/requirements/`)
* [`course-guideline.md`](docs/requirements/course-guideline.md): Hướng dẫn đồ án môn học Mật mã học và ứng dụng (NT2205.11.CH).
* [`topic-18.md`](docs/requirements/topic-18.md): Đề bài chi tiết Topic 18: Bảo vệ cơ sở dữ liệu y tế đa tenant trên Cloud DBMS.
* [`source-analysis.md`](docs/requirements/source-analysis.md): Bản phân tích chuyên sâu đối chiếu chuẩn đầu ra Thạc sĩ, ma trận Rubric đánh giá điểm xuất sắc và danh mục tài liệu tham khảo chính.

#### B. Đề cương Đăng ký Đề tài (`docs/proposal/`)
* [`project-proposal.md`](docs/proposal/project-proposal.md): **Văn bản nguồn chuẩn (Single Source of Truth)** của đề cương đồ án. Mọi thay đổi về nội dung đề tài bắt buộc phải sửa tại đây trước tiên.
* [`project-proposal.docx`](docs/proposal/project-proposal.docx): Bản Word đồng bộ 100% nội dung với file Markdown trên, được sinh tự động bằng script `render_proposal.py`.

#### C. Kế hoạch & Phân công Công việc (`docs/planning/`)
* [`implementation-plan.md`](docs/planning/implementation-plan.md): Kế hoạch triển khai chi tiết 12 tuần (Giai đoạn 1 đến Giai đoạn 4), các yêu cầu an toàn SR-01 $\to$ SR-18, yêu cầu mật mã CR-01 $\to$ CR-12.
* [`step-by-step-plan.md`](docs/planning/step-by-step-plan.md): Lộ trình từng bước chi tiết (Step-by-Step), ma trận trách nhiệm RACI giữa Thành viên A (Nguyễn Đạo Ga Đô) và Thành viên B (Đào Võ Hữu Hiệp), tiêu chí nghiệm thu từng cổng (Gate Tuần 2, 6, 10, 12).
* [`team-work-plan.docx`](docs/planning/team-work-plan.docx): File kế hoạch phối hợp nhóm nộp cho giảng viên.

#### D. Thiết kế Mật mã & Giao thức (`docs/design/`)
* [`crypto-and-protocol-design.md`](docs/design/crypto-and-protocol-design.md): Trái tim kỹ thuật của đề tài. Đặc tả chi tiết các primitive mật mã (M-01 $\to$ M-12), cấu trúc phân cấp khóa (Key Hierarchy), cấu trúc Envelope và Capsule, công thức tính AAD, quy trình Write/Read của Profile P1, cơ chế chống tấn công tráo đổi ngữ cảnh.
* [`cpabe-source-evaluation.md`](docs/design/cpabe-source-evaluation.md): Báo cáo đánh giá và tái sử dụng mã nguồn CP-ABE từ công trình nghiên cứu trước đây của tác giả Đào Võ Hữu Hiệp (`daovohuuhiep2003/Project-MMH-CP-ABE`).

#### E. Sơ đồ Kiến trúc & Luồng Dữ liệu (`docs/diagrams/`)
Chứa toàn bộ mã nguồn Mermaid (.mmd) và sơ đồ trực quan định dạng Draw.io (.drawio):
* [**`medshare_system_activity_flow.drawio`**](docs/diagrams/medshare_system_activity_flow.drawio): Bản vẽ sơ đồ tương tác & luồng dữ liệu toàn diện của hệ thống MedShare-Lab theo chuẩn Draw.io (định dạng XML diagrams.net). Bao quát cấu trúc 4 Trust Zones (Z0 $\to$ Z3), các cổng giao tiếp F0 $\to$ F9, phân vùng DBMS & KMS, và các luồng nghiệp vụ tương tác.
* `architecture.mmd`: Sơ đồ kiến trúc 4 vùng tin cậy (Zone Z0 $\to$ Z3).
* `data-flows.mmd`: Sơ đồ 10 luồng dữ liệu nghiệp vụ (F0 Provisioning $\to$ F9 Audit).
* `key-hierarchy.mmd`: Phân cấp khóa từ KMS Root, KEK, DEK đến ABE/PQC keys.
* `read-sequence.mmd`: Thứ tự xác thực, kiểm tra ABAC, cấp khóa và giải mã tại Gateway.
* `rotation-state.mmd`: Máy trạng thái xoay vòng khóa không gián đoạn (Key Lifecycle Rotation).
* `proposal-overview.mmd` & `proposal-profiles.mmd`: Sơ đồ tóm tắt đề cương và các profile bảo vệ.

#### F. Thử nghiệm, Đánh giá & Truy vết (`docs/testing/`)
* [`experiments-and-validation.md`](docs/testing/experiments-and-validation.md): Thiết kế chi tiết 8 thí nghiệm khoa học (E1, E2, E3, E4, E5, E7, E8, E9), 30 nhóm Test Cases (TC-01 $\to$ TC-30), phương pháp đo đạc hiệu năng, độ trễ và phân tích rò rỉ.
* [`traceability-matrix.md`](docs/testing/traceability-matrix.md): Ma trận truy vết khoa học liên kết chặt chẽ:
  $$\text{Threat (T)} \longrightarrow \text{Security Requirement (SR)} \longrightarrow \text{Crypto Requirement (CR)} \longrightarrow \text{Mechanism (M)} \longrightarrow \text{Module} \longrightarrow \text{Test Case (TC)} \longrightarrow \text{Evidence}$$

#### G. Hướng dẫn Phát triển & Quyết định Kiến trúc (`docs/development/`, `docs/adr/`, `docs/maintenance/`)
* `environment-setup.md`: Nguyên tắc cô lập môi trường Host vs Docker Containers.
* `git-workflow.md`: Hướng dẫn luồng làm việc với Git, push remote và code review.
* `repository-layout.md`: Định nghĩa trách nhiệm từng package.
* `adr/README.md`: Nơi lưu các Architecture Decision Records.
* `validation.md`: Trạng thái kiểm chứng tài liệu và các giới hạn phạm vi đề tài.

---

### 2.3. Thư mục Mã nguồn Ứng dụng Lõi (`src/medshare/`)
Chứa khung mã nguồn Python Core (chạy trong môi trường ảo `.venv` trên host):

#### A. Phân hệ Mật mã Tầng trường ([`src/medshare/crypto/`](src/medshare/crypto/)) — [ĐÃ HOÀN THÀNH WP3]
* [`errors.py`](src/medshare/crypto/errors.py): Định nghĩa các lớp ngoại lệ bảo mật fail-closed:
  * `CryptoError`: Lớp cơ sở.
  * `InvalidKeyError`: Lỗi khóa DEK/KEK không đúng 32 bytes (256 bits).
  * `EnvelopeValidationError`: Lỗi envelope sai định dạng, version không hỗ trợ hoặc vượt bounds 10 MB.
  * `ContextMismatchError`: Phát hiện tấn công tráo đổi ngữ cảnh (Context Splicing/Swapping).
  * `DecryptionIntegrityError`: Phát hiện can thiệp bit trên bản mã hoặc authentication tag.
* [`context.py`](src/medshare/crypto/context.py): Lớp dữ liệu `CryptoContext` lưu giữ 10 trường ngữ cảnh bất biến: `domain`, `format_version`, `data_suite_id`, `tenant_id`, `object_kind`, `record_id`, `field_id`, `data_version`, `data_policy_version`, `dek_id`. Phương thức `compute_canonical_aad()` sinh mảng byte AAD chuẩn hóa theo RFC 8785 (JCS).
* [`envelope.py`](src/medshare/crypto/envelope.py): Lớp dữ liệu `FieldEnvelope` đóng gói bản mã có cấu trúc gồm Header + Payload nhị phân (`nonce` 12 bytes, `ciphertext` $N$ bytes, `tag` 16 bytes). Hỗ trợ tuần tự hóa qua lại JSON và Base64 có kiểm tra giới hạn an toàn.
* [`engine.py`](src/medshare/crypto/engine.py): Lõi `FieldCipherEngine`:
  * `encrypt_field()`: Sử dụng thuật toán chuẩn `AES-256-GCM`, tự động sinh fresh nonce 12-byte qua CSPRNG cho mỗi trường, gắn kết AAD bất biến.
  * `decrypt_field()`: Bắt buộc đối soát nghiêm ngặt với `expected_context` được cấp từ Zone Z1 TCB trước khi giải mã. Tuyệt đối không bao giờ trả về bất kỳ phần plaintext nào khi xảy ra lỗi.
* [`blind_index.py`](src/medshare/crypto/blind_index.py): Lõi `Equality Blind Index Engine` (WP6 — Tuần 7):
  * `compute_blind_index()`: Tính toán HMAC-SHA-256 token trên canonical tuple JCS RFC 8785 (`domain = medshare/search/v1`).
  * `derive_search_key()`: Dẫn xuất search key phân tách độc lập theo từng bệnh viện (`tenant_id`), từng trường (`field_name`), và từng epoch qua HKDF-SHA256 (M-06 / CR-07).
  * `normalize_field_value()`: Chuẩn hóa Unicode NFC, loại bỏ khoảng trắng, chuẩn hóa chữ hoa/chữ thường.
  * `validate_equality_query()`: Bộ lọc truy vấn từ chối các toán tử range (`>`, `<`, `between`), wildcard (`%`, `*`), regex với mã lỗi HTTP 422 (`UnsupportedQueryError`).
* [`file_cipher.py`](src/medshare/crypto/file_cipher.py): `MedicalFileCipher` — mã hóa chunked AES-256-GCM (khối 4 MB, AAD gắn `tenant/patient/file/chunk_index`) cho tệp DICOM/ảnh/PDF lưu MinIO.
* [`he_client.py`](src/medshare/crypto/he_client.py): `HeBfvClient` — adapter gọi binary SEAL BFV, kèm Differencing Attack Guard (TC-30).
* [`abe_client.py`](src/medshare/crypto/abe_client.py): `AbeClient` — adapter REST/CLI tới CP-ABE worker `:9002`.
* [`__init__.py`](src/medshare/crypto/__init__.py): Xuất các class và hàm công khai phục vụ các module khác sử dụng.


#### B. Phân hệ Quản lý Khóa & Software KMS ([`src/medshare/broker/`](src/medshare/broker/)) — [ĐÃ HOÀN THÀNH WP4]
* [`kms.py`](src/medshare/broker/kms.py): Lớp kết nối Software KMS tại Zone Z1:
  * `VaultKmsClient`: Kết nối HashiCorp Vault Transit API (`http://localhost:8200`), kích hoạt `derived: True` để context binding chặt chẽ ở cấp độ KDF của KMS. Hỗ trợ bọc (`wrap_dek`), gỡ (`unwrap_dek`), xoay vòng (`rotate_key`) và bọc lại (`rewrap_dek`).
  * `MockKmsClient`: Bộ giả lập Software KMS cục bộ dùng AES-256-GCM phục vụ chạy unit tests độc lập khi offline.
* [`capsule.py`](src/medshare/broker/capsule.py): Cấu trúc dữ liệu `KeyCapsule` đóng gói DEK đã bọc, metadata khóa (`kek_id`, `kek_version`), và ngữ cảnh ràng buộc `bound_object_context` chuẩn hóa JCS RFC 8785 (`domain = medshare/wrap/v1`).
* [`broker.py`](src/medshare/broker/broker.py): Lõi `KeyBroker` hoạt động như Policy Enforcement Point (PEP) độc lập tại Zone Z1:
  * `issue_dek_and_capsule()`: Sinh fresh 256-bit DEK ngẫu nhiên bằng CSPRNG, bọc qua Vault KMS và chỉ lưu DEK tạm thời trong RAM.
  * `unwrap_dek()`: Thực thi chốt chặn bảo mật **TC-06 (Tenant Boundary)** ngăn chặn truy cập chéo giữa các bệnh viện, phát hiện tráo đổi ngữ cảnh bệnh nhân và phát hiện phát lại capsule cũ (Anti-Replay).
  * `rewrap_capsule()`: Hỗ trợ **TC-09 (Zero-Data-Mutation Rewrap)** nâng cấp phiên bản KEK mà không cần giải mã lại dữ liệu trên đĩa.
* [`__init__.py`](src/medshare/broker/__init__.py): Xuất giao diện công khai cho package broker.

#### C. Phân hệ Lưu trữ Tầng trường ([`src/medshare/storage/`](src/medshare/storage/)) — [ĐÃ HOÀN THÀNH WP4]
* [`schema.py`](src/medshare/storage/schema.py): Đặc tả tên collection và chỉ mục MongoDB 7.0 (`key_capsules`, `encrypted_patients`, `search_index`, `patient_attachments`).
* [`dal.py`](src/medshare/storage/dal.py): Lớp Data Access Layer (DAL) tương tác với Zone Z2:
  * `EncryptedPatientRecord`: Cấu trúc bản ghi bệnh nhân đã mã hóa chứa các trường `FieldEnvelope` và mã băm Blind Index Token.
  * `EncryptedAttachmentMeta`: Metadata tệp đính kèm (object key MinIO, capsule, số chunk).
  * `MongoStorage`: Thao tác ghi/đọc trên MongoDB 7.0 (mặc định DB `medshare_db`), kèm truy vấn thô quyền DBA phục vụ kiểm chứng TC-02. *(PostgreSQL đã bị loại khỏi kiến trúc — xem TIEN_DO_HIEN_TAI.md mục 3, ý 5.)*
* [`minio_dal.py`](src/medshare/storage/minio_dal.py): `MinioStorage` — lưu/đọc object ciphertext trên MinIO (bucket `medshare-{tenant}`), không giữ khóa hay bản rõ.
* [`__init__.py`](src/medshare/storage/__init__.py): Xuất giao diện lưu trữ.

#### D. Phân hệ Chính sách Phân quyền ABAC ([`src/medshare/policy/`](src/medshare/policy/)) — [ĐÃ HOÀN THÀNH WP5]
* [`abac.py`](src/medshare/policy/abac.py): Lõi Policy Decision Point (PDP) Zone Z1:
  * `AbacPolicyEngine`: Động cơ ra quyết định tuân thủ nguyên tắc **Deny-by-Default**. Đánh giá 4 chiều: Subject (Role, Dept, Clearance, Tenant), Object (Record, Dept, Sensitivity), Action (READ, WRITE, SEARCH, EXPORT), Environment.
  * `BreakGlassTicket`: Quản lý quy trình cấp cứu khẩn cấp có thời hạn (`valid_from` $\to$ `valid_until`), có người phê duyệt, và gắn cờ audit khẩn cấp (TC-04).
  * `revocation_list`: Danh sách thu hồi người dùng tức thời ngăn chặn truy cập ngay lập tức (TC-07).
  * Thực thi chốt chặn **TC-27 (Admin/DBA Restriction)**: Cấm tuyệt đối tài khoản quản trị viên truy cập hồ sơ bệnh án lâm sàng.
* [`__init__.py`](src/medshare/policy/__init__.py): Xuất giao diện chính sách.

#### E. Phân hệ Trusted Crypto Gateway ([`src/medshare/gateway/`](src/medshare/gateway/)) — [ĐÃ HOÀN THÀNH WP5]
* [`service.py`](src/medshare/gateway/service.py): Lớp điều phối Gateway PEP tại Zone Z1:
  * `ClinicalGatewayService`: Tích hợp ABAC PDP, Key Broker, FieldCipherEngine và Storage DAL.
  * `ingest_patient_record()`: Tiếp nhận hồ sơ bệnh án (Pipeline W1), kiểm tra quyền ghi qua Gateway PEP, bọc DEK và mã hóa trường AAD trước khi ghi xuống Cloud DB.
  * `read_patient_record()`: Tiếp nhận truy vấn đọc (Pipeline W2), thực thi **Kiến trúc Phòng thủ Hai lớp (Dual PEP)** phối hợp giữa Gateway PEP và Broker PEP.
  * **Chiếu trường An toàn (Field Projection)**: Tự động lọc và giấu các trường nhạy cảm vượt thẩm quyền (như Điều dưỡng chỉ xem thông tin hành chính, giấu chẩn đoán lâm sàng).
  * Ghi nhận nhật ký kiểm toán F9 (Metadata only) độc lập tại Zone Z3.
* [`api.py`](src/medshare/gateway/api.py): FastAPI backend cho Web Portal — các endpoint `/api/v1/auth/*`, `/patients`, `/attachments`, `/crypto/abe/*`, `/crypto/he/sum`, `/dba/raw-records`, `/audit/logs`; tự seed dữ liệu demo khi import và phục vụ `frontend/dist` tại `/`.
* [`__init__.py`](src/medshare/gateway/__init__.py): Xuất giao diện gateway service.

#### F. Phân hệ Định danh Zone Z1 ([`src/medshare/auth/`](src/medshare/auth/)) — [ĐÃ HOÀN THÀNH WP10]
* [`service.py`](src/medshare/auth/service.py): Cấp phát/thu hồi tài khoản, băm Argon2id, JWT HS256, HMAC `record_mac` chống DBA sửa thuộc tính, quy tắc username cá thể hóa (`format_individual_username`).

---

### 2.4. Thư mục Dữ liệu Tổng hợp & Bộ Nạp ([`datasets/`](datasets/)) — [ĐÃ HOÀN THÀNH WP2]
* [`generate_datasets.py`](datasets/generate_datasets.py): Script tự động sinh tập dữ liệu hồ sơ y tế tổng hợp (Synthetic EHR):
  * Tạo dữ liệu quy mô 1.000 và 10.000 bản ghi.
  * Hỗ trợ 5 seeds độc lập cho kiểm thử thống kê: `1801`, `1802`, `1803`, `1804`, `1805`.
  * Hỗ trợ 2 chế độ phân bố: `uniform` (đều) và `skewed` (theo luật Zipf phản ánh thực tế bệnh viện phục vụ đo lường suy luận tần suất E5).
* [`loader.py`](datasets/loader.py): Script nạp dữ liệu sạch (baseline B0, plaintext) vào MongoDB 7.0:
  * Khởi tạo collection `ehr_records` trong DB `medshare_records` (với compound indexes). Tham số: `--file <json> [--reset]`.
  * Nạp dữ liệu theo batch insert hiệu năng cao và đo lường dung lượng lưu trữ (Data size, Index size).
* `datasets/generated/`: Thư mục lưu các file JSON dữ liệu tổng hợp đã sinh (gitignored).
* `datasets/samples/raw/`: 15 tệp y tế mẫu theo modality (`xray/`, `ultrasound/`, `ct_mri/`, `reports/`) và `manifest.json`.
* `datasets/oracle/`: Thư mục lưu các file Plaintext Ground Truth Oracle phục vụ kiểm chứng tính đúng độc lập (Differential Oracle Verification - gitignored).

---

### 2.5. Thư mục Đo lường Hiệu năng & Thực nghiệm ([`benchmarks/`](benchmarks/)) — [ĐÃ HOÀN THÀNH E1, E2, E3, E4, E5, E7]
* [`run_e1_baseline.py`](benchmarks/run_e1_baseline.py): Script chạy Thí nghiệm E1 (Plaintext & Volume Baseline Benchmark):
  * Đo lường độ trễ (p50, p95, p99) và Throughput (QPS) cho các truy vấn mẫu: W1 (Point read), W2 (Equality search), W7 (Bulk write).
  * Thực thi qua 5 lần lặp độc lập trên MongoDB 7.0.
  * Kiểm thử ranh giới bảo mật **TC-08** (Mô phỏng đĩa ảo LUKS bị trộm offline có Shannon entropy = 7.997 bits/byte).
  * Chứng minh giới hạn chí tử của B1 **TC-02** (DBA truy vấn trực tiếp đọc được 100% Plaintext khi DB đang chạy).
* [`run_e2_field_overhead.py`](benchmarks/run_e2_field_overhead.py): Script chạy Thí nghiệm E2 (Field Envelope Overhead & Key Separation):
  * Đo lường chi phí độ trễ Profile P1 (W1 Write p50 = 2.522 ms, W2 Read p50 = 1.346 ms — theo `e2_field_overhead_report.json`).
  * Phân rã chi phí Ablation (P50): CPU AES-256-GCM < 5%, KMS wrap/unwrap ≈ 53–55%, MongoDB I/O ≈ 41–43%.
  * Xác thực 4 Security Gates: TC-02 (DBA query chỉ thấy Base64), TC-06 (Tenant boundary), TC-09 (KEK rotation data preservation), TC-10 (0 canary leaks).
* [`run_e3_abac_bypass.py`](benchmarks/run_e3_abac_bypass.py): Script chạy Thí nghiệm E3 (ABAC Enforcement, Break-Glass & Bypass Assurance):
  * Đo độ trễ ra quyết định chính sách PDP (p50 = 2.49 $\mu$s, p95 = 2.88 $\mu$s).
  * Bảng chân lý Truth Table: 50 requests, False Permit Rate = 0.0%, False Deny Rate = 0.0%.
  * Xác thực 4 Security Gates: TC-03 (Chặn khác khoa & khác bệnh viện), TC-04 (Vòng đời Break-glass), TC-07 (Thu hồi tức thì), TC-27 (DBA bypass RLS nhưng thất bại tại Key Broker PEP — **Gate Tuần 6 PASSED**).
* [`run_e5_leakage_analysis.py`](benchmarks/run_e5_leakage_analysis.py): Script chạy Thí nghiệm E5 (Equality Blind Index & Leakage Inference Analysis — WP6 Tuần 7):
  * Đo lường tính đúng đắn tra cứu đẳng thức, kiểm tra biên chuẩn hóa Unicode NFC, vòng đời Update/Delete, và từ chối truy vấn range/wildcard ngoài phạm vi bằng HTTP 422 (TC-15).
  * Giả lập tấn công suy luận tần suất (Frequency-Rank Matching Attack) với tập auxiliary corpus độc lập: Skewed Zipf Micro Accuracy = 79.6% (Advantage = +42.8%), Uniform Micro Accuracy = 16.6% (TC-16).
  * Kiểm chứng hậu kiểm Gateway (Post-Filter) loại bỏ 100% bản ghi giả mạo do Cloud chèn vào chỉ mục và minh định rõ giới hạn thiết kế LIMIT đối với tấn công bỏ sót kết quả (TC-17).
* [`run_e4_cpabe_sharing.py`](benchmarks/run_e4_cpabe_sharing.py): Thí nghiệm E4 — CP-ABE AC17 trên BN254 & SS512 với số lá chính sách $k \in \{2,4,8,16\}$; gates TC-11 → TC-14 (đúng chính sách, chống thông đồng, thu hồi theo epoch, giới hạn giải mã offline).
* [`run_e7_homomorphic_sum.py`](benchmarks/run_e7_homomorphic_sum.py): Thí nghiệm E7 — BFV SUM trên cohort N = 10 → 1.000, theo dõi noise budget; gates TC-18, TC-19 (LIMIT), TC-30.
* `benchmarks/results/`: Báo cáo JSON (`e1_baseline_report.json`, `e2_field_overhead_report.json`, `e3_abac_bypass_report.json`, `e4_cpabe_results.json`, `e5_leakage_analysis_report.json`, `e7_bfv_results.json` — gitignored).

---

### 2.6. Thư mục Bằng chứng Thực nghiệm ([`evidence/`](evidence/))
* `evidence/runs/e1_baseline_evidence.md`: Bằng chứng thực nghiệm độc lập của Thí nghiệm E1, lưu giữ bảng số liệu latency p50/p95, dung lượng lưu trữ, entropy đĩa mã hóa và mẫu dữ liệu rò rỉ trước DBA.
* `evidence/runs/e2_field_overhead_evidence.md`: Bằng chứng thực nghiệm Thí nghiệm E2, bảng số liệu phân rã chi phí ablation, kết quả 4 ranh giới an toàn TC-02, TC-06, TC-09, TC-10.
* `evidence/runs/e3_abac_bypass_evidence.md`: Bằng chứng thực nghiệm Thí nghiệm E3, bảng chân lý Truth Table, độ trễ PDP CPU microseconds, và bằng chứng chốt chặn phòng thủ hai lớp Dual PEP (TC-27 Gate Tuần 6).
* `evidence/runs/e4_cpabe_sharing_evidence.md`: Bằng chứng Thí nghiệm E4 (kích thước/thời gian CP-ABE theo $k$, TC-11 → TC-14).
* `evidence/runs/e7_homomorphic_sum_evidence.md`: Bằng chứng Thí nghiệm E7 (Integer Exactness, noise budget, TC-18/19/30).
* `evidence/runs/e5_leakage_analysis_evidence.md`: Bằng chứng thực nghiệm Thí nghiệm E5, bảng số liệu rò rỉ mẫu truy vấn, kết quả tấn công suy luận tần suất kèm khoảng tin cậy Bootstrap CI 95%, và khuyến nghị chuẩn không đánh chỉ mục Blind Index trên các trường chẩn đoán lâm sàng có entropy thấp.


---

### 2.7. Thư mục Hạ tầng Lab ([`infra/`](infra/))
* [`docker-compose.yml`](infra/docker-compose.yml): Cấu hình khởi chạy cụm dịch vụ container của Lab:
  * **`mongo-cloud`:** Container `medshare-mongo` (MongoDB 7.0, port `27017`, user `medshare_dba`; DB `medshare_db` cho Portal/DAL/ingest và `medshare_records` cho baseline loader).
  * **`vault-kms`:** Container `medshare-vault-kms` (HashiCorp Vault 1.15.6, port `8200`, token lab `dev-root-token-topic18`). File storage bền vững + tự init/unseal/bật Transit qua [`infra/vault/entrypoint.sh`](infra/vault/entrypoint.sh).
  * **`minio-cloud`:** Container `medshare-minio` (MinIO, S3 API `9000`, Console `9001`; healthcheck bằng BusyBox `wget`).
  * **`abe-worker`:** Container `medshare-abe-worker` (image cục bộ, phải `docker build` trước; FastAPI `:9002`).
* `infra/certs/`: Chứng chỉ RSA-2048 tự ký cho Portal HTTPS (sinh tự động bởi `scripts/run_portal.sh`).
* `infra/runtime/`: Thư mục lưu trữ volume cục bộ của MongoDB, MinIO và Vault (gitignored).

---

### 2.8. Thư mục Worker Mật mã Nâng cao ([`workers/`](workers/)) — [ĐÃ HOÀN THÀNH SPIKE]
Chứa 3 worker mật mã chuyên sâu được đóng gói thành các Docker container hoàn toàn cô lập:

#### A. CP-ABE Worker ([`workers/abe/`](workers/abe/))
* **Mục đích:** Profile P2 (Fine-grained Data Sharing) — Mã hóa chia sẻ hồ sơ bệnh án liên viện dựa trên chính sách thuộc tính logic boolean.
* **Công nghệ:** Ubuntu 22.04 LTS + Thư viện Stanford PBC 0.5.14 + Thư viện `charm-crypto` (Scheme AC17 trên đường cong SS512/BN254).
* [`Dockerfile`](workers/abe/Dockerfile): Quy trình tự động tải, biên dịch Stanford PBC và Charm-Crypto từ nguồn C.
* [`engine.py`](workers/abe/engine.py), [`service.py`](workers/abe/service.py), [`cli.py`](workers/abe/cli.py): Lõi AC17 + KEM/DEM AES-GCM, REST API `:9002`, và CLI fallback.
* [`smoke_test.py`](workers/abe/smoke_test.py): Kịch bản kiểm thử: Positive test (Bác sĩ chuyên khoa thỏa policy giải mã thành công) và Negative test (Điều dưỡng không đủ thuộc tính bị từ chối giải mã).
* `workers/abe/reference/`: Mã nguồn tham khảo từ công trình của tác giả Đào Võ Hữu Hiệp (`daovohuuhiep2003/Project-MMH-CP-ABE`).

#### B. Homomorphic Encryption Worker ([`workers/he/`](workers/he/))
* **Mục đích:** Profile P3 (Privacy-Preserving Aggregates) — Tính toán tổng chi phí điều trị (SUM) trực tiếp trên bản mã số nguyên mà máy chủ Cloud không cần giải mã.
* **Công nghệ:** Ubuntu 22.04 LTS + Microsoft SEAL v4.1.2 + C++17 + Ninja Build.
* [`Dockerfile`](workers/he/Dockerfile): Quy trình tự động tải Microsoft SEAL v4.1.2 từ GitHub và biên dịch C++ native.
* [`CMakeLists.txt`](workers/he/CMakeLists.txt): Cấu hình build C++ liên kết với thư viện `SEAL::seal`.
* [`seal_bfv_engine.cpp`](workers/he/seal_bfv_engine.cpp): Engine BFV dùng cho E7/Portal ($N = 8192$, plain modulus 30-bit batching; chế độ `benchmark`, `aggregate`, `tamper_test`).
* [`smoke_test.cpp`](workers/he/smoke_test.cpp): Kịch bản kiểm thử (plain modulus 20-bit): Data Owner mã hóa 4 khoản chi phí, Cloud Worker thực thi phép cộng đồng cấu `evaluator.add()`, Owner giải mã kết quả chính xác 100% số nguyên ($2000$), đối thủ không có khóa giải mã thất bại.

#### C. Post-Quantum Cryptography Worker ([`workers/pqc/`](workers/pqc/))
* **Mục đích:** Profile P4 (PQC Readiness & Migration) — Chuẩn bị lộ trình di chuyển kháng máy tính lượng tử.
* **Công nghệ:** Python 3.11 Slim Bookworm + Thư viện `liboqs` C native v0.10+ & `liboqs-python`.
* [`Dockerfile`](workers/pqc/Dockerfile): Quy trình tự động biên dịch `liboqs` C native và cài đặt wrapper Python.
* [`smoke_test.py`](workers/pqc/smoke_test.py): Kịch bản kiểm thử FIPS 203 (ML-KEM-768 đóng gói khóa 32-byte DEK) và FIPS 204 (ML-DSA-65 ký số thông điệp y tế và phát hiện giả mạo).

---

### 2.9. Thư mục Kiểm thử Tự động ([`tests/`](tests/))
Chứa hệ thống test cases thực thi qua lệnh `pytest tests/`:

#### A. Kiểm thử Đơn vị ([`tests/unit/`](tests/unit/))
* [`test_dataset_generator.py`](tests/unit/test_dataset_generator.py): Kiểm tra cấu trúc bản ghi synthetic, tính duy nhất UUIDv4, tính toàn vẹn của Plaintext Oracle và sự phân bố tần suất theo luật Zipf.
* [`test_field_crypto.py`](tests/unit/test_field_crypto.py): Kiểm thử TC-01 (Mã hóa/giải mã round-trip chuỗi UTF-8, số nguyên, empty/null, kiểm tra Nonce/Ciphertext ngẫu nhiên) và TC-24 (Kiểm tra giới hạn kích thước, bắt lỗi format_version và suite không hỗ trợ).
* [`test_kms_broker.py`](tests/unit/test_kms_broker.py): Kiểm thử Software KMS (MockKmsClient/Vault Transit), đóng gói KeyCapsule, unwrap DEK, rewrap capsule nâng cấp phiên bản KEK (TC-09).
* [`test_abac_gateway.py`](tests/unit/test_abac_gateway.py): Kiểm thử động cơ chính sách ABAC (Doctor/Nurse, cấm Admin/DBA TC-27, danh sách thu hồi người dùng TC-07, và vé cấp cứu Break-Glass TC-04).
* [`test_portal_api.py`](tests/unit/test_portal_api.py): 9 test API Portal — đăng nhập username cá thể hóa, cấp/thu hồi tài khoản (TC-07), đổi mật khẩu vô hiệu token cũ, phân tách tenant. *Cần Vault Transit đang chạy vì module import sẽ seed dữ liệu.*
* [`test_blind_index.py`](tests/unit/test_blind_index.py): Kiểm thử Equality Blind Index: chuẩn hóa Unicode NFC, chữ hoa/chữ thường, tính tất định HMAC, phân tách tenant/field/epoch, từ chối range/wildcard (HTTP 422), và hậu kiểm Gateway loại bỏ bản ghi giả mạo (TC-15, TC-17).

#### B. Kiểm thử Bảo mật Đối kháng ([`tests/security/`](tests/security/))
* [`test_e1_baseline.py`](tests/security/test_e1_baseline.py): Kiểm thử ranh giới bảo mật Baseline B0/B1: TC-08 (Shannon entropy đĩa mã hóa $> 7.99$) và TC-02 (Chứng minh lỗ hổng đọc bản rõ trực tiếp từ DBA).
* [`test_e2_key_separation.py`](tests/security/test_e2_key_separation.py): Kiểm thử cô lập khóa khỏi Cloud DB: TC-02 (DBA chỉ thấy ciphertext và capsule), TC-06 (Cô lập đa tenant và chống replay), TC-09 (Xoay vòng KEK bảo toàn bản mã), TC-10 (Quét canary bản rõ).
* [`test_e3_abac_bypass.py`](tests/security/test_e3_abac_bypass.py): Kiểm thử phòng thủ hai lớp Dual PEP: TC-03 (Từ chối khác khoa/khác bệnh viện), TC-04 (Vòng đời Break-glass), TC-07 (Tuyến tính hóa thu hồi tức thời), TC-27 (DBA bypass RLS nhưng thất bại tại Key Broker PEP — Critical Gate Tuần 6).
* [`test_e5_blind_index.py`](tests/security/test_e5_blind_index.py): Kiểm thử ranh giới bảo mật truy vấn mù: TC-15 (Đúng đắn tra cứu, Unicode NFC, update/delete, từ chối range/wildcard 422), TC-16 (Tấn công suy luận tần suất trên phân bố lệch với tập auxiliary độc lập), TC-17 (Hậu kiểm Gateway decrypt phát hiện và loại bỏ ứng viên giả mạo, xác nhận giới hạn omission).
* [`test_e4_cpabe_sharing.py`](tests/security/test_e4_cpabe_sharing.py): 6 test CP-ABE (TC-11 → TC-14, tamper tag/ciphertext/context).
* [`test_e7_homomorphic_encryption.py`](tests/security/test_e7_homomorphic_encryption.py): 6 test BFV (TC-18, TC-19, TC-30).
* [`test_minio_attachments.py`](tests/security/test_minio_attachments.py): 6 test tệp đính kèm MinIO (toàn vẹn chunk, chunk swapping, cô lập tenant, ABAC).
* [`test_tc05_envelope_tamper.py`](tests/security/test_tc05_envelope_tamper.py): Kiểm thử đối kháng TC-05:
  * Lật 1 bit trên Ciphertext $\rightarrow$ Bị từ chối bởi `DecryptionIntegrityError`.
  * Sửa đổi 1 byte trên Authentication Tag $\rightarrow$ Bị từ chối.
  * Can thiệp Nonce $\rightarrow$ Bị từ chối.
  * Tấn công tráo bản mã giữa 2 bệnh nhân (Cross-patient swap) $\rightarrow$ Bị chặn bởi `ContextMismatchError`.
  * Tấn công tráo bản mã giữa 2 bệnh viện (Cross-tenant swap) $\rightarrow$ Bị chặn.
  * Tấn công tráo bản mã giữa 2 trường khác nhau (Cross-field swap) $\rightarrow$ Bị chặn.
  * Tấn công tráo phiên bản cũ (Stale version swap) $\rightarrow$ Bị chặn.
  * Giải mã bằng sai khóa DEK $\rightarrow$ Bị từ chối.


#### C. Kiểm thử Công cụ Repository ([`tests/tooling/`](tests/tooling/))
* [`test_render_proposal.py`](tests/tooling/test_render_proposal.py): Kiểm thử chức năng render Word DOCX từ Markdown (kiểm tra pipe escape, bảng, link an toàn, tính tất định).
* [`test_repository.py`](tests/tooling/test_repository.py): Kiểm thử toàn vẹn repository: kiểm tra file nhạy cảm được che giấu trong `.gitignore`, liên kết tài liệu không bị hỏng, đồng bộ nội dung Proposal.

#### D. Kiểm thử Tích hợp ([`tests/integration/`](tests/integration/))
* Hiện chỉ có `README.md` — chưa có test tích hợp riêng; luồng end-to-end đang được phủ gián tiếp qua `tests/unit/test_portal_api.py` và các test bảo mật dùng Mongo/Vault/MinIO thật.

---

### 2.10. Thư mục Scripts Công cụ ([`scripts/`](scripts/))
* [`setup_ubuntu.sh`](scripts/setup_ubuntu.sh): Script bash thiết lập môi trường tự động: cài đặt apt packages, trình biên dịch C/C++, Docker, biên dịch Stanford PBC, khởi tạo `.venv` và sanity check.
* [`check_repo.py`](scripts/check_repo.py): Bộ công cụ kiểm tra đối soát chất lượng repository trước mỗi lần commit/push (chạy syntax checks, doc links, proposal sync, tooling tests).
* [`render_proposal.py`](scripts/render_proposal.py): Script độc lập biên dịch file Markdown Proposal sang Word DOCX chính xác đến từng ô bảng, tiêu đề và liên kết.
* [`validate_docs.py`](scripts/validate_docs.py): Công cụ kiểm tra toàn bộ liên kết nội bộ, hình ảnh và cấu trúc cú pháp các khối Mermaid trong thư mục `docs/`.
* [`validate_proposal_sync.py`](scripts/validate_proposal_sync.py): Công cụ kiểm tra tính đồng bộ nội dung từng dòng, từng bảng giữa file Markdown và file Word DOCX của Proposal.
* [`run_portal.sh`](scripts/run_portal.sh): Chạy Portal (`http 8000` hoặc `https 8443` TLS 1.3, tự sinh cert tự ký nếu chưa có).
* [`prepare_medical_samples.py`](scripts/prepare_medical_samples.py) / [`ingest_medical_samples.py`](scripts/ingest_medical_samples.py): Chuẩn bị 15 tệp mẫu + manifest, sau đó mã hóa chunked và nạp vào MinIO + metadata MongoDB.
* [`gen_proposal_pptx.py`](scripts/gen_proposal_pptx.py): Sinh slide `PROPOSAL_MedShare_Lab.pptx`.

---

### 2.11. Thư mục Phân tích & Thống kê ([`analysis/`](analysis/))
* `analysis/output/`: Nơi xuất các biểu đồ Matplotlib/Seaborn phân tích hiệu năng, khoảng tin cậy 95% (CI 95%) và biểu đồ đo lường rò rỉ suy luận tần suất (phục vụ viết Báo cáo khoa học 13 chương ở Tuần 11 & 12).

---

## 3. BẢNG TRA CỨU NHANH THEO MÃ CÔNG VIỆC (WORK PACKAGE INDEX)

| Giai đoạn & Tuần | Mã Work Package | Thư mục & Tệp tin trọng tâm | Trạng thái hiện tại |
|---|---|---|:---:|
| **Tuần 1 & 2** | **WP1:** System, Trust Model & Feasibility Spikes | `docs/design/`, `docs/planning/`, `workers/abe/`, `workers/he/`, `workers/pqc/`, `scripts/setup_ubuntu.sh` | **HOÀN THÀNH (100%)** |
| **Tuần 3** | **WP2:** Synthetic Datasets & Baseline B0/B1 | `datasets/generate_datasets.py`, `datasets/loader.py`, `benchmarks/run_e1_baseline.py`, `evidence/runs/` | **HOÀN THÀNH (100%)** |
| **Tuần 4** | **WP3:** Field Envelope Encryption Engine | `src/medshare/crypto/` (`errors.py`, `context.py`, `envelope.py`, `engine.py`), `tests/security/test_tc05_envelope_tamper.py` | **HOÀN THÀNH (100%)** |
| **Tuần 5** | **WP4:** Key Broker, Software KMS & Persistence | `src/medshare/broker/`, `src/medshare/storage/`, `infra/docker-compose.yml` (Thí nghiệm E2) | **HOÀN THÀNH (100%)** |
| **Tuần 6** | **WP5:** ABAC Engine, Break-glass & Gateway PEP | `src/medshare/policy/`, `src/medshare/gateway/` (Thí nghiệm E3) | **HOÀN THÀNH (100%)** |
| **Tuần 7** | **WP6:** Equality Blind Index & Leakage Analysis | `src/medshare/crypto/blind_index.py` (Thí nghiệm E5) | **HOÀN THÀNH (100%)** |
| **Tuần 8** | **WP7:** Homomorphic Encryption Integration | `workers/he/`, `src/medshare/crypto/he_client.py` (Thí nghiệm E7) | **HOÀN THÀNH (100%)** |
| **Tuần 9** | **WP8:** CP-ABE Data Sharing Integration | `workers/abe/`, `src/medshare/crypto/abe_client.py` (Thí nghiệm E4) | **HOÀN THÀNH (100%)** |
| **Bổ sung** | MinIO S3 & 15 tệp y tế mẫu | `src/medshare/storage/minio_dal.py`, `src/medshare/crypto/file_cipher.py`, `scripts/ingest_medical_samples.py` | **HOÀN THÀNH (100%)** |
| **Tuần 10** | **WP10:** Web Portal Vue 3 + FastAPI + TLS 1.3 & IdP Zone Z1 | `frontend/`, `src/medshare/gateway/api.py`, `src/medshare/auth/` | **HOÀN THÀNH (100%)** |
| **Tuần 11** | **WP9:** Post-Quantum Migration & Lifecycle (E8/E9); mTLS nội bộ (phạm vi rút gọn) | `workers/pqc/`, KEM/DSA, xoay vòng KEK, `plan-mTLS.md` | *Đang thực hiện / tiếp theo* |
| **Tuần 12** | Evidence Consolidation, Report & Demo | `evidence/`, `benchmarks/`, báo cáo 13 chương, slide, live demo | *Kế hoạch tuần 12* |

