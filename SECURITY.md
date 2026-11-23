# An toàn dữ liệu và báo lỗi bảo mật

MedShare-Lab là đồ án nghiên cứu, **không có bảo đảm production**. Chỉ dùng dữ liệu tổng hợp hoặc dữ liệu công khai đã khử định danh; không đưa hồ sơ bệnh nhân thật, khóa production hoặc credentials cloud thật vào repository.

Repository đang **công khai** tại `github.com/daovohuuhiep2003/NT2205.22.CH-MedShare-Lab-Topic-18`. Mọi nội dung đã push coi như đã công bố, kể cả lịch sử Git.

## 1. Giá trị dev mặc định đã công khai (không phải bí mật)

Các giá trị dưới đây xuất hiện trong `infra/docker-compose.yml`, mã nguồn và `HUONG_DAN_DICH_VU.md`, **chỉ dùng cho lab cục bộ**:

| Thành phần | Giá trị mặc định |
|---|---|
| MongoDB | user `medshare_dba` / `dba_secret_dev_pass` |
| Vault | token lab `dev-root-token-topic18` (quyền root) |
| MinIO | `medshare_admin` / `minio_secret_dev_pass` |
| Web Portal | `Admin@MedShare2026!`, `Staff@MedShare2026!`, `Patient@2026!` cho 1.012 tài khoản demo |

Vì ai cũng biết các giá trị này: không mở cổng `27017`, `8200`, `9000/9001`, `9002`, `8000/8443` ra mạng ngoài; không tái sử dụng chúng ở môi trường khác. Trước khi demo qua Internet phải đổi toàn bộ, ưu tiên nạp qua biến môi trường/secret file thay vì hard-code.

## 2. Bí mật sinh tại runtime (không bao giờ commit)

| File | Nội dung | Bảo vệ |
|---|---|---|
| `infra/runtime/vault/.lab-init` | Unseal key + initial root token của Vault | gitignored, quyền root 600 |
| `infra/runtime/vault/` | Dữ liệu Vault đã mã hóa (KEK của các tenant) | gitignored |
| `infra/runtime/z1_auth_secrets.json` | Khóa ký JWT và khóa HMAC `record_mac` | gitignored; có thể thay bằng `MEDSHARE_JWT_SECRET`, `MEDSHARE_AUTH_MAC_KEY` |
| `infra/certs/server.key` | Private key chứng chỉ TLS tự ký của Portal | gitignored (`*.key`) |

Nếu một trong các file này lộ: với Vault, coi toàn bộ KEK là đã lộ (khởi tạo lại Vault và nạp lại dữ liệu); với JWT/HMAC, xóa file để sinh khóa mới (mọi phiên đăng nhập bị vô hiệu); với TLS key, xóa `infra/certs/` để `run_portal.sh` sinh lại.

## 3. Không được commit

- Private keys, unseal key, AA master secret (CP-ABE), secret key BFV, KMS material, bearer token, cookie/session, mật khẩu thật và credential files.
- `.env`, dump/backup DB, nội dung `infra/runtime/`, raw request/response hoặc log chứa plaintext/khóa.
- Dataset sinh ra, oracle, `benchmarks/results/`, `evidence/runs/` và tệp y tế mẫu (`datasets/samples/raw/*`, trừ `manifest.json`) chưa rà soát.

Không dùng `git add -f` để bỏ qua `.gitignore`. File đã track không được bảo vệ chỉ bằng việc thêm vào `.gitignore`. Trước mỗi lần push, kiểm tra `git diff --cached --stat` và nội dung diff.

## 4. Giới hạn bảo mật đã biết của bản lab

- **Kênh nội bộ chưa mã hóa:** Gateway ↔ Vault/MinIO/CP-ABE worker dùng HTTP, chưa có mTLS. Kế hoạch và đánh giá: `plan-mTLS.md`, `TIEN_DO_HIEN_TAI.md` mục 7.
- **Vault seal không bảo vệ volume:** unseal key nằm cùng volume để tự mở khóa khi khởi động. Ai có `infra/runtime/vault/` sẽ mở được KEK. Môi trường thật cần auto-unseal qua HSM/Cloud KMS.
- **Chứng chỉ Portal tự ký** (RSA-2048): trình duyệt cảnh báo; không có pinning.
- **JWT HS256 dùng khóa đối xứng** do Gateway giữ; không tách IdP độc lập.
- **Dữ liệu demo tự seed** khi import `gateway/api.py`; chỉ phù hợp lab.
- **Rò rỉ có chủ đích:** blind index lộ equality/frequency pattern (đo ở E5); BFV không bảo vệ tính đúng của kết quả trước worker độc hại (TC-19); CP-ABE không thu hồi được dữ liệu đã giải mã offline (TC-14).
- **Chưa có:** PQC migration (E8), xoay vòng khóa có crash-recovery (E9), audit witness độc lập Z3.

## 5. Khi phát hiện lộ secret

Ngừng chia sẻ artifact, báo trực tiếp partner/giảng viên qua kênh riêng, **thu hồi/rotate credential trước**, không dán secret vào issue/PR. Xóa file ở commit mới không xóa lịch sử Git; với repo công khai, coi secret đã lộ ngay cả khi viết lại lịch sử. Viết lại lịch sử cần thống nhất với cộng tác viên.

## 6. Báo lỗi bảo mật

Chưa cấu hình email tiếp nhận riêng. Liên hệ nhóm qua kênh riêng đã thống nhất hoặc GitHub private vulnerability reporting (nếu chủ repo bật); không mở issue công khai kèm exploit hoặc thông tin truy cập lab.

## 7. Quyền chia sẻ và license

Repository có file `LICENSE` (Apache-2.0) được tạo khi khởi tạo repo trên GitHub. License này chỉ có thể áp dụng cho phần mã và tài liệu do nhóm viết. Tài liệu học phần (`docs/requirements/course-guideline.md`, `docs/requirements/topic-18.md`), mã tham khảo bên thứ ba và tên/mã học viên trong proposal **cần nhóm xác nhận quyền chia sẻ công khai**.
