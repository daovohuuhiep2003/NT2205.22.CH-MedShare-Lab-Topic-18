# MedShare-Lab — Topic 18

Đồ án **Mật mã học và ứng dụng — NT2205.11.CH**, bậc thạc sĩ An toàn thông tin; nhóm 2 học viên, 12 tuần.

**Bảo vệ hồ sơ y tế đa tenant trên Cloud DBMS:** kiến trúc phân lớp 4 vùng tin cậy (Z0–Z3), mã hóa tầng trường AES-256-GCM + Vault KMS, ABAC hai lớp PEP, chỉ mục mù HMAC, chia sẻ CP-ABE, tính tổng đồng cấu BFV và lộ trình hậu lượng tử.

## Trạng thái (23/11/2026)

| Hạng mục | Trạng thái |
|---|---|
| WP1–WP8, WP10 (Tuần 1–10): field envelope, Key Broker + Vault, ABAC/Break-glass, Blind Index, BFV, CP-ABE, MinIO, Web Portal TLS 1.3 | **Đã triển khai** |
| Thí nghiệm E1, E2, E3, E4, E5, E7 | **Đã chạy**, có báo cáo JSON + evidence Markdown (lưu local, xem bên dưới) |
| Test tự động | `pytest tests/` — **100 passed**; `scripts/check_repo.py` — **16/16 OK** |
| WP9 (PQC migration E8, xoay vòng khóa E9), mTLS nội bộ, audit witness Z3 | **Tuần 11** — chưa được triển khai |

Chi tiết tiến độ: [TIEN_DO_HIEN_TAI.md](TIEN_DO_HIEN_TAI.md). Trạng thái từng threat/SR/TC: [ma trận truy vết](docs/testing/traceability-matrix.md). Kết quả test chứng minh hành vi trong phạm vi test case, không phải chứng nhận an toàn mật mã.

## Kiến trúc đã triển khai

| Thành phần | Công nghệ | Vùng |
|---|---|---|
| Web Portal | Vue 3 + Vite + TailwindCSS (`frontend/`), FastAPI (`src/medshare/gateway/api.py`), TLS 1.3 | Z0/Z1 |
| Định danh | Argon2id, JWT HS256, HMAC `record_mac` chống sửa thuộc tính (`src/medshare/auth/`) | Z1 |
| Gateway + ABAC | Dual PEP, deny-by-default, field projection, break-glass (`gateway/`, `policy/`) | Z1 |
| Key Broker + KMS | DEK 256-bit, KeyCapsule RFC 8785, HashiCorp Vault Transit (`broker/`) | Z1 |
| Lưu trữ | MongoDB 7.0 (envelope, capsule, blind index) + MinIO (tệp mã hóa chunked) | Z2 |
| CP-ABE | AC17 trên Charm-Crypto, BN254 & SS512, REST `:9002` (`workers/abe/`) | Z1/Z0 |
| HE | Microsoft SEAL 4.1.2 BFV, N = 8192 (`workers/he/`) | Z2 |
| PQC | liboqs ML-KEM-768 / ML-DSA-65 — mới ở mức smoke test (`workers/pqc/`) | — |

Các quyết định lệch khỏi proposal ban đầu (bỏ PostgreSQL, chọn AC17 thay BSW07, Vault bền vững) được ghi tại [docs/adr/](docs/adr/README.md).

## Chạy nhanh

Yêu cầu: Ubuntu 22.04/24.04, Docker + Compose, Python 3.12 (`scripts/setup_ubuntu.sh` cài toàn bộ).

```bash
docker build -t medshare-abe-worker ./workers/abe          # lần đầu
docker compose -f infra/docker-compose.yml up -d           # mongo, vault, minio, abe-worker
PYTHONPATH=src:. .venv/bin/python -m pytest tests/ -q      # 100 tests
./scripts/run_portal.sh https 8443                         # https://127.0.0.1:8443
```

Tài khoản demo, cổng, lệnh nạp dữ liệu/benchmark và xử lý sự cố: [HUONG_DAN_DICH_VU.md](HUONG_DAN_DICH_VU.md). Bản đồ từng file: [MUC_LUC_DU_AN.md](MUC_LUC_DU_AN.md).

## Nguồn chuẩn

- **Proposal chuẩn:** [docs/proposal/project-proposal.md](docs/proposal/project-proposal.md); bản Word sinh bằng `python -B scripts/render_proposal.py`. Proposal giữ phạm vi đã đăng ký; thay đổi kỹ thuật sau đó nằm trong ADR.
- [Kế hoạch triển khai](docs/planning/implementation-plan.md), [kế hoạch từng bước](docs/planning/step-by-step-plan.md).
- [Thiết kế mật mã](docs/design/crypto-and-protocol-design.md), [thí nghiệm và test catalog](docs/testing/experiments-and-validation.md).
- [Guideline](docs/requirements/course-guideline.md) và [Topic 18](docs/requirements/topic-18.md) giữ nguyên nội dung, có kiểm tra SHA-256.

## Cấu trúc repository

| Thư mục | Nội dung |
|---|---|
| `src/medshare/` | Python core: `auth`, `broker`, `crypto`, `gateway`, `policy`, `storage` |
| `frontend/` | Web Portal Vue 3 (`npm run build` → `dist/`, được FastAPI phục vụ) |
| `workers/` | CP-ABE (REST), SEAL BFV (CLI), PQC (CLI) — mỗi worker một Dockerfile |
| `infra/` | `docker-compose.yml`, cấu hình Vault bền vững, cert Portal |
| `tests/` | `unit/`, `security/`, `tooling/` (100 tests) |
| `benchmarks/` | Harness E1, E2, E3, E4, E5, E7 |
| `datasets/` | Bộ sinh dữ liệu synthetic, loader, manifest tệp mẫu |
| `docs/` | Proposal, requirements, planning, design, testing, diagrams, ADR |
| `scripts/` | Setup, portal, ingest, render/kiểm tra tài liệu |

Output thực nghiệm (`benchmarks/results/`, `evidence/runs/`), dataset sinh ra và volume runtime **không commit** (xem `.gitignore`); chạy lại harness để tái tạo.

## Phạm vi nghiên cứu

Dữ liệu tổng hợp trên MongoDB 7.0 + MinIO: volume baseline; field envelope + broker/KMS + ABAC; equality blind index có leakage contract; CP-ABE share; BFV SUM/count; PQC key/signature migration. 8 thí nghiệm E1–E5/E7–E9, 18 SR, 12 CR và 30 nhóm TC. Không xây DBMS mới, không full FHE SQL, không tuyên bố zero leakage hoặc end-to-end PQ security.

## Bảo mật

Repository này **công khai**. Mọi mật khẩu/token trong tài liệu là giá trị **dev mặc định cho lab**, không phải bí mật thật; không triển khai ra Internet với các giá trị này. Kết nối nội bộ giữa Gateway và Vault/MinIO/worker chưa có TLS. Xem [SECURITY.md](SECURITY.md) và [CONTRIBUTING.md](CONTRIBUTING.md).
