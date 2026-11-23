# Detailed project implementation
## Kế hoạch triển khai chi tiết Topic 18 — bậc thạc sĩ

**Phiên bản thiết kế:** 1.1 — đồng bộ phạm vi và repository ngày 16/09/2026. **Trạng thái (23/11/2026):** WP1–WP8 và WP10 đã triển khai, E1/E2/E3/E4/E5/E7 đã chạy; WP9 (E8/E9) là việc của Tuần 11. Tiến độ: [TIEN_DO_HIEN_TAI.md](../../TIEN_DO_HIEN_TAI.md); quyết định lệch thiết kế: [ADR](../adr/README.md).  
**Căn cứ:** hai tài liệu nguồn đã đọc đầy đủ; xem [phân tích nguồn và rubric](../requirements/source-analysis.md).  
**Bản đăng ký:** [project proposal](../proposal/project-proposal.md).

> Không bắt đầu bằng cài thư viện AES/ABE/PQC. Hoàn tất system model, asset, threat, SR và ranh giới tin cậy trước. Các thư viện, endpoint và các module/API bên dưới là **contracts dự kiến cần xây dựng**, không phải API đang tồn tại trong workspace. Không có số liệu benchmark hoặc kết quả security test đã được xác nhận.

## 0. Bản đồ tài liệu và cách bắt đầu

| Tài liệu | Dùng để làm gì |
|---|---|
| File này | Hướng dẫn system → assets → threats → SR → architecture → CR → mechanisms → implementation → testing → evaluation |
| [Crypto và protocol design](../design/crypto-and-protocol-design.md) | Format envelope, AAD, key hierarchy, CP-ABE, BFV, PQC, lifecycle và failure behavior |
| [Experiments and validation](../testing/experiments-and-validation.md) | E1–E9 đã chọn, TC-01–TC-30, workload, oracle, leakage/inference và thống kê |
| [Traceability matrix](../testing/traceability-matrix.md) | Threat → SR → CR → mechanism → module → test → evidence |
| [Source analysis](../requirements/source-analysis.md) | Phân tích từng file, yêu cầu Master, rubric và primary references |
| [Architecture](../diagrams/architecture.mmd), [DFD](../diagrams/data-flows.mmd) | Sơ đồ nguồn Mermaid có miền tin cậy và F0–F9 |
| [Read sequence](../diagrams/read-sequence.mmd), [key hierarchy](../diagrams/key-hierarchy.mmd), [rotation](../diagrams/rotation-state.mmd) | Thứ tự xác thực, cấp khóa và trạng thái vận hành |

**Ba hành động đầu tiên khi bắt tay vào đồ án:** (1) phê duyệt use cases/trust model và lập SR; (2) chạy feasibility spike cho CP-ABE, BFV, ML-KEM/ML-DSA trên runtime cô lập; (3) tạo synthetic generator và plaintext oracle trước khi viết field encryption. Chưa tạo UI, cluster Kubernetes hoặc tự viết primitive.

### 0.1 Phạm vi chốt và ngân sách công sức

- Nhóm 2 học viên, 12 tuần; dự trù 36–44 giờ/tuần cho toàn nhóm, khoảng 432–528 giờ theo proposal. Đây là giả định kế hoạch, chưa phải cam kết được xác nhận. Phân công cụ thể được chốt trong team-work-plan.docx.
- Core P1 chạy trên MongoDB 7.0 (NoSQL Document Store). ABE/HE/PQC là worker/CLI hẹp, không tạo ba ứng dụng web mới.
- Một encrypted equality query, một phép BFV SUM/count, một cấu trúc chia sẻ CP-ABE, một quy trình PQ migration. Không cần full FHE.
- 8 experiments: E1, E2, E3, E4, E5, E7, E8, E9. Không làm E6 TEE vì không giả định có hardware/attestation; BFV đáp ứng advanced query của Master.
- Máy đề xuất 8 logical CPU, RAM 32 GB, 60 GB đĩa lab. Với 16 GB: chạy profile tuần tự và dùng 10k main dataset. Không cài hoặc chạy job dài trên máy hiện tại chỉ để viết proposal.
- Cắt trước khi thiếu thời gian: UI, scale 100k, nhiều mẫu policy, advanced range/text, hybrid KEM tùy chọn. Không âm thầm bỏ ABE, HE, leakage hoặc PQ migration mà vẫn gọi là hoàn tất scope Master.

## 1. System Analysis — Phân tích nghiệp vụ và trust model

### 1.1 Hệ thống cụ thể

Tên làm việc: **MedShare-Lab** — bảo vệ hồ sơ y tế đa tenant trên Cloud DBMS. Đây không phải phần mềm khám chữa bệnh production. Dữ liệu là synthetic, không cần dữ liệu bệnh nhân thật.

| Use case | Chủ thể | Đầu vào/đầu ra | Điều kiện nghiệp vụ |
|---|---|---|---|
| UC-01 tạo/cập nhật hồ sơ | Doctor/data-entry theo phân quyền | PII/clinical fields → record version mới | Đúng tenant, field write permission, expected version |
| UC-02 xem hồ sơ | Doctor/nurse/registrar | Record ID → field projection được phép | Phân công chăm sóc, role/dept, purpose ticket, time |
| UC-03 equality search | Doctor/registrar theo field | Giá trị chuẩn hóa → danh sách candidate được lọc quyền | Tenant cố định, field được allowlist, giới hạn kết quả |
| UC-04 export/share | Data owner | Tập hồ sơ đã duyệt → encrypted share artifact | Approval, independent share policy và thời hạn |
| UC-05 aggregate | Analyst | Cohort đã duyệt → SUM/count | Không mặc định cấp quyền đọc từng record; giới hạn truy vấn lặp |
| UC-06 emergency | Doctor đã xác thực | Incident ticket → temporary field scope | Phê duyệt/step-up, không có header tự bật emergency |
| UC-07 vận hành | DBA/operator | Backup/restore/replication | Không có quyền decrypt key; restore theo manifest |
| UC-08 quản trị khóa | Key/policy admin | Rotation/revocation plan → version mới | Tách vai trò, review, audit, rollback recovery có kiểm soát |

### 1.2 Miền tin cậy và nơi plaintext xuất hiện

| Zone | Thành phần | Có thể thấy plaintext/secret? | Giả định và tác động compromise |
|---|---|---|---|
| Z0 endpoint | User UI/CLI, recipient SDK | Plaintext được cấp; private key riêng | Bị compromise thì mất dữ liệu đã cấp; không có remote erase tuyệt đối |
| Z1 tổ chức | Trusted Crypto Gateway, PDP, IdP, broker/KMS, registry, AA, HE owner/PQ archiver | Gateway có plaintext; KMS/broker có DEK; AA có master secret | Đây là trusted computing base của từng profile; không nằm dưới quyền DBA cloud |
| Z2 cloud | MongoDB NoSQL, backup/CDC, token index, BFV worker | Metadata, ciphertext, token; không giữ plaintext DEK/private keys | Có thể đọc, copy, sửa, replay, xóa; confidentiality không đồng nghĩa availability |
| Z3 kiểm toán | Append-only audit, checkpoint witness | Metadata tối thiểu, public verification keys | Witness/version registry phải độc lập với quyền rollback của Z2 |

**A-01:** OS/CSPRNG/thư viện tại Z1 và endpoint thực thi đúng; không chứng minh chống host compromise.  
**A-02:** nguồn identity/attributes/approval và trust anchor được provision xác thực.  
**A-03:** quyền DBA không bao gồm root của Z1 hoặc secret của KMS/AA/recipient.  
**A-04:** trusted registry/current checkpoint không bị rollback cùng DB cloud.  
**A-05:** plaintext hợp lệ đã đến endpoint có thể bị người nhận sao chép.  
**A-06:** benchmark correctness search/HE dùng server thực thi đúng; khả năng active server trả kết quả thiếu/sai được test và báo cáo riêng.  
**A-07:** lab VM/container dùng phân quyền logic; root máy chủ lab có thể vượt mọi zone.  
**A-08:** không sử dụng secret/dataset production; public reference và software license được kiểm tra trước sử dụng.

**Nhạy cảm với thay đổi giả định:** nếu gateway đặt cùng quyền quản trị với DB, không còn claim chống cloud operator; nếu registry bị rollback, chữ ký hợp lệ của bản cũ không giúp freshness; nếu AA bị chiếm, ABE sharing mất policy confidentiality; nếu cần integrity của HE output trước malicious evaluator, phải thêm verifiable computation hoặc recomputation tin cậy và thay đổi phạm vi.

### 1.3 Luồng F0–F9 và ranh giới

| Flow | Đường đi và dữ liệu | Control và điểm cần đo |
|---|---|---|
| F0 provisioning | Admin/IdP/AA/KMS → service/recipient | Trust anchor, public descriptor, private key qua kênh xác thực; ghi key ID, không log key |
| F1 authentication | User → gateway; service → broker/DB | TLS, issuer/audience/expiry, service identity, nguồn claims |
| F2 authorization | Gateway/broker → PDP + registry | Deny-by-default, authoritative attributes, current policy version |
| F3 write | Gateway plaintext → AEAD envelope → DB | Fresh DEK/nonce, expected AAD, conditional write, no plaintext logs |
| F4 point/equality | Gateway → record ID/token → DB → ciphertext → authorized decrypt | Allowlist query, tenant domain, key release sau quyền, leakage traces |
| F5 range/text | Request → query planner | Core từ chối unsupported; không full scan/decrypt âm thầm |
| F6 aggregate/join | HE owner → encrypted batch → cloud worker → owner | Cohort manifest, BFV sum/count, disclose trust/integrity gap; sensitive join unsupported |
| F7 backup/CDC | DB → backup/replica/change stream | Field ciphertext và token vẫn là metadata nhạy cảm; keys backup riêng |
| F8 lifecycle | Admin → signed plan → broker/registry/DB | New version, CAS, dual-read, stale rejection, revocation boundary |
| F9 audit | Gateway/PDP/broker → audit → independent checkpoint | IDs/hashes/status/latency, không plaintext/token giá trị thấp/secret |

Mở [architecture.mmd](../diagrams/architecture.mmd) và [data-flows.mmd](../diagrams/data-flows.mmd) bằng Mermaid renderer khi viết báo cáo. Sơ đồ là source có thể chỉnh sửa; không có bằng chứng attestation/hardware chỉ từ hình vẽ.

## 2. Assets — Phân loại dữ liệu, khóa và state

### 2.1 Inventory tài sản

| ID | Tài sản | Owner / vị trí | Ưu tiên và yêu cầu |
|---|---|---|---|
| AS-01 | PII name/email/external patient ID | Tenant; Z1/plaintext, Z2/ciphertext | Cao: C/I; chỉ field projection được phép |
| AS-02 | Diagnosis, notes, treatment cost | Tenant; field ciphertext | Rất cao: C/I, clinical role, chống cross-context |
| AS-03 | Tenant/record UUID, dept, sensitivity label, linkage | Tenant/registry; metadata DB + trusted copy | Cao về integrity; disclose linkage/volume leakage |
| AS-04 | Identity, credentials, attributes, assignment/purpose ticket | IdP/attribute source; Z1 | Rất cao: authenticity, expiry, chống self-assertion |
| AS-05 | Policy bundle và emergency approval | Policy admin; PDP/registry | Rất cao: signature, version, least privilege |
| AS-06 | KMS root, tenant/class KEK, wrapped DEK | Key admin/KMS; capsule ở DB | Rất cao: key separation, restricted backup, lifecycle |
| AS-07 | Search keys và token index | Tenant; key ở Z1, token ở Z2 | Cao: chống dictionary không có key; token vẫn lộ mẫu |
| AS-08 | AA master secret, user-bound attribute keys | AA/recipient; không ở DB | Rất cao: không escrow ở cloud; epoch/key issuance audit |
| AS-09 | ML-KEM/ML-DSA/HE private keys và public descriptors | Archive/signing/HE owner | Rất cao: identity binding, key-use separation |
| AS-10 | Nonce, version, manifest hash, migration/replay state | SDK và trusted registry | Rất cao: uniqueness, monotonicity, crash consistency |
| AS-11 | Backups, WAL/oplog/CDC, audit checkpoints | DB ops/auditor | C/I/A theo từng loại, retention và restore consistency |
| AS-12 | Code, build config, test oracle, raw benchmark | Developer/researcher | Integrity/provenance; không ngộ nhận seed dữ liệu là crypto RNG |

C = confidentiality, I = integrity, A = availability. Không xếp mọi asset cùng mức rồi bỏ ưu tiên; AS-04/05/06/08/10 là các điểm compromise có thể lan rộng.

### 2.2 Field protection matrix

| Field | Loại và query need | P1 lưu trữ/protection | Metadata/lưu ý |
|---|---|---|---|
| tenant_id | Routing/equality | Clear pseudonymous ID + AAD + registry | Lộ tenant grouping; không coi là secret tenant name |
| record_id | Point lookup | Random UUID + AAD | Không lấy patient ID thật làm record ID |
| department, classification | Authorization/filter | Label clear được registry xác thực | Có thể lộ chuyên khoa; không tin label từ DB đơn độc |
| external_patient_id | Linkable PII, equality | AEAD + tenant/field HMAC token | Tránh ID thấp entropy trong khuyến nghị cuối |
| name/email | PII; display/equality email | AEAD; chỉ email equality nếu được duyệt | Không prefix/text; normalization theo version |
| diagnosis_code | Clinical categorical | AEAD | Chỉ lập blind index trong leakage experiment riêng để chứng minh rủi ro |
| note | Highly sensitive text | Randomized AEAD | Không full-text search trong core |
| amount_units | Integer confidential, aggregate | AEAD; P3 tạo encrypted BFV snapshot riêng | Không dùng range token hoặc OPE mặc định |
| attachments | Blob nhạy cảm, no query | Ngoài MVP; đề xuất object AEAD/chunked format | Không tải file nhạy cảm thật vào lab |
| object/capsule metadata | Version, suite, policy, key ID | Signed/registry-bound; phần immutable là AAD | Metadata crypto không tự trusted |

Không đưa tên bệnh/PII vào AAD, key ID, log hoặc policy label. Làm padding hay hiding tenant metadata là extension; nếu không làm thì catalogue rõ rò rỉ kích thước/linkage.

### 2.3 Compromise graph và containment

- AS-04 bị sửa → PDP nhận sai role/assignment → broker phát key đúng kỹ thuật nhưng sai nghiệp vụ → AS-01/02 lộ. Bảo vệ attribute source là yêu cầu độc lập, không thể thay bằng AEAD.
- Một DEK lộ → một field-version lộ nếu đúng key granularity. Tenant KEK lộ + tập capsule tương ứng → nhiều field-version lộ. KMS root lộ → nhiều tenant; tách tenant KEK không chống root compromise.
- Search key lộ → đối thủ có thể thử dictionary và map tokens trong domain tương ứng. Không dùng chung search key với DEK/wrap key.
- AA master secret lộ → attacker sinh keys thỏa policy. Giảm blast radius bằng AA research domain riêng, không reuse share DEK với core.
- Signing key lộ → policy/manifest giả có thể được tin. Có quy trình revoke descriptor và minimum accepted key version; chữ ký không bảo vệ khỏi signer độc hại.

## 3. Threat Model — Kịch bản ưu tiên

Chấm risk ban đầu bằng likelihood × impact, mỗi chiều 1–3; đây là ưu tiên định tính phục vụ lab, không phải xác suất thực tế. STRIDE dùng làm checklist, không thay thế mô tả attacker capability.

| ID | Attacker action và asset/flow | L×I | Mục tiêu kiểm chứng |
|---|---|---:|---|
| T-01 | Lấy volume/snapshot/backup, đọc AS-01/02 qua F7 | 3×3 | At-rest vs field confidentiality đúng phạm vi |
| T-02 | Query trực tiếp bằng service role/DBA, bypass F2 | 3×3 | DB policy có thể bị vượt; key boundary còn bảo vệ |
| T-03 | Giả tenant/record/object label/field path trên F2–F4 | 3×3 | Tenant/field isolation, trusted context |
| T-04 | Giả role/purpose/time/emergency/assignment | 3×3 | Identity/attribute source, break-glass kiểm soát |
| T-05 | Sửa ciphertext/tag/AAD hoặc tráo giữa context | 3×3 | AEAD reject, không trả plaintext một phần |
| T-06 | Replay nguyên record/capsule/policy hợp lệ cũ | 2×3 | Freshness ngoài DB; signature đơn lẻ không đủ |
| T-07 | Người bị thu hồi dùng cached key/export cũ | 3×3 | Online deny và giới hạn offline revocation |
| T-08 | Ghép thành phần ABE key của người không đủ quyền | 2×3 | Collusion behavior của đúng implementation |
| T-09 | Frequency/query observation + auxiliary knowledge | 3×2 | Inference và leakage profile, không zero-leakage claim |
| T-10 | Server thêm/bớt/reorder search result hoặc index | 2×3 | Content integrity có giới hạn completeness/freshness |
| T-11 | Thay public key, forged descriptor/policy, MITM | 2×3 | Authenticated key binding và TLS validation |
| T-12 | Downgrade/unknown suite hoặc HNDL qua old wrapper | 2×3 | No silent fallback, inventory weakest decryption path |
| T-13 | Crash/retry/concurrent write trong rotation | 2×3 | Nonce/version safety, CAS/idempotency/recovery |
| T-14 | Lộ key/token/plaintext qua log, file tạm, backup | 2×3 | Non-sensitive artifacts và restricted secret persistence |
| T-15 | Xóa/truncate/replay audit hoặc checkpoint | 2×2 | Independent witness, continuity và limits |
| T-16 | PDP/KMS down, input quá lớn/lỗi gây fail-open/DoS | 3×2 | Fail closed, quotas/timeouts, availability limits |
| T-17 | HE worker trả ciphertext sai hoặc cohort không đúng | 2×3 | Exactness under honest compute; integrity gap trước malicious compute |
| T-18 | Build/dependency/config sai làm vô hiệu thiết kế | 2×3 | Version/parameter pin, provenance, tests và security review |

Mô hình M0 = offline storage thief; M1 = honest-but-curious DB và người dùng trái quyền; M2 = active storage/network attacker; M3 = revoked/colluding recipients; M4 = future quantum attacker. Không sử dụng kết quả M1 để suy ra toàn bộ bảo đảm M2/M4.

## 4. Security Requirements — SR có điều kiện và oracle

| Mã | Yêu cầu bắt buộc trong scope | Điều kiện kiểm chứng và giới hạn |
|---|---|---|
| SR-01 | P1/P2/P4 không lưu plaintext field nhạy cảm ở Z2 | DB/snapshot không có keys; TC-02/08/10; không nói B0/B1 chống DBA |
| SR-02 | Tenant/record/field isolation trên API và key release | Sai scope bị deny trước unwrap; direct DB ciphertext access không phải quyền decrypt |
| SR-03 | Role/dept/assignment/action chỉ từ nguồn được xác thực | Không false permit trong policy suite; client body không override claims |
| SR-04 | Purpose/time/emergency được kiểm soát theo workflow | Deny invalid/expired approval; audit mọi break-glass; không chứng minh ý định thật |
| SR-05 | Reject modified/misbound data trước trả plaintext | Trusted expected AAD + AEAD verify; mọi dimension mutation có test |
| SR-06 | Online path không nhận record/capsule/policy cũ hơn current registry | Replay cả envelope hợp lệ phải reject; mất registry độc lập thì claim không còn |
| SR-07 | Thu hồi chặn key release online tiếp theo theo epoch hiện hành | Cache decision/key tối đa 0 trong profile kiểm thử; cấp khóa đang hoàn tất là điểm tuyến tính hóa; offline historical access là residual |
| SR-08 | P2 chỉ key đủ policy mới phục hồi share DEK | Collusion test với user-bound keys; không giả định union attr là keygen hợp lệ |
| SR-09 | Equality kết quả đúng trên honest execution, leakage tường minh | Oracle normalized equality; metrics inference; không cam kết active-server completeness |
| SR-10 | P3 worker không có HE secret key và SUM/count đúng miền số | BFV bounded exactness; computation authenticity không nằm trong HE primitive |
| SR-11 | Key hierarchy/lifecycle có containment và recovery | Keys riêng theo chức năng/tenant/class; rotate/restore tests, escrow và retention tường minh |
| SR-12 | PQ profile và migration authenticated, versioned, no implicit fallback | Reject unknown/retired suites; PQ claim chỉ cho đường không còn wrapper yếu và assumptions đúng |
| SR-13 | Audit không lộ secret và phát hiện sửa checkpoint có witness | Metadata-only, tamper/truncate/replay tests; logger bị chiếm trước ghi có thể nói dối |
| SR-14 | Lỗi/input bất hợp lệ/dependency outage không làm lộ dữ liệu hoặc fail-open | Error chung, size limits, timeouts, no plaintext on tag failure |
| SR-15 | Entity/public key/policy nguồn được xác thực trước dùng | TLS/cert/issuer/audience/key descriptor validation; reject forged/expired artifacts |
| SR-16 | Backup/replica/CDC giữ đúng bảo vệ và restore nhất quán | Field ciphertext xuyên F7; protected key backup riêng; reconcile current registry |
| SR-17 | Kết quả nghiên cứu tái lập và không trộn expected với observed | Versioned dataset/query seeds, raw logs, CI, manifest, oracle độc lập |
| SR-18 | Dependency/API/parameters được kiểm chứng trước claim | Build/KAT/negative tests, license/advisory review, không production/FIPS certification claim |

Các yêu cầu freshness, audit và backup cần control trạng thái/quản trị ngoài mật mã. Nếu SR không cần primitive riêng, ghi rõ “control phi mật mã”, không ép gắn một thuật toán cho đẹp ma trận.

## 5. Security Architecture — Placement và quyết định

### 5.1 Cấu hình bảo vệ

| Profile | Boundary và cơ chế | Dữ liệu/thí nghiệm |
|---|---|---|
| B0 | Plain MongoDB trong lab isolated | Oracle và baseline, không production |
| B1 | MongoDB trên encrypted lab volume, keys tách snapshot | At-rest E1; engine vẫn thấy plaintext |
| P1 | Trusted gateway field AEAD + KMS/broker + ABAC; equality token tùy workload | Core E2/E3/E5/E9 trên MongoDB NoSQL |
| P2 | Encrypted export với independent share DEK wrapped bởi CP-ABE | E4/E9, recipient decrypt ngoài broker; online ABAC chỉ kiểm soát download |
| P3 | Independent authorized aggregate snapshot, BFV inputs, owner giữ key | E7, SUM/count; không dùng P1 DEK làm HE key |
| P4 | Independent archive capsule với ML-KEM/KDF/AEAD và signed manifest | E8/E9; dữ liệu archive riêng để tránh alternate classical decrypt path |

B1 là baseline cần triển khai thật: đề xuất dedicated encrypted virtual disk trong Linux VM với volume encryption; không format ổ người dùng. Tài liệu này không cung cấp lệnh phá hủy disk. Trong thực hiện, tạo và xác nhận đúng lab disk, kiểm tra mount/key separation rồi mới thao tác. Volume encryption không mã hóa logical dump xuất ra nơi khác.

### 5.2 ABAC policy model

Subject: sub, tenant, role, department, clearance, active status, assignment; Object: tenant, record ID, field class, department, sensitivity, version; Action: READ_FIELD/WRITE_FIELD/SEARCH/EXPORT/DECRYPT/AGGREGATE/ROTATE; Environment: server time, authenticated workflow purpose, incident approval, device/session assurance nếu có nguồn thật.

**Rule precedence:** explicit deny → default deny → permit khi đầy đủ điều kiện. Break-glass không vượt tenant hoặc cho phép bulk export/key administration; chỉ mở một tập clinical field trong thời hạn approval và ghi audit trước release. Thời gian lấy từ server đáng tin; tests dùng clock injection, không sửa đồng hồ máy thật.

| Role | Quyền thường | Không mặc định có |
|---|---|---|
| Doctor | Assigned clinical read/write đúng khoa, treatment workflow | Cross-tenant, bulk export, key admin |
| Nurse | Assigned limited clinical read | Financial details, full note write, export |
| Registrar | PII/admin fields trong tenant | Diagnosis/note |
| Analyst | Approved aggregate cohort | Raw patient fields/DEKs |
| Data owner | Approve share/export dataset | AA master secret/KMS root tự động |
| DBA | Ciphertext backup/index/maintenance | DECRYPT hoặc identity/attribute edit |
| Auditor | Decision/key-use metadata | Clinical plaintext/private keys |

PDP không tin object attributes do cloud DB cung cấp một mình. Gateway lấy object label/version từ trusted registry, hoặc manifest có signature + latest digest. Broker tự xác thực identity/request context, đọc current version và đánh giá quyền; không chấp nhận cờ permit từ gateway như một chứng cứ đủ.

### 5.3 NoSQL Storage: thực thi và kiểm thử bypass DBA

- MongoDB: dùng tenant-scoped collection/documents và role tương ứng; document schema validator không là authorization. Tenant filter do middleware không chống bypass DBA trực tiếp.
- Test hai cấp direct query: least-privileged service role và privileged DBA. P1 cho DBA thấy toàn bộ document ciphertext và tokens; đó không phải failure SR-01. Nếu thấy plaintext hoặc nhận DEK không qua quyền mới là failure.
- Cloud metadata có thể bị sửa: registry/capsule hash bảo vệ accepted object, nhưng index deletion hoặc DB omitting rows chưa có completeness proof. Không đánh đồng record AEAD integrity với integrity của toàn bộ kết quả truy vấn.

## 6. Cryptographic Requirements — Thuộc tính trước primitive

| CR | Thuộc tính cần có | SR nguồn / phạm vi |
|---|---|---|
| CR-01 | Authenticated confidentiality, key secrecy theo threat model | SR-01/05/11/16; AEAD dưới nonce discipline |
| CR-02 | Cryptographic context binding và domain separation | SR-02/05/11; data vs capsule context, tenant/field/version |
| CR-03 | Unforgeability và identity/public-key binding | SR-03/04/12/13/15; signatures/channels + trusted provisioning |
| CR-04 | Integrity của state và chống replay bằng current-state validation | SR-06/07/12/16; stateful control, không chỉ crypto |
| CR-05 | Entropy, nonce uniqueness, KDF key separation | SR-01/05/11/14; CSPRNG và collision/retry handling |
| CR-06 | CP-ABE policy confidentiality và user-key collusion resistance | SR-08; đúng assumptions/security notion của scheme đã chọn |
| CR-07 | Search token PRF với leakage function công bố | SR-09; không forward/backward-private dynamic SSE |
| CR-08 | HE semantic confidentiality và bounded homomorphic correctness | SR-10; không bảo đảm malicious result authenticity |
| CR-09 | PQ KEM shared-secret security + KDF/DEM composition | SR-12; authenticated recipient descriptor; HNDL scope |
| CR-10 | Authentic audit chain/manifest và external checkpoint binding | SR-13/16; append-only operational controls |
| CR-11 | Key version/lifetime/recovery/retirement constraints | SR-07/11/12/16; escrow và irreversible disclosure limits |
| CR-12 | Safe implementation/validation of cryptographic APIs | SR-14/17/18; KAT, parser bounds, error behavior, parameters |

Mức bảo mật không cộng dồn. AES-256 và category-3 PQC không nâng pairing demo lên 128-bit hay biến toàn bộ thiết kế thành category 3. Ghi assumptions, scheme version, group/parameter set, security notion (ví dụ CPA/CCA/PRF/EUF-CMA) đúng từng thành phần; không tự khẳng định construction nghiên cứu đạt CCA nếu tài liệu chỉ chứng minh CPA.

## 7. Cryptographic Mechanisms — Thiết kế chi tiết và alternatives

Đọc [crypto-and-protocol-design](../design/crypto-and-protocol-design.md) trước viết crypto code. Đây là đặc tả bắt buộc cho envelope, state và adapter, không chỉ một bài tổng quan thuật toán.

| Lựa chọn | Rationale xuất phát từ yêu cầu | Alternative và lý do không chọn làm core |
|---|---|---|
| AES-256-GCM, DEK mới mỗi field-value/version | CR-01/02/05, API AEAD phổ biến; blast radius rõ | Shared tenant DEK nhanh hơn nhưng nonce/revocation/containment khó hơn; ChaCha20-Poly1305 có thể so nếu thiếu AES acceleration |
| Software KMS + independent broker PEP | SR-02/11, tách DB và key access | HSM/cloud KMS mạnh hơn về vận hành nhưng cần hạ tầng; software KMS không non-exportable trước root |
| ABAC Gateway & Broker PEP | Dynamic access cần subject/object/action/environment | RBAC đơn thuần thiếu purpose/time; m-NGAC chỉ related work, không giả có sẵn |
| HMAC blind index equality | CR-07, implementation logic trên MongoDB và đo leakage trực tiếp | MongoDB QE production equality/range là alternative có model/library riêng; không đồng nhất với blind index |
| CP-ABE research adapter | CR-06, durable one-to-many share condition | RBAC online không bảo vệ offline capsule; lattice ABE chưa drop-in standardized |
| BFV exact integer SUM | CR-08, đáp ứng Master advanced query không cần attestation | CKKS phù hợp xấp xỉ nhưng không cần ở bài này; TEE thêm hardware/TCB |
| ML-KEM-768, HKDF-SHA-256, AES-GCM; ML-DSA-65 | CR-03/09, standardized key/signature track | Không dùng KEM để mã hóa bulk; không tự xây hybrid combiner như chuẩn |

Không thêm SLH-DSA/HQC vào implementation chỉ để tăng số thuật toán. Survey nêu trạng thái và kiểm tra source lúc nộp; không coi PQ ABE là NIST-certified. Thư viện hỗ trợ thuật toán FIPS không đồng nghĩa module được FIPS 140 validation.

## 8. Implementation — Backlog kỹ thuật và contracts

### 8.1 Stack và feasibility gate

| Module dự kiến | Công nghệ ứng viên | Gate trước sử dụng |
|---|---|---|
| Gateway/SDK/test harness | Python supported stable runtime, web framework nhẹ, pytest | AEAD API tồn tại, bytes serialization, sync/async bounds, supported runtime |
| NoSQL adapter | MongoDB + supported driver | Collection privilege, schema, atomic update, index behavior |
| PDP | OPA/Rego hoặc engine tương đương — **đã chọn:** engine Python tự viết `policy/abac.py` (deny-by-default, bảng quy tắc) | Policy version syntax, table-driven tests, deny on parse/error |
| KMS | Vault Transit hoặc software KMS đã có authenticated wrap/context — **đã chọn:** Vault 1.15.6 Transit `derived: true`, file storage ([ADR-0003](../adr/0003-vault-persistent-lab-unseal.md)) | TLS/auth/persistence, backup, key versions, no root token in app; nếu mock phải ghi mock |
| CP-ABE | Charm CPabe_BSW07 candidate, isolated Linux container — **đã chọn:** AC17 BN254/SS512 ([ADR-0002](../adr/0002-cpabe-ac17.md)) | Build + documented scheme/group/security profile; không dùng SS512 ví dụ như production level |
| PQC | liboqs qua adapter hoặc library có final ML-KEM/ML-DSA | Đúng final algorithm IDs, test vectors, version/license, API validation |
| HE | Microsoft SEAL C++ BFV worker | Build examples, parameter security check, serialization validation |
| Infra | Compose trong Linux VM/WSL2, dedicated encrypted lab disk | Health checks, identities/network separation, exact volume target và recovery |

Không dùng Python của máy hiện tại làm ràng buộc phiên bản CP-ABE; container riêng tránh dependency cũ làm hỏng core runtime. Pin release/commit/digest, compiler flags và parameter profile **sau build thử**, bằng package manager/lock workflow của từng hệ. Không tự viết lại primitives nếu thư viện build khó.

Gate cuối tuần 2: mỗi advanced worker chạy một positive và một negative test thật; nếu không, chuyển sang runtime/library tương thích có ghi ADR. Nếu vẫn không khả thi, đánh dấu branch bị chặn; một mock không thay thế experiment bắt buộc.

### 8.2 Schema logic cần triển khai

| Entity | Trường chính | Constraint / boundary |
|---|---|---|
| records | tenant_id, record_id, department, classification, current_data_version | Composite tenant/record identity; labels được registry xác thực |
| encrypted_fields | tenant_id, record_id, field_id, data_version, envelope_bytes, capsule_id | Unique identity/version/field; envelope bytes không tự trusted |
| key_capsules | capsule_id, capsule_version, suite_id, wrapped_key, key_id, wrap_context, manifest_signature | Latest digest/version ở Z1; parser bounded; không plaintext key |
| search_index | tenant_id, field_name, search_epoch, token, record_id | Compound index theo query; không cross-tenant token reuse |
| trusted_objects | tenant/record, current_version, label digest, field/capsule manifest | **Store riêng Z1**, không cùng credential/backup rollback với DB |
| policy_registry | bundle_version, minimum_version, descriptor digest, approvals | Signed update; authoritative attributes có revision |
| migration_jobs | job_id, signed plan, old/new version, per-item state, counters | Idempotent, CAS, write-ahead status; không log DEK |
| audit_events | event_id, correlation_id, actor pseudonym, action, resource class, decision, key/policy version, error category | Không PII/token/key; trusted append + checkpoint |

MongoDB tổ chức thành các collection: `encrypted_patients` chứa các field envelopes và capsule references, `key_capsules` lưu các wrapped DEK, và `search_index` phục vụ blind index. Dùng canonical envelope bytes chuẩn RFC 8785 (JCS). Report document và index overhead chi tiết.

### 8.3 Hợp đồng API dự kiến

| Endpoint/operation | Input cần xác minh | Output/lỗi và invariant |
|---|---|---|
| POST /records | Identity, workflow purpose, allowed field map, tenant từ identity | Record ID/version; server tự tạo cryptographic state |
| GET /records/{id} | Allowed field list, authoritative tenant, current version | Chỉ fields được cấp; generic not-found/denied theo policy chống enumeration |
| PATCH /records/{id} | Expected version, writable field set, idempotency ID | CAS; conflict trả 409, không reuse encryption under ambiguous state |
| POST /search/equality | Field allowlist, normalized typed value, result limit | Authorized matched records; unsupported operator trả 422 |
| POST /shares | Approved dataset manifest + static ABE policy | Independent P2 artifact; không gửi share DEK qua API public |
| POST /aggregates/sum | Approved cohort ID, amount field, allowed threshold | Job/result reference; HE owner decrypt ở trusted side, không arbitrary decrypt oracle |
| POST /key-requests | Authenticated subject/action/resource + expected manifest | Broker kiểm tra lại PDP/registry; key chỉ trên restricted internal channel |
| POST /migrations | Signed approved plan, allowed old/new suite IDs | Job ID/progress; no arbitrary algorithm string fallback |
| GET /audit/checkpoints | Auditor identity, checkpoint range | Metadata và public verification material; không log raw clinical request |

Các endpoint là **contract cần tạo**, không phải command để chạy ngay. Error categories nội bộ tách AuthDenied, IntegrityFailure, StaleVersion, UnsupportedQuery, InvalidInput, DependencyUnavailable; response ngoài không lộ stack trace, secret hoặc chi tiết oracle giải mã. Sign/verify/decrypt không mở unauthenticated endpoint.

### 8.4 Cấu trúc repository và trạng thái khởi tạo

| Đường dẫn tại repository | Trách nhiệm | Tests cần đi kèm |
|---|---|---|
| infra/ | Compose, networks, identities, lab-volume runbook | health/config isolation |
| src/medshare/gateway/ | Authentication, query planner, field projection | auth/context/unsupported query |
| src/medshare/crypto/ | Envelope/AAD/nonce + adapters | round-trip, tamper, wrong key/context |
| src/medshare/broker/ | Key release, lifecycle, current state | independent PDP, revoke, stale/version |
| src/medshare/policy/ | ABAC rules/attribute resolution | exhaustive policy decision table |
| src/medshare/storage/ | MongoDB Schema/DAL/index | equivalent semantics + bypass |
| workers/abe/, he/, pqc/ | Isolated advanced prototypes | scheme-specific positive/negative |
| datasets/ | Synthetic generator, public seeds/config | determinism and constraints |
| tests/unit/, integration/, security/ | TC implementation | no secret fixture commits |
| benchmarks/ và analysis/ | Workload harness/raw schema/plots | oracle, schema validation, reproducibility |
| evidence/ | Run manifests, redacted metadata, reports | checksum/traceability; actual secrets excluded |
| docs/ | A1–A10, ADRs, threat model, report/runbook | links/ID coverage/diagram checks |

Cập nhật 23/11/2026: các module trên đã có implementation và test (100 tests), trừ `tests/integration/` (chưa có test riêng) và audit checkpoint Z3. API thực tế nằm trong `src/medshare/gateway/api.py` (`/api/v1/...`), khác tên với bảng contract 8.3 ở trên; các endpoint `/migrations` và `/audit/checkpoints` chưa có.

### 8.5 Backlog theo dependency

1. **WP1 — models/oracle:** freeze logical schema, normalization, scope, SR/CR; asset registry và DFD review. Output A1–A7 bản đầu.
2. **WP2 — baseline/harness:** generate seeded datasets, MongoDB load, reference oracle, volume baseline, raw result schema. Chưa benchmark crypto nếu baseline semantics sai.
3. **WP3 — envelope/registry:** AEAD encrypt/decrypt, trusted context, immutable AAD, capsule verification, nonce behavior, version CAS; unit tests trước integration.
4. **WP4 — KMS/broker:** real authenticated software KMS integration, separate identities, wrap/unwrap/context, key inventory, fault paths. Mock chỉ dùng unit tests, không E2 evidence.
5. **WP5 — ABAC/query:** identity claims, policy table, broker recheck, NoSQL scope, field projection, direct-query tests.
6. **WP6 — index/leakage:** HMAC tokens/normalization, query oracle, storage/access trace observer, inference evaluation và mitigation trade-offs.
7. **WP7 — HE:** BFV snapshot/cohort owner, worker SUM/count, input validation, noise/correctness measurement, malicious result limitation.
8. **WP8 — ABE:** static policy parser, key issuance by user, group secret → KDF → share DEK wrap, epoch/reissue, collusion adapter test.
9. **WP10 — Web portal:** lightweight FastAPI + Web UI đa vai trò, ABAC field projection, MinIO upload/view, CP-ABE export, BFV aggregate query, DBA ciphertext-only view.
10. **WP9 — PQ migration + evidence:** final ML-KEM/ML-DSA API, descriptors/signatures, independent archive, migration state machine, old/new rollback tests; full relevant test scope, benchmark CI/sensitivity, audit/backup restore, update traceability and scoped conclusion.

### 8.6 Lịch 12 tuần và Definition of Done

| Tuần | Output định lượng được | DoD |
|---|---|---|
| 1 | UC/assets/DFD + threat list + source/ADR notes | Mọi plaintext/key location xác định; không có thuật toán không gắn nhu cầu |
| 2 | SR/CR, schema, feasibility workers | ABE/HE/PQC build được + positive/negative smoke; scope/parameter risk documented |
| 3 | B0/B1 và oracle trên MongoDB | E1/TC-08, raw format, equivalent results |
| 4 | Core AEAD/serialization/nonce | TC-01/05/24, no partial plaintext on failure |
| 5 | KMS/broker/registry, MongoDB persistence | TC-02/06/09/10, E2; restricted keys outside DB |
| 6 | ABAC + break-glass + bypass | TC-03/04/07/27, E3, policy latency |
| 7 | Equality index, leakage observers | TC-15/16/17, E5, explicit unsupported matrix |
| 8 | BFV aggregate | TC-18/19/30, E7, integer correctness and resource data |
| 9 | CP-ABE share + epoch | TC-11/12/13/14, E4/E9, residual offline test |
| 10 | Web portal đa vai trò (FastAPI + UI) | 5 role views, ABAC field projection, MinIO upload, CP-ABE export button, DBA ciphertext-only |
| 11 | PQ key/signature + rotation + re-test/benchmark/audit | TC-20/21/22/23, E8/E9, TC-25/26/28/29, CI, evidence linked to SR |
| 12 | Technical report/slides/demo/package | A1–A10, traceability filled, reproducible demo on clean lab |

Definition of Done chung: code reviewed ở security-critical path; positive + negative tests pass trong stated scope; no secret in artifact; config/version recorded; document và traceability cập nhật. Một test failure không rõ nguyên nhân không được “sửa” bằng nới oracle cho pass.

## 9. Security Testing — Thực thi và quản lý evidence

Chi tiết nằm trong [experiments-and-validation](../testing/experiments-and-validation.md). Chạy từ unit test nhỏ → integration module → security experiment → benchmark. Lần viết proposal này chỉ kiểm tra tài liệu; **không có application tests để chạy**.

- Negative tests sửa từng dimension độc lập, rồi test các cặp có ý nghĩa: valid ciphertext + wrong trusted context; valid old capsule + old policy; forged subject + direct broker request.
- Differential oracle là plaintext reference code độc lập, không gọi chung helper của implementation để quyết định “expected”. Crypto known-answer tests dùng vector của implementation/chuẩn có nguồn, không tự sinh expected bằng cùng hàm đang test.
- Negative controls cố ý yếu trong isolated test fixture (ví dụ bỏ context check) chỉ dùng để xác nhận test có thể bắt lỗi; không đưa insecure mode vào deployment default.
- Test có expected residual: B1 DBA plaintext, old recipient decrypts old export, malicious HE result không được HE phát hiện, active DB bỏ sót rows. Đây là bằng chứng giới hạn, không phải đạt yêu cầu không thực sự được thiết kế.
- Evidence mỗi run: test ID, source revision, config/parameter profile, dataset/query seed, expected behavior, observed assertion, status, timestamps, artifact digest, limitations. Không dump request/response body/header, env hoặc credentials.
- Bất kỳ fail nào ở confidentiality/authz/integrity scope phải sửa và re-run tests liên quan; benchmark không bù được security failure.

## 10. Evaluation — Từ evidence đến kết luận

### 10.1 Phương pháp đánh giá

1. Kiểm tra query semantics và security gates trước so hiệu năng.
2. Báo cáo theo từng cấu hình/attacker/workload; không xếp hạng mọi profile bằng một điểm tổng vô nghĩa.
3. So paired baseline/protected trong MongoDB NoSQL. Không quy mọi chênh lệch native DB thành overhead crypto.
4. Latency/QPS có raw samples, phân bố, CI và điều kiện warm/cold; phân biệt service-time và end-to-end gồm TLS/PDP/KMS.
5. Leakage có adversary view và inference experiment xác định rõ auxiliary information. Không dùng plaintext ground truth làm input cho attacker.
6. Migration báo thời gian, số capsule/rows touched, failed/retried operations và historical decryptability. “Không re-encrypt payload” không đồng nghĩa đã thu hồi DEK cũ.
7. Security claims lấy từ [traceability matrix](../testing/traceability-matrix.md): verified/partial/not verified, chỉ các điều kiện thực sự có evidence.

### 10.2 Khuyến nghị cuối cần có điều kiện

- Volume encryption phù hợp at-rest baseline, không đủ cho confidentiality trước DBA.
- P1 phù hợp clinical/PII field ít query khi chấp nhận trusted gateway/KMS; gateway compromise vẫn nghiêm trọng.
- Equality blind index chỉ hợp lý với nhu cầu hẹp và leakage chấp thuận; low-entropy clinical categories có thể không nên index sau inference evaluation.
- CP-ABE phù hợp durable share policy nhưng operational revocation đắt và không xóa dữ liệu đã lộ; pairing branch không PQ-safe.
- BFV thích hợp aggregate hẹp; output privacy/completeness/integrity cần control khác, không phải “HE là đủ”.
- PQC key/signature layer có ý nghĩa khi inventory không bỏ qua alternative classical wraps, TLS identity, backup/export và KMS access paths. Không gọi toàn hệ thống hậu lượng tử chỉ dựa E8 microbenchmark.

### 10.3 Report, slides và demo

Báo cáo theo 13 chương của G mục 6: problem/scope → system/trust → assets → threat → SR → architecture → CR → mechanisms → implementation → security tests → evaluation/residual risks → conclusion → appendices. Các mục 1–10 ở file này cung cấp khung nội dung, không copy proposal thay cho results.

| Slide/demo | Nội dung và evidence phải hiện |
|---|---|
| 1–2 | Problem, scope và câu hỏi nghiên cứu; vì sao TDE chưa đủ |
| 3–4 | Architecture/trust boundary, asset dependency và attacker models |
| 5–6 | Một chuỗi threat → SR → CR → mechanism đầy đủ; key/read flow |
| 7–8 | Cấu hình thí nghiệm, query support/leakage, raw measurement method |
| 9–10 | Authz/tamper/revocation evidence và performance/CI thực tế |
| 11 | PQ readiness và residual risks, không overclaim |
| 12 | Workload-specific recommendation và scoped conclusion |

Demo mục tiêu 12 phút: 1 phút scope; 2 phút B1 vs P1 direct DB; 2 phút deny/swap context; 2 phút equality query + leakage trace; 2 phút CP-ABE valid/invalid + epoch; 1 phút BFV SUM; 1 phút PQ migration/downgrade; 1 phút evidence/limitations. Nếu thời lượng bảo vệ ngắn hơn, trình bày ba luồng bắt buộc live và cung cấp log/video nhánh còn lại; không cắt kết luận giới hạn.

### 10.4 Checklist hoàn thành đồ án

- [ ] A1–A7 đã cập nhật theo implementation cuối, không giữ architecture cũ.
- [ ] A8 có source/config/build/run với version thực tế, không chỉ pseudo API.
- [ ] A9 có TC thực thi, expected/observed và negative results trung thực.
- [ ] A10/traceability có evidence links, CI, residual risk và scoped claims.
- [ ] MongoDB NoSQL, CP-ABE revocation, leakage/inference, BFV và PQ migration đều có kết quả hoặc limitation được ghi rõ.
- [ ] MinIO service được bổ sung vào `infra/docker-compose.yml` và health check pass.
- [ ] Attachment write path: 6 pre-commit gates (G-WRITE-01–06) có test case tương ứng.
- [ ] Read permission matrix (§11.3) được ánh xạ vào ABAC policy table và test bằng truth table.
- [ ] Non-text file (binary synthetic) đã qua AEAD chunked encrypt + benchmark overhead ghi nhận.
- [ ] Web portal (lightweight hoặc reference) được mô tả trong báo cáo chương Implementation.
- [ ] Field protection matrix, W1–W10 support matrix và F0–F9 nhất quán.
- [ ] B1 không bị mô tả là chống DBA; P1 không bị mô tả chống gateway root.
- [ ] CP-ABE không mang dynamic purpose/emergency như một bảo đảm offline.
- [ ] HE không bị gọi là authenticated/verifiable computation.
- [ ] PQ wrapper không che khuất alternative classical decrypt path.
- [ ] No secrets/PII thật; audit/benchmark artifacts đã được kiểm tra an toàn.
- [ ] Người khác tái lập demo trong lab sạch theo runbook.

**Nguyên tắc cuối:** hoàn thành tài liệu này không đồng nghĩa hoàn thành đồ án. Bước tiếp theo là thực thi WP1–WP2, cập nhật/viết tests cùng từng module và chạy chúng trước khi đưa bất kỳ claim nào vào báo cáo cuối.

---

## 11. Bổ sung kiến trúc thực tế — Câu hỏi thiết kế mở và quyết định kỹ thuật

> Phần này ghi lại các câu hỏi thiết kế phát sinh từ thực tế triển khai, cùng quyết định và hành động kỹ thuật tương ứng. Không thay thế các phần 1–10; bổ sung chi tiết triển khai cho từng vấn đề cụ thể.

### 11.1 Dữ liệu trên DB: Text (JSON/NoSQL) và Non-text (File)

#### Hiện trạng và vấn đề

| Loại dữ liệu | Hiện tại | Vấn đề |
|---|---|---|
| **Text / JSON** | Lưu trong MongoDB 7.0 dưới dạng BSON Document với `FieldEnvelope` AEAD | ✅ Đã xử lý (WP3–WP4) |
| **Non-text (File nhị phân)** | Chưa xử lý trong scope MVP; mục `attachments` trong field matrix ghi "Ngoài MVP; đề xuất object AEAD/chunked format" | ⚠️ Cần làm rõ chiến lược |

**Dữ liệu non-text y tế điển hình cần lưu:**
- Ảnh X-Quang (DICOM `.dcm`, JPEG, PNG) — dung lượng điển hình 5–50 MB/file
- Film chụp MRI/CT (DICOM series) — có thể lên đến vài GB
- Kết quả siêu âm (video/ảnh DICOM)
- File PDF kết quả xét nghiệm, phiếu xuất viện
- File âm thanh (ghi chú giọng nói bác sĩ)

#### Quyết định kỹ thuật: NoSQL + Object Storage (MinIO S3-compatible)

**Kiến trúc đề xuất:** MongoDB lưu **metadata và text** (JSON document); MinIO lưu **file nhị phân** (object storage).

```
Bệnh nhân record (MongoDB):
{
  "record_id": "uuid",
  "tenant_id": "hospital_a",
  "encrypted_fields": { ... },          ← AEAD envelope (text/JSON)
  "attachments": [
    {
      "attachment_id": "uuid",
      "type": "xray",                    ← metadata (cleartext label)
      "sensitivity": "HIGH",
      "object_key": "hospital_a/patient_uuid/xray_2026_01.dcm.enc",  ← tham chiếu MinIO
      "capsule_id": "kms_capsule_uuid",  ← DEK được bọc trong Vault KMS
      "uploaded_by": "doctor_id",
      "uploaded_at": "ISO8601",
      "content_hash_sha256": "hex",      ← hash của bản rõ để kiểm tra toàn vẹn
      "aead_tag": "base64"               ← GCM tag của toàn bộ file
    }
  ]
}
```

**Quy trình lưu file (write path):**
1. Gateway nhận file binary từ client qua multipart upload
2. ABAC PDP kiểm tra: chủ thể có quyền `WRITE_ATTACHMENT` trên object/tenant tương ứng không
3. **Nếu được phép:** sinh DEK mới (CSPRNG), mã hóa file bằng `AES-256-GCM` chunked (chunk 1 MB) → tạo `FieldEnvelope` file
4. Bọc DEK vào `KeyCapsule` qua Vault KMS (Z1)
5. Upload ciphertext lên MinIO bucket được cấu hình theo `tenant_id`
6. Ghi metadata attachment vào MongoDB document (không lưu DEK plaintext)
7. Ghi audit event vào Z3

**MinIO bucket policy:** mỗi tenant có bucket riêng (`medshare-{tenant_id}`); service account MinIO chỉ được phép read/write bucket của tenant mình; không có public read.

**Tham chiếu thêm vào field protection matrix:**

| Field | Loại | Protection |
|---|---|---|
| `attachments[].object_key` | Object storage path (non-sensitive prefix + UUID) | Cleartext reference; không embed PII vào path |
| `attachments[].capsule_id` | Reference DEK capsule trong Z1 | Non-sensitive ID |
| File object trong MinIO | Binary blob — X-Quang, MRI, siêu âm, PDF | AEAD chunked encrypt; DEK trong KMS capsule |

**Stack bổ sung vào infra:**
```yaml
# infra/docker-compose.yml — thêm service MinIO
medshare-minio:
  image: minio/minio:RELEASE.2024-01-01T00-00-00Z   # pin release
  environment:
    MINIO_ROOT_USER: medshare_admin
    MINIO_ROOT_PASSWORD: "<secret từ .env, không commit>"
  command: server /data --console-address ":9001"
  ports:
    - "9000:9000"   # S3 API
    - "9001:9001"   # Web console
  volumes:
    - ./infra/runtime/minio:/data
  healthcheck:
    test: ["CMD", "mc", "ready", "local"]
```

**Lưu ý scope lab:** Trong phạm vi đồ án, **không upload ảnh X-Quang thật**. Dùng file binary synthetic (random bytes có kích thước mô phỏng ~5 MB) để đo overhead mã hóa/upload. Không lưu DICOM thật, PII thật vào lab.

---

### 11.2 Chính sách lưu trữ (Data Persistence Policy) — Khi nào dữ liệu được lưu?

**Vấn đề:** Không phải mọi dữ liệu được upload đều nên được lưu vĩnh viễn. Cần có cơ chế kiểm soát rõ ràng khi nào dữ liệu được commit vào storage.

#### Các điều kiện trước khi lưu (Pre-commit Gates)

| Gate | Điều kiện bắt buộc | Xử lý khi fail |
|---|---|---|
| **G-WRITE-01: Xác thực danh tính** | JWT/token hợp lệ, issuer đúng, không hết hạn | Trả 401; không lưu |
| **G-WRITE-02: Kiểm tra quyền ABAC** | Chủ thể có quyền `WRITE_FIELD` / `WRITE_ATTACHMENT` theo role/dept/tenant | Trả 403; không lưu |
| **G-WRITE-03: Kiểm tra toàn vẹn dữ liệu đầu vào** | Payload đúng format, không vượt size limit (text ≤ 1 MB/field, file ≤ 50 MB), content-type hợp lệ | Trả 422; không lưu |
| **G-WRITE-04: DEK sinh và bọc thành công** | Vault KMS respond OK và trả capsule hợp lệ | Nếu KMS lỗi → abort toàn bộ giao dịch; không lưu ciphertext mồ côi |
| **G-WRITE-05: Idempotency check** | Kiểm tra `idempotency_id` (header `X-Idempotency-Key`) chưa tồn tại trong window 24h | Nếu trùng → trả kết quả của lần đầu; không lưu lại |
| **G-WRITE-06: Version conflict check** | `expected_version` trong request khớp với `current_version` trong registry (CAS) | Trả 409 Conflict; client phải fetch version mới rồi retry |

#### Các trường hợp KHÔNG lưu

- Upload file từ thiết bị **không được xác thực** (device/session assurance fail)
- Bác sĩ **chưa được phân công** cho bệnh nhân đó (assignment check fail)
- Dữ liệu đến trong **emergency break-glass** nhưng ticket đã hết hạn hoặc chưa được duyệt
- Kích thước file vượt ngưỡng cho phép → **chunked upload phải được hoàn tất đầy đủ** (partial chunk không được commit)
- KMS không khả dụng → **fail closed** (không lưu plaintext dự phòng)
- File binary upload không vượt qua **virus/malware scan** (trong scope production; lab có thể bỏ qua nhưng phải ghi nhận là residual risk)

#### Các trường hợp lưu có điều kiện

| Tình huống | Điều kiện | Hành vi |
|---|---|---|
| Điều dưỡng ghi chú | Role `NURSE` + action `WRITE_FIELD` cho field `nursing_notes` | Được phép; không được ghi `diagnosis_code` |
| Bác sĩ cập nhật kết quả xét nghiệm | Đã phân công, đúng khoa, ticket mục đích hợp lệ | Được phép; tạo version mới, không overwrite cũ |
| Upload ảnh X-Quang | `WRITE_ATTACHMENT` + type `xray` + size ≤ 50 MB | Được phép sau tất cả pre-commit gates |
| Người nhà bệnh nhân ghi nhận triệu chứng | Role `FAMILY_REPORTER` (nếu có) + field `patient_reported_symptoms` | Chỉ được phép nếu policy bundle version hiện tại cho phép role này; nếu không → 403 |

#### Atomicity (tính nguyên tử)

Giao dịch ghi phải nguyên tử: **hoặc tất cả thành công, hoặc không có gì được lưu**.

```
Thứ tự commit:
1. Sinh DEK + bọc capsule (KMS) — nếu fail → stop
2. Mã hóa payload (memory) — nếu fail → stop, capsule bị orphan → dọn dẹp async
3. Ghi ciphertext vào DB/MinIO — nếu fail → rollback
4. Cập nhật trusted registry version — nếu fail → rollback DB + xóa MinIO object
5. Ghi audit event Z3 — nếu fail → log warning; không rollback dữ liệu
```

---

### 11.3 Phân quyền chi tiết — Ai xem được gì

#### Ma trận phân quyền đọc (Read Permission Matrix)

| Chủ thể | Trường được xem | Trường bị giấu | Điều kiện bổ sung |
|---|---|---|---|
| **Bác sĩ điều trị** (`DOCTOR` + phân công) | Tất cả clinical fields: `diagnosis_code`, `note`, `treatment_plan`, `amount_units`, attachments | Thông tin hành chính của bệnh nhân khác | Chỉ bệnh nhân đang được phân công; đúng khoa; thời gian trong ca |
| **Điều dưỡng** (`NURSE` + phân công) | Thông tin hành chính, `nursing_notes`, vital signs | `diagnosis_code`, `note` đầy đủ của bác sĩ, `amount_units`, file X-Quang | Phân công chăm sóc |
| **Lễ tân / Đăng ký** (`REGISTRAR`) | PII hành chính: tên, ngày sinh, BHYT, lịch hẹn | Mọi clinical data, attachments | Đúng tenant |
| **Nhà phân tích** (`ANALYST`) | Aggregate results (SUM/count BFV) | Raw patient fields, file ảnh, PII | Approved cohort manifest; không xem từng record |
| **Bệnh nhân / Người nhà** (`PATIENT`, `FAMILY`) | Thông tin cá nhân của chính bệnh nhân: lịch sử khám, kết quả xét nghiệm, kết quả siêu âm/X-Quang của mình | Thông tin bệnh nhân khác; chi phí nội bộ (`amount_units` raw) | Xác thực qua cổng bệnh viện; chỉ read-only; không export |
| **DBA Cloud** (`DBA`) | Ciphertext và token (metadata không nhạy cảm) | Mọi plaintext, DEK | Không có quyền gọi KMS unwrap |
| **Kiểm toán viên** (`AUDITOR`) | Audit metadata: action, actor pseudonym, timestamp, decision | Clinical plaintext, private keys, DEK | Append-only read; không có write |
| **Chủ dữ liệu** (`DATA_OWNER`) | Có thể phê duyệt export/share artifact | KMS root, AA master secret tự động | Phải qua workflow approval |

#### Phân cấp xem file đính kèm (Attachment Visibility)

| Loại file | Bác sĩ | Điều dưỡng | Lễ tân | Bệnh nhân/Người nhà | Analyst |
|---|:---:|:---:|:---:|:---:|:---:|
| Ảnh X-Quang | ✅ (đúng khoa) | ❌ | ❌ | ✅ (của mình) | ❌ |
| Phim MRI/CT | ✅ (đúng khoa) | ❌ | ❌ | ✅ (của mình) | ❌ |
| Kết quả siêu âm | ✅ | ❌ | ❌ | ✅ (của mình) | ❌ |
| PDF kết quả xét nghiệm | ✅ | ✅ (kết quả cụ thể) | ❌ | ✅ (của mình) | ❌ |
| Ghi chú giọng nói bác sĩ | ✅ (tác giả + cùng khoa) | ❌ | ❌ | ❌ | ❌ |

#### Field Projection enforcement

Gateway thực thi field projection **trước khi trả response** — không trả envelope của field không có quyền. Key Broker độc lập kiểm tra lại trước khi unwrap DEK — dual PEP layer (đã triển khai ở WP5).

---

### 11.4 Website / Hệ thống quản lý hồ sơ bệnh nhân (Patient Portal & EHR Interface)

#### Yêu cầu

Cần một giao diện web cho phép:
- **Bác sĩ:** cập nhật tình trạng bệnh nhân, ghi chú lâm sàng, upload kết quả xét nghiệm
- **Bệnh nhân / Người nhà:** theo dõi tình trạng bệnh, xem kết quả, lịch hẹn
- **Lễ tân:** đăng ký thông tin hành chính, quản lý lịch hẹn
- **Quản trị:** phân quyền, quản lý tài khoản

#### Gợi ý hệ thống mã nguồn mở phù hợp

Dưới đây là các hệ thống EHR / Patient Portal mã nguồn mở được đánh giá theo mức độ phù hợp với yêu cầu:

---

**🏆 Khuyến nghị hàng đầu:**

**1. OpenEMR** ⭐⭐⭐⭐⭐
- **Repo:** https://github.com/openemr/openemr
- **Giấy phép:** GPL v3
- **Mô tả:** Hệ thống EHR (Electronic Health Record) mã nguồn mở phổ biến nhất thế giới, được sử dụng tại 30.000+ phòng khám ở 100+ quốc gia.
- **Ưu điểm:**
  - Hỗ trợ đầy đủ: hồ sơ bệnh nhân, lịch hẹn, đơn thuốc, kết quả xét nghiệm, billing
  - Có patient portal tích hợp (bệnh nhân tự xem hồ sơ)
  - REST API và FHIR HL7 support
  - Có phân quyền role-based cho nhiều loại nhân viên y tế
- **Nhược điểm:** Codebase PHP/MySQL truyền thống; cần tùy chỉnh nhiều nếu muốn tích hợp với MedShare-Lab (field encryption, Vault KMS)
- **Phù hợp:** Demo giao diện thực tế cho báo cáo; không thay thế core security layer của đề tài

---

**2. OpenMRS** ⭐⭐⭐⭐
- **Repo:** https://github.com/openmrs/openmrs-core
- **Giấy phép:** MPL 2.0
- **Mô tả:** Nền tảng EHR modular, ban đầu phát triển cho môi trường y tế thiếu tài nguyên (WHO/partners). Được dùng rộng rãi ở châu Phi, châu Á.
- **Ưu điểm:**
  - Kiến trúc module/plugin linh hoạt (Java Spring)
  - REST API đầy đủ, dễ tích hợp backend tùy chỉnh
  - Cộng đồng lớn, tài liệu phong phú
  - Hỗ trợ multi-tenant (multiple facilities)
- **Nhược điểm:** Cần Java/Tomcat stack; không có patient portal sẵn (cần cài thêm module)

---

**3. Medplum** ⭐⭐⭐⭐
- **Repo:** https://github.com/medplum/medplum
- **Giấy phép:** Apache 2.0
- **Mô tả:** Nền tảng EHR hiện đại xây dựng trên FHIR R4, TypeScript/React, PostgreSQL. Có cả backend (FHIR server) và frontend (React app).
- **Ưu điểm:**
  - **Stack hiện đại:** TypeScript, React, Node.js, PostgreSQL — dễ customize
  - FHIR R4 native — chuẩn interoperability quốc tế
  - Có patient portal, practitioner UI, admin UI sẵn
  - OAuth2/SMART on FHIR authentication
  - **Tích hợp tốt nhất với MedShare-Lab** vì có thể thay PostgreSQL layer bằng encrypted adapter của WP4
- **Nhược điểm:** Còn tương đối mới (2021), community nhỏ hơn OpenEMR

---

**4. GNU Health** ⭐⭐⭐
- **Repo:** https://gitlab.com/gnuhealth/gnuhealth
- **Giấy phép:** GPL v3
- **Mô tả:** Hệ thống health information system xây dựng trên Tryton ERP platform.
- **Ưu điểm:** Đầy đủ chức năng bệnh viện (hospital management, pharmacy, lab); dữ liệu có thể export FHIR
- **Nhược điểm:** UI Tryton không web-native; stack Python/PostgreSQL nhưng không RESTful

---

**5. Tự xây lightweight Patient Portal** ⭐⭐⭐ (phù hợp nhất cho đề tài)
- **Stack gợi ý:** FastAPI (backend) + Next.js hoặc Vue 3 (frontend)
- **Lý do:** Đề tài đã có FastAPI gateway; một frontend đơn giản kết nối trực tiếp vào gateway hiện có sẽ **minh họa đúng nhất luồng bảo mật** (authentication → ABAC → field projection → decrypt tại Z0)
- **Tính năng tối thiểu cần demo:**
  - Đăng nhập (JWT)
  - Bác sĩ: xem/cập nhật hồ sơ bệnh nhân, upload kết quả
  - Bệnh nhân/Người nhà: xem hồ sơ của mình (read-only)
  - Hiển thị rõ "Bạn không có quyền xem trường này" thay vì ẩn hoàn toàn
  
> [!TIP]
> Với mục tiêu đồ án thạc sĩ về **bảo mật**, hướng **tự xây lightweight portal** (mục 5) kết hợp OpenEMR làm reference/screenshot cho báo cáo là cân bằng tốt nhất giữa thời gian và giá trị minh họa.

#### So sánh tổng hợp

| Tiêu chí | OpenEMR | OpenMRS | Medplum | GNU Health | Tự xây |
|---|:---:|:---:|:---:|:---:|:---:|
| Tích hợp với FastAPI gateway | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Patient portal sẵn | ✅ | ❌ (module) | ✅ | ❌ | Tự làm |
| Stack quen thuộc (Python/JS) | ❌ PHP | ❌ Java | ✅ TS/React | ⭐⭐ | ✅ |
| Thời gian tích hợp | Cao | Cao | Trung bình | Cao | Thấp |
| Minh họa security layer | Khó | Trung bình | Tốt | Khó | Tốt nhất |
| Phù hợp demo đồ án | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |

#### Ghi chú scope cho đề tài

Việc xây dựng một hệ thống EHR đầy đủ **nằm ngoài phạm vi** đồ án mật mã học này. Phạm vi phù hợp là:
- **Demo tối thiểu:** một giao diện web đơn giản hiển thị luồng: login → ABAC decision → field projection → hiển thị bản rõ được phép
- **Trong báo cáo:** tham chiếu OpenEMR/Medplum như ứng dụng thực tế mà kiến trúc MedShare-Lab hướng đến bảo vệ; không cần triển khai đầy đủ
- **Tích hợp MinIO:** nằm trong phạm vi nếu thực hiện E7 (file attachment overhead) hoặc mở rộng E2
