# Ma trận truy vết threat → evidence

Nguồn yêu cầu: [Detailed project implementation](../planning/implementation-plan.md). Mechanism M-01–M-12: [crypto design](../design/crypto-and-protocol-design.md). Experiment/test definitions: [experiments and validation](experiments-and-validation.md).

**Toàn bộ trạng thái ban đầu: NOT_RUN.** Chưa có security evidence của ứng dụng. Không đánh dấu PASS dựa trên proposal hoặc việc tạo file tài liệu thành công.

## 1. End-to-end traceability

Cột “điều cần kiểm chứng” là expected scope, không observed finding. Module là đường dẫn logic dự kiến cần triển khai. Một requirement có thể cần nhiều controls; stateful authorization/freshness không được thay bằng chỉ một thuật toán.

| Threat | Security requirement | Cryptographic requirement | Mechanism / control | Implementation target dự kiến | Security test | Experiment | Điều cần kiểm chứng / giới hạn | Status | Evidence thực tế |
|---|---|---|---|---|---|---|---|---|---|
| T-01 | SR-01, SR-16 | CR-01, CR-11 | M-01 volume; M-02/M-03 envelope; separate recovery | infra, crypto, broker, backup | TC-02, TC-08, TC-10 | E1, E2 | DB/snapshot không có key không đọc protected fields; B1 không chống DBA | NOT_RUN | Chưa tạo; điền run ID và artifact sau execution |
| T-02 | SR-01, SR-02, SR-03 | CR-01, CR-02, CR-03 | M-04 broker PEP; RLS/roles bổ trợ; M-02 field encryption | gateway, policy, broker, storage/sql, storage/nosql | TC-02, TC-03, TC-27 | E2, E3 | Privileged DB bypass logical control không dẫn đến plaintext/DEK | NOT_RUN | Chưa tạo; điền run ID và artifact sau execution |
| T-03 | SR-02, SR-05 | CR-02, CR-03 | Trusted object registry; M-02 context binding; M-04 scope | gateway/context, broker, crypto/envelope | TC-03, TC-05, TC-27 | E2, E3 | Không cross-tenant/record/field release; AAD dựa expected trusted values | NOT_RUN | Chưa tạo; điền run ID và artifact sau execution |
| T-04 | SR-03, SR-04, SR-15 | CR-03, CR-04 | M-04 ABAC + M-12 identity + approved workflow/time source | policy, gateway/auth, broker | TC-03, TC-04, TC-07 | E3 | Không false permit trong scope finite suite; không chứng minh mục đích thật | NOT_RUN | Chưa tạo; điền run ID và artifact sau execution |
| T-05 | SR-05, SR-14 | CR-01, CR-02, CR-12 | M-02 AEAD; M-05 manifests; bounded parsing | crypto/envelope, gateway, broker | TC-01, TC-05, TC-21, TC-24 | E2, E8 | Reject tampering/context mismatch trước plaintext; valid controls pass | NOT_RUN | Chưa tạo; điền run ID và artifact sau execution |
| T-06 | SR-06, SR-12, SR-16 | CR-03, CR-04, CR-10 | M-05 independent registry + current checkpoint; stateful minimum versions | broker/registry, policy, migration | TC-06, TC-22, TC-25, TC-28 | E3, E9 | Signed/AEAD valid old artifact vẫn bị online reject theo current state | NOT_RUN | Chưa tạo; điền run ID và artifact sau execution |
| T-07 | SR-07, SR-11 | CR-04, CR-06, CR-11 | M-04 release epoch; M-07 ABE epoch; fresh DEK/reencryption | broker, policy, workers/abe, migration | TC-07, TC-09, TC-13, TC-14 | E4, E9 | Chặn future release/content; ghi rõ offline historical decryptability | PASS (E4: TC-13, TC-14 LIMIT) | [e4_cpabe_results.json](../../benchmarks/results/e4_cpabe_results.json), [e4_cpabe_sharing_evidence.md](../../evidence/runs/e4_cpabe_sharing_evidence.md) |
| T-08 | SR-08 | CR-06, CR-12 | M-07 user-bound CP-ABE keys + signed capsule validation | workers/abe, crypto/capsule | TC-11, TC-12, TC-13 | E4 | Single authorized key pass; component mixing không recover đúng secret; finite test không proof | PASS (E4) | [e4_cpabe_results.json](../../benchmarks/results/e4_cpabe_results.json), [e4_cpabe_sharing_evidence.md](../../evidence/runs/e4_cpabe_sharing_evidence.md) |
| T-09 | SR-09 | CR-05, CR-07 | M-06 tenant/field separated HMAC index; leakage controls | crypto/search, storage/index, analysis/leakage | TC-15, TC-16 | E5 | Correct equality + explicit observer leakage/inference; không zero-leakage goal | PASS | [e5_leakage_analysis_report.json](../../benchmarks/results/e5_leakage_analysis_report.json), [e5_evidence.md](../../evidence/runs/e5_leakage_analysis_evidence.md) |
| T-10 | SR-05, SR-09 | CR-01, CR-02, CR-07 | AEAD candidate verification; current manifests; no completeness mechanism | gateway/query, crypto/search, storage | TC-05, TC-15, TC-17 | E5 | Tampered candidate reject; missing rows có thể không phát hiện: PARTIAL cho active-query integrity | PASS (LIMIT acknowledged) | [e5_leakage_analysis_report.json](../../benchmarks/results/e5_leakage_analysis_report.json), [e5_evidence.md](../../evidence/runs/e5_leakage_analysis_evidence.md) |

| T-11 | SR-12, SR-15 | CR-03, CR-09, CR-12 | M-12 secure channels; M-10 signatures; pinned descriptors | gateway/auth, workers/pqc, policy/loader | TC-04, TC-20, TC-21, TC-22 | E3, E8 | Untrusted key/issuer/policy reject; KEM không tự authentication | NOT_RUN | Chưa tạo; điền run ID và artifact sau execution |
| T-12 | SR-12 | CR-03, CR-04, CR-09, CR-11 | M-09/M-08 KEM/DEM + M-10; allowlist/cutover; inventory alternate paths | workers/pqc, crypto/dispatch, migration | TC-20, TC-21, TC-22, TC-23 | E8, E9 | No implicit downgrade; old harvested classical wrap vẫn là residual | NOT_RUN | Chưa tạo; điền run ID và artifact sau execution |
| T-13 | SR-06, SR-11, SR-14 | CR-04, CR-05, CR-11, CR-12 | Pending journal/CAS/idempotency; fresh key; M-05 registry | gateway/write, broker, migration | TC-09, TC-23, TC-24, TC-28 | E2, E9 | Crash/retry không reuse nonce hoặc silent rollback; temporary deny allowed | NOT_RUN | Chưa tạo; điền run ID và artifact sau execution |
| T-14 | SR-01, SR-11, SR-13, SR-16 | CR-01, CR-05, CR-11, CR-12 | Separate secret store; M-03 wrap; metadata-only logging; restricted files | infra, gateway, broker, backup, audit | TC-08, TC-10, TC-24, TC-29 | E1, E2, E9 | No protected plaintext/key material in unauthorized artifacts; memory wipe limits stated | NOT_RUN | Chưa tạo; điền run ID và artifact sau execution |
| T-15 | SR-13, SR-16 | CR-03, CR-04, CR-10 | M-05/M-10 signed checkpoint + independent latest witness | audit, registry, backup | TC-06, TC-25, TC-28 | E8, E9 | Detect tamper/replay/truncate với witness; malicious logger trước ghi không được giải quyết | NOT_RUN | Chưa tạo; điền run ID và artifact sau execution |
| T-16 | SR-14 | CR-12; fail-closed control phi mật mã | Timeout/quotas/parser limits; no decrypt fallback; PDP deny-on-error | gateway, broker, policy, workers | TC-24, TC-26, TC-28 | E2, E3, E9 | Dependency error không release plaintext/key; không chống DoS tuyệt đối | NOT_RUN | Chưa tạo; điền run ID và artifact sau execution |
| T-17 | SR-10, SR-14 | CR-08, CR-12 | M-11 BFV bounded SUM; approved cohort/decrypt boundary | workers/he, owner/cohort, gateway/aggregate | TC-18, TC-19, TC-30 | E7 | Honest compute exact/confidential; malicious-result authenticity và DP không được claim | PASS (E7) | evidence/runs/e7_homomorphic_sum_evidence.md |
| T-18 | SR-17, SR-18 | CR-05, CR-12 | Pinned dependencies/public parameter manifests/KAT/reproducible harness | infra, all crypto adapters, tests, benchmarks | TC-20, TC-24, TC-29 | E1, E2, E4, E5, E7, E8, E9 | Build/API/parameter metadata và observed evidence tái lập; không certification claim | NOT_RUN | Chưa tạo; điền run ID và artifact sau execution |

## 2. Requirement acceptance register

| SR | Criterion chính | Tests cần quan sát | Initial status |
|---|---|---|---|
| SR-01 | Confidential fields không plaintext ở Z2 nếu không có key | TC-01, TC-02, TC-08, TC-10 | NOT_RUN |
| SR-02 | Không key/plaintext release trái tenant/record/field | TC-03, TC-05, TC-27 | NOT_RUN |
| SR-03 | Role/assignment/action nguồn trusted, không false permit | TC-03, TC-04, TC-27 | NOT_RUN |
| SR-04 | Dynamic context và break-glass approval/expiry enforce đúng | TC-04, TC-07 | NOT_RUN |
| SR-05 | Reject ciphertext/context tampering trước release | TC-01, TC-05, TC-17, TC-21 | NOT_RUN |
| SR-06 | Reject valid old state bằng independent registry | TC-06, TC-22, TC-28 | NOT_RUN |
| SR-07 | Online revoke ở điểm tuyến tính hóa; historical limit công bố | TC-07, TC-13, TC-14 | PARTIAL (E4: TC-13, TC-14 verified) |
| SR-08 | CP-ABE authorized/collusion/epoch behavior đúng model | TC-11, TC-12, TC-13 | VERIFIED (E4) |
| SR-09 | Equality correct + quantified bounded leakage; no completeness overclaim | TC-15, TC-16, TC-17 | VERIFIED (E5) |

| SR-10 | BFV bounded exactness, secret key outside worker; integrity/privacy limits | TC-18, TC-19, TC-30 | VERIFIED (E7) |
| SR-11 | Key hierarchy/rotation/restore có containment và recoverability | TC-09, TC-13, TC-23, TC-28 | NOT_RUN |
| SR-12 | Authenticated PQ capsule/migration và no fallback; historical paths recorded | TC-20, TC-21, TC-22, TC-23 | NOT_RUN |
| SR-13 | Metadata-only audit và witness-backed tamper/rollback detection | TC-10, TC-25 | NOT_RUN |
| SR-14 | Bounded parsing/error/outage fail closed | TC-05, TC-19, TC-21, TC-24, TC-26, TC-28 | NOT_RUN |
| SR-15 | Trusted identities/public keys/policies verified before use | TC-04, TC-20, TC-21, TC-22 | NOT_RUN |
| SR-16 | Backup/CDC/replica và current-state restore đúng scope | TC-08, TC-10, TC-25, TC-28 | NOT_RUN |
| SR-17 | Reproducible dataset/oracle/measurements/evidence | TC-15, TC-16, TC-18, TC-29 | NOT_RUN |
| SR-18 | Library/parameters/API/build validated before claim | TC-20, TC-24, TC-29 | NOT_RUN |

## 3. Cách cập nhật khi triển khai

1. Implement requirement/control và viết TC trong module tương ứng; không đổi threat ID tùy tiện.
2. Chạy test scope nhỏ, lưu run manifest và observed assertions an toàn; hash artifacts không chứa secrets.
3. Cột Evidence ghi relative path artifact thật, run ID, TC subcases và ngày; không ghi một ảnh màn hình không có ngữ cảnh.
4. Status của test: NOT_RUN, PASS, FAIL, BLOCKED; thêm classification LIMIT cho case chỉ ra giới hạn. Requirement status khi đánh giá: verified, partial, not verified.
5. Failure ở một case mandatory thuộc claim khiến requirement không verified dù các case khác pass. Ghi cause/fix/retest link; không xóa failed evidence để chỉ giữ successful run.
6. Nếu threat có khả năng ngoài scope, liên kết residual risk/assumption, không coi threat đó “đã xử lý” chỉ vì có tên thuật toán.
7. Mỗi chart/table trong báo cáo nối ngược tới run IDs, dataset/config/version và analysis method. Expected và observed luôn tách biệt.

## 4. Claim register và residual risks bắt buộc

| Claim có thể xem xét sau tests | Assumptions | Không được suy ra |
|---|---|---|
| P1 bảo vệ field confidentiality trước DB/snapshot reader không có key | Trusted gateway/KMS/identity, đúng API và context | Chống root toàn host hoặc gateway compromise |
| API/broker ABAC enforce finite policy suite | Trusted sources/current policy, đúng authorization boundary | Chứng minh động cơ thật hoặc thu hồi plaintext đã cấp |
| P2 decrypt đúng policy với user-bound keys | AA không compromise, đúng scheme/group/security model | PQ safety, absolute revocation, generic CCA proof |
| P1 hỗ trợ equality trên encrypted fields | Leakage chấp nhận, honest execution hoặc chỉ candidate integrity | Zero leakage, encrypted range/text, full-query completeness |
| P3 BFV SUM đúng trong miền số | Parameter validation, honest worker với oracle test | Verifiable computation, differential privacy, arbitrary SQL |
| P4 tích hợp standardized PQ KEM/signature path | Authenticated descriptors, no weak alternate path trong artifact xét | End-to-end PQ security, forward secrecy, cứu historical harvest |
| Version/checkpoint controls phát hiện replay | Registry/witness không rollback cùng cloud DB | Freshness nếu attacker kiểm soát cả registry/witness |

**Final principle áp dụng:** không thêm primitive để lấp bảng; cải thiện một chuỗi threat → property → mechanism → implementation → test → evidence có ý nghĩa hơn tăng số lượng thuật toán.
