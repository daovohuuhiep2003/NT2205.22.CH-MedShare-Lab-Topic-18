# Kế hoạch mTLS nội bộ + định danh SPIFFE — v2.0

> **Trạng thái:** ĐỀ XUẤT – CHƯA TRIỂN KHAI (viết lại 24/11/2026). Bản v1 (PKI ML-DSA toàn hệ thống, Public Edge InfinityFree/ZeroSSL, Envoy Ingress) nằm trong lịch sử Git và **không triển khai được trên stack hiện tại**. Lý do và các lỗi của v1: xem mục 8 và `TIEN_DO_HIEN_TAI.md` mục 7.
>
> **Liên kết:** cơ chế M-12 trong `docs/design/crypto-and-protocol-design.md`; threat T-11; yêu cầu SR-15; test TC-20 trong `docs/testing/experiments-and-validation.md`; ADR-0004 (proposed) trong `docs/adr/README.md`.

## 1. Mục tiêu và phạm vi

**Vấn đề:** Gateway (Zone Z1, chạy trên host) gọi Vault KMS, MinIO và CP-ABE worker bằng **HTTP không mã hóa, không xác thực lẫn nhau**. Bất kỳ tiến trình nào vào được mạng Docker/host đều có thể:
- nghe lén DEK đã unwrap trên đường từ Vault về;
- giả mạo abe-worker hoặc MinIO;
- dùng token Vault đã lộ từ bất kỳ đâu.

**Mục tiêu:** mỗi kết nối nội bộ phải là mTLS. Hai phía kiểm tra chứng chỉ do CA nội bộ cấp **và** kiểm tra **SPIFFE ID** của phía kia, không chỉ kiểm tra hostname.

| Trong phạm vi | Ngoài phạm vi (lý do) |
|---|---|
| Gateway ↔ Vault (`:8200`) | Kết nối Gateway ↔ MongoDB — chỉ chở ciphertext; làm sau nếu còn thời gian |
| Gateway ↔ MinIO (`:9000`) | Public Edge / tên miền công khai — hoãn (mục 7) |
| Gateway ↔ abe-worker (`:9002`) | HE và PQC worker — là CLI, không có kết nối mạng |
| Inventory thuật toán TLS (M-12) | Chứng chỉ ML-DSA cho toàn hệ thống — chưa thư viện nào trong stack hỗ trợ (mục 2) |

**Không tuyên bố:** kênh "an toàn hậu lượng tử". Bản này dùng ECDSA P-256 + X25519 cổ điển. Phần PQ chỉ được đo trong thí nghiệm tùy chọn (mục 6).

## 2. Hiện trạng đã kiểm tra (24/11/2026)

| Thành phần | Phiên bản | Chứng chỉ ML-DSA | Trao đổi khóa PQ |
|---|---|---|---|
| Host OpenSSL / Python `ssl` (Gateway) | OpenSSL 3.0.2; không có `SSLContext.set_groups` | Không (cần ≥ 3.5) | Không chọn được nhóm |
| Vault 1.15.6 | Go 1.21.7 | Không | Không |
| MinIO `latest` | Go 1.23.0 | Không | `X25519Kyber768Draft00` (bản draft, không phải ML-KEM FIPS 203) |
| abe-worker (Uvicorn, Python 3.10, Ubuntu 22.04) | OpenSSL 3.0.x | Không | Không |

Kết luận: chỉ dùng được **chứng chỉ ECDSA P-256** và trao đổi khóa **X25519**. Mỗi kết nối đều có Gateway (Python 3.0.2) ở một đầu, nên kể cả nâng cấp server thì handshake vẫn là cổ điển.

## 3. Định danh SPIFFE và tên DNS

- Trust domain: `spiffe://medshare.local`. Trust domain không cần phân giải DNS nên không vướng `.local`.
- DNS nội bộ: `*.medshare.internal`. Không dùng `.local` vì đuôi này dành cho mDNS (RFC 6762). Gateway chạy trên host nên cần ánh xạ trong `/etc/hosts` (`127.0.0.1 vault.medshare.internal ...`). Các container dùng `networks: aliases` trong compose.

| Dịch vụ | DNS SAN | SPIFFE ID (URI SAN) | Vai trò TLS |
|---|---|---|---|
| Gateway | — | `spiffe://medshare.local/ns/z1/sa/gateway` | client |
| Vault KMS | `vault.medshare.internal` | `spiffe://medshare.local/ns/z1/sa/vault` | server |
| abe-worker | `abe-worker.medshare.internal` | `spiffe://medshare.local/ns/z1/sa/abe-worker` | server |
| MinIO | `minio.medshare.internal` | `spiffe://medshare.local/ns/z2/sa/minio` | server |

Namespace `z1`/`z2` mã hóa luôn vùng tin cậy vào định danh. Chính sách mặc định: chỉ chấp nhận peer có SPIFFE ID nằm trong allowlist của từng kết nối.

## 4. PKI nội bộ

- **Root CA:** ECDSA P-256, hạn 10 năm, chỉ dùng để ký Intermediate; private key giữ offline (ngoài repo, không mount vào container).
- **Intermediate CA:** ECDSA P-256, hạn 1 năm, `pathlen:0`; dùng để ký SVID.
- **SVID (leaf):** ECDSA P-256, hạn **7 ngày** (lab; SPIRE mặc định khoảng 1 giờ). Extensions bắt buộc:
  - `basicConstraints = critical, CA:FALSE`
  - `keyUsage = critical, digitalSignature`
  - `extendedKeyUsage = serverAuth` (server), `clientAuth` (gateway), hoặc cả hai
  - `subjectAltName = URI:spiffe://..., DNS:<svc>.medshare.internal`
- **Công cụ:** script tĩnh `scripts/gen_mtls_certs.sh` dùng OpenSSL 3.0 có sẵn. Script sinh Root (nếu chưa có), Intermediate và 4 SVID vào `infra/runtime/pki/` (gitignored, quyền 600). Chạy lại script = xoay vòng SVID.
- **Không dùng** cert-manager đọc Docker socket: socket Docker tương đương quyền root trên host. Nếu sau này cần cấp tự động, dùng SPIRE hoặc step-ca.

## 5. Cấu hình từng kết nối

| Kết nối | Phía server | Phía client (Gateway) |
|---|---|---|
| Vault | `infra/vault/config.hcl`: `tls_cert_file`, `tls_key_file`, `tls_client_ca_file`, `tls_require_and_verify_client_cert = true`, `tls_min_version = "tls13"`; `entrypoint.sh` đổi `VAULT_ADDR` sang `https://` kèm `VAULT_CACERT`/`VAULT_CLIENT_CERT` cho các lệnh nội bộ và healthcheck | `VaultKmsClient` (`src/medshare/broker/kms.py`): `session.cert = (crt, key)`, `session.verify = ca_bundle`; kiểm tra SPIFFE ID của peer |
| MinIO | Mount `public.crt`/`private.key` và `CAs/` vào `/root/.minio/certs/`; bật xác thực client cert | `MinioStorage` (`src/medshare/storage/minio_dal.py`): `secure=True`, truyền `http_client` urllib3 `PoolManager(cert_file, key_file, ca_certs)` |
| abe-worker | Uvicorn `--ssl-certfile --ssl-keyfile --ssl-ca-certs --ssl-cert-reqs 2` | `AbeClient` (`src/medshare/crypto/abe_client.py`): `ssl.SSLContext(PROTOCOL_TLS_CLIENT)`, `load_cert_chain`, `load_verify_locations`, `minimum_version = TLSv1_3` |

**Module dùng chung** `src/medshare/transport/mtls.py`, gồm:
- `load_mtls_config()`: đọc biến môi trường `MEDSHARE_MTLS`, `MEDSHARE_PKI_DIR`.
- `build_client_ssl_context()`
- `verify_peer_spiffe_id(peercert, allowed: set[str])`: đọc SAN URI từ `getpeercert()`; nếu không khớp allowlist thì ném lỗi fail-closed.

**Bật/tắt:** `MEDSHARE_MTLS=0` (mặc định) giữ HTTP như hiện tại để 100 test hiện có vẫn chạy được. `MEDSHARE_MTLS=1` thì bắt buộc mTLS, không có fallback âm thầm về HTTP.

**Phía server kiểm tra SPIFFE ID của client:**
- abe-worker: middleware FastAPI đọc `request.scope["transport"].get_extra_info("peercert")`.
- Vault, MinIO: chỉ dựa vào CA nội bộ, vì không cấu hình được allowlist SPIFFE.
- Đây là giới hạn của bản lab và cần ghi rõ: ở Vault và MinIO, mọi chứng chỉ do Intermediate ký đều được chấp nhận, nên phải giữ Intermediate chỉ cấp cho 4 dịch vụ.

## 6. Kiểm thử và đo đạc

Các test sau gắn với **TC-20** (catalog đã có "TLS certificate chain/name/expiry sai"), T-11, SR-15 và M-12. Không tạo mã TC mới vì catalog giữ đúng 30 nhóm.

| Ca | Kịch bản | Kỳ vọng |
|---|---|---|
| TC-20.a | Client không gửi chứng chỉ | Handshake thất bại, TLS alert `certificate_required` (116); không có phản hồi HTTP |
| TC-20.b | Chứng chỉ do CA lạ ký | Handshake thất bại (`unknown_ca`) |
| TC-20.c | **Đúng CA nhưng sai SPIFFE ID** (dùng SVID của abe-worker để gọi Vault qua Gateway) | Gateway từ chối sau handshake, trước khi gửi request |
| TC-20.d | SVID hết hạn / sai DNS SAN | Handshake thất bại |
| TC-20.e | Chứng chỉ và SPIFFE ID đúng | Thành công; toàn bộ 100 test chạy lại với `MEDSHARE_MTLS=1` đều pass |
| TC-20.f | Không chạy lại `gen_mtls_certs.sh` (SVID hết hạn sau 7 ngày) | Fail-closed, không tự fallback về HTTP |

Đo thêm: thời gian handshake p50/p95 cho từng kết nối, mức tăng độ trễ của W1/W2 so với E2. Mọi thứ được đo trên cùng máy và dataset với E2.

**Thí nghiệm tùy chọn (mở rộng E8), không chặn tiến độ chính:**
- Dựng một container nginx build với OpenSSL ≥ 3.5 làm sidecar trước abe-worker.
- Đo handshake cho các tổ hợp {ECDSA P-256, ML-DSA-44, ML-DSA-65} × {X25519, X25519MLKEM768}, ghi kích thước chuỗi chứng chỉ (bytes) và thời gian.
- Client đo là `openssl s_client` 3.5, không phải Gateway Python.
- Kết quả ghi vào inventory M-12 kèm phiên bản Go/OpenSSL của từng thành phần.

## 7. Lộ trình

| Bước | Nội dung | Ước lượng |
|:---:|---|:---:|
| M1 | `scripts/gen_mtls_certs.sh`, PKI Root/Intermediate/SVID, `/etc/hosts` + network aliases | 0,5 ngày |
| M2 | TLS server cho Vault (sửa `config.hcl`, `entrypoint.sh`, healthcheck), MinIO, abe-worker | 1 ngày |
| M3 | `src/medshare/transport/mtls.py` + 3 client + middleware SPIFFE ở abe-worker | 1 ngày |
| M4 | Test TC-20.a → f, chạy lại 100 test với `MEDSHARE_MTLS=1`, cập nhật traceability | 0,5 ngày |
| M5 *(tùy chọn)* | Thí nghiệm sidecar OpenSSL 3.5 (E8 mở rộng) | 1–1,5 ngày |
| — | Public Edge (tên miền công khai + chứng chỉ ACME) | Hoãn |

**Điều kiện nếu sau này cần Public Edge:**
- Dùng **DuckDNS** hoặc một domain riêng + Cloudflare DNS, với `acme.sh --dns dns_duckdns` (DNS-01).
- Chỉ mở cổng 443 của Portal.
- **Đổi toàn bộ mật khẩu/token mặc định trước** (xem `SECURITY.md` mục 1).
- Cipher suite kỳ vọng là `TLS_AES_256_GCM_SHA384` hoặc `TLS_AES_128_GCM_SHA256` (TLS 1.3).

## 8. Lỗi của bản v1 đã được sửa

| v1 | Vấn đề | v2 |
|---|---|---|
| PKI ML-DSA-44/65 cho mọi dịch vụ | Không thành phần nào trong stack hỗ trợ (mục 2) | ECDSA P-256; ML-DSA chỉ đo ở M5 |
| "Bảo vệ tuyệt đối trước máy tính lượng tử" | ML-DSA chỉ xác thực; mối đe dọa harvest-now-decrypt-later nằm ở trao đổi khóa | Không claim PQ; đo hybrid KEM ở M5 |
| Chữ ký ML-DSA-65 = 3.293 bytes | FIPS 204: **3.309 bytes** (3.293 là Dilithium3 bản round 3) | Dùng số FIPS 204 trong M5 |
| InfinityFree + `dns_infinityfree` | InfinityFree không cho trỏ bản ghi về IP lab; `acme.sh` không có plugin này | Hoãn; nếu làm thì dùng DuckDNS |
| Ingress ↔ MinIO trực tiếp | Phá phân vùng: MinIO thuộc Z2, chỉ Gateway Z1 được gọi tới | Chỉ Gateway gọi MinIO |
| `*.medshare.local` làm DNS | `.local` dành cho mDNS | `*.medshare.internal` |
| `pqc-cert-manager` đọc Docker socket | Tương đương quyền root trên host | Script tĩnh; SPIRE/step-ca nếu cần tự động |
| Cert không có KU/EKU/basicConstraints, Root ký trực tiếp leaf, hạn 90 ngày | PKI yếu | Root offline + Intermediate, đủ extensions, hạn 7 ngày |
| Envoy `match_typed_subject_alt_names` thiếu `san_type: URI` | Không khớp được SPIFFE ID | Bỏ Envoy; kiểm tra SPIFFE ID bằng code |
| TC-PQC-01: `ECDHE-ECDSA-AES256-GCM-SHA384` | Đây là cipher suite TLS 1.2 | Cipher suite TLS 1.3 (mục 7) |
| TC-PQC-04: "HTTP 403" khi thiếu cert | Handshake thất bại thì không có HTTP; TLS 1.3 trả alert 116 | TC-20.a |
| Không có test đúng CA nhưng sai SPIFFE ID | Đây là test cốt lõi của SPIFFE | TC-20.c |
| "he-worker" là dịch vụ mạng | HE worker là CLI | Ngoài phạm vi |
| Mâu thuẫn M-12 ("không tự có PQ TLS") | Thiếu ADR | ADR-0004 (proposed) |
