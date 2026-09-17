# Thí nghiệm, security tests và đánh giá bằng chứng

Kèm [Detailed project implementation](../planning/implementation-plan.md) và [protocol design](../design/crypto-and-protocol-design.md).

**Trạng thái ban đầu của mọi experiment/test:** NOT_RUN. Những expected outcomes bên dưới là tiêu chí hoặc giới hạn cần xác nhận, không phải observed results. Lần lập tài liệu này chưa có application implementation để chạy test/benchmark.

## 1. Quy tắc thực nghiệm và an toàn

- Chỉ local lab/synthetic dataset. Không tấn công hệ thống công cộng, DB thật hay dữ liệu bệnh nhân thật.
- Mỗi experiment có hypothesis/question, independent variable, controlled variables, oracle, negative controls, metric, artifact và limitation.
- B0 plaintext là baseline đo trong isolated lab, không production option. B1 có encrypted volume thật mới được ghi “implemented”; encrypt một file JSON không thay volume baseline.
- Test trên target sao chép riêng; restore/rotation fault injection không đụng workspace gốc hoặc hạ tầng ngoài scope.
- Không lưu secret/key/plaintext clinical body vào test logs. Test fixture chứa synthetic plaintext ở data generator/oracle được tách khỏi evidence metadata; private crypto fixture sinh runtime.
- Unit tests có thể dùng mock KMS, nhưng E2 phải có authenticated real software KMS hoặc ghi rõ mô phỏng và thu hẹp claim. Không gọi container isolation là hardware-backed security.
- Chỉ chạy benchmark dài sau khi security/correctness gates đạt. Trong triển khai, đo thử pilot để ước lượng thời gian; đặt ngân sách thời gian rõ cho full run.

## 2. Dataset, query semantics và workload W1–W10

### 2.1 Generator có seed nhưng khóa không có seed công khai

| Dimension | Profile chính | Lý do |
|---|---|---|
| Tenant | 3 tenant H1/H2/H3, cân bằng ban đầu | Test cross-tenant và domain separation |
| Record count | 1k functional; 10k main; 100k scale-up nếu tài nguyên cho phép | Không tăng toàn bộ tổ hợp thí nghiệm vô hạn |
| Roles/departments | Doctor/nurse/registrar/analyst/owner/DBA/auditor; 3 khoa | Tạo positive/negative/collusion/approval cases |
| PII | Synthetic names, external IDs và email miền example.invalid | Không lấy dữ liệu người thật |
| Categorical diagnosis | 20 categories synthetic, không ánh xạ hồ sơ thật | Uniform vs skewed distribution cho inference |
| amount_units | Integer 0–1000 | BFV exact sum có upper bound rõ |
| Notes | Synthetic text lengths 128/1024/4096 byte | Đo ciphertext length/storage impact |
| Seed dữ liệu | 1801, 1802, 1803, 1804, 1805 | 5 lần độc lập; config không chứa key seed |
| Query seed | Tách dataset seed, lưu trong manifest | Workload cùng semantics giữa profiles |
| Crypto randomness | CSPRNG runtime, không deterministic benchmark seed | Seed reproducibility dữ liệu không làm suy yếu key generation |

Policy truth table/oracle do researcher viết độc lập với PDP rules: tenant, role, department, assignment, field, action, purpose ticket, time window, emergency approval và revoked status. Sinh tổ hợp exhaustive trên các miền nhỏ cộng boundary cases; không chỉ 5–10 request minh họa.

### 2.2 Support matrix

Ký hiệu: S = hỗ trợ; U = không hỗ trợ, reject rõ; N/A = không áp dụng. B0/B1 dùng cùng plaintext semantics. Profile P2/P3/P4 không là DB query engine đầy đủ.

| Workload | B0/B1 | P1 SQL/NoSQL | P2 share | P3 BFV | P4 archive |
|---|---|---|---|---|---|
| W1 point lookup | S | S: record UUID, decrypt allowed fields | S: fetch share artifact, không row policy động offline | N/A | S: archive object fetch/decrypt |
| W2 equality filter | S | S: approved blind index + field/row authz | U | U | U |
| W3 range query | S | U trên encrypted sensitive field | U | U | U |
| W4 join | S, logical reference oracle | U với sensitive join; public metadata join chỉ extension có nhãn | U | U | U |
| W5 text search | S nếu cấu hình baseline hỗ trợ | U; không tự decrypt full DB | U | U | U |
| W6 aggregate | S | U cho server aggregate encrypted amount | U | S: approved cohort SUM/count | U |
| W7 insert/update | S | S: fresh field DEK/version; CAS | S: export version mới, không OLTP update | S: snapshot batch mới, không OLTP | S: archive version mới |
| W8 bulk export | S, authorized baseline | S: data-owner approval, bounded export | S: encrypted share package | N/A | S: archive package |
| W9 backup/restore | S, B1 keys separated | S: ciphertext + separate key/registry recovery | S: encrypted artifact + AA/recipient recovery riêng | S: ciphertext và owner keys backup riêng | S: ciphertext và recipient key backup riêng |
| W10 rotation | N/A B0; S B1 key operation thực tế | S: KEK/DEK/index/policy | S: epoch/reissue/reencrypt | S: snapshot/key profile mới | S: wrap/signature migration |

SQL và NoSQL baseline dùng cùng normalized equality/aggregate semantics ở client oracle để tránh collation/NULL/missing khác nhau bị tính nhầm là crypto error. W3/W4/W5 trong baseline là functional comparison, không ép so latency với P1 không hỗ trợ. Unsupported là kết quả thiết kế hợp lệ nhưng phải hiện bảng, không được thay bằng full-client scan bí mật.

### 2.3 Workload chạy và phạm vi matrix

- Functional suite dùng 1k records và edge fixtures (empty/missing/Unicode/duplicate values, wrong tenant, same token across different domain).
- Micro/workload đơn: W1, W2, W7, W9, W10 riêng; W6 cho P3. Main mix: 60% W1, 25% W2, 15% W7 theo cùng seed.
- Main comparison B0/B1/P1 trên từng DB với 10k records, concurrency 1 và 8. Nếu muốn tách attribution: P1-no-index, P1-with-index và policy/KMS warm/cold là các ablation đã gắn ID; không tắt authorization trong profile protected chính.
- Scale-up 100k/concurrency 32 chỉ thực hiện sau pilot, tối đa một tập cấu hình quan trọng; không full Cartesian product N × concurrency × field size × every policy/suite.
- P2 policy size 4/8/16 leaves, recipient groups 10/50; P3 cohorts 100/1000/10000; P4 capsules 100/1000. Dữ liệu ứng dụng nền giống nhau, nhưng cryptographic microbench có units riêng.

## 3. Đặc tả experiments

### E1 — Plaintext và volume baseline

**Câu hỏi:** volume encryption thay đổi stolen-snapshot coverage và overhead thế nào, và tại sao không chống DBA đang query?

Biến độc lập B0/B1, cùng DB version/dataset/resources/query plan/durable write setting; chạy PostgreSQL và MongoDB riêng, không cùng tranh CPU. Tạo encrypted lab disk riêng, key không nằm trong snapshot. Oracle query là plaintext reference; backup restore có hai tình huống raw volume và logical dump.

Đo p50/p95/p99/QPS/errors, DB/index/backup bytes, startup/unlock/restore time. Security: raw encrypted volume không có key không đọc được; DBA query ở B1 **vẫn đọc plaintext**; logical dump B1 ra ngoài volume có thể là plaintext. Negative control B0 stolen files đọc được khi có compatible DB tooling. Không dùng việc grep không thấy một chuỗi làm chứng minh crypto confidentiality.

Artifacts: profile manifest, metadata disk/DB, benchmark CSV, TC-02/08/28 logs, protection boundary table. Không xuất unlock key hoặc destructive disk commands vào report.

### E2 — Field envelope và key management

**Câu hỏi:** giữ DEK ngoài DB giảm exposure thế nào và tốn bao nhiêu key/storage/network cost?

So B0/B1/P1 trên mỗi DB; ablation crypto CPU vs KMS network vs per-field DEK granularity. Core sử dụng key mới per field-version, PDP/broker độc lập, expected AAD/registry. Tests TC-01/02/05/06/09/10/24/26/28. Đo AEAD enc/dec, wrap/unwrap, end-to-end read/write, ciphertext/capsule expansion, number of KMS calls, cache policy và DB admin outcome.

Không claim service-side gateway bảo vệ khỏi chính gateway. Empty field/null và malformed envelope phải có semantics rõ, không lưu plaintext “fallback” khi KMS down.

### E3 — ABAC enforcement và bypass

**Câu hỏi:** policy đúng ở API có còn được giữ khi client query DB hoặc gọi broker trực tiếp?

Truth table độc lập đánh giá false permit = unauthorized requests được permit / total unauthorized requests; false deny = authorized bị deny / total authorized. Ghi cả count và denominator; không hide invalid inputs khỏi mẫu tính mà không báo.

So PEP gateway, PEP broker và SQL RLS bổ trợ; cùng logical policy trên NoSQL layout. Tests TC-03/04/07/27 và parts TC-02/26. Thử normal user, stolen least-privileged service DB credential, privileged DBA, direct broker caller không có đúng identity/context.

DBA đọc ciphertext là expected; DBA đọc protected plaintext hoặc broker unwrap không đúng scope là fail. Mục tiêu 0 false permit trên finite suite, không phải chứng minh correctness mọi chương trình/quy tắc tương lai. Policy latency tách network round-trip và evaluation CPU.

### E4 — CP-ABE policy sharing

**Câu hỏi:** durable policy plane có tác dụng gì ngoài ABAC và chi phí phụ thuộc policy/recipient thế nào?

P2 độc lập; ABE wrap small group-secret capsule → KDF → AEAD-wrapped share DEK → AEAD bulk export. Record exact scheme/backend/group/claimed security model; không assume ví dụ library đạt modern security.

So policy leaves 4/8/16 và thỏa/không thỏa, 10/50 recipient key issuance; đo setup/keygen/enc/dec, user key/capsule size, serialization và full export encryption riêng. Tests TC-11/12/13/14. Epoch/revocation đo trong E9. ABE collusion test gồm component-level manipulation phù hợp implementation, không chỉ middleware từ chối list keys.

Không dùng thử nghiệm hữu hạn thay security proof; nếu scheme CPA-only thì ghi rõ. Signed input validation giảm active tampering surface trong prototype, không tự chứng minh generic ABE composition CCA-secure.

### E5 — Secure equality query và leakage inference

**Câu hỏi:** query functionality/latency đổi lấy observable information nào, và leakage có thực sự suy ra được giá trị dưới auxiliary knowledge đã định?

Profile P1 with HMAC blind index trên SQL/NoSQL; diagnosis index bật riêng trong isolated leakage fixture. Controls: randomized AEAD không index, uniform categories, skew categories và tenant-scoped vs intentionally shared-domain negative fixture. Không gọi fixture key-sharing yếu là recommended mode.

Correctness TC-15; inference TC-16; active index/result tampering TC-17. Chi tiết phương pháp ở mục 5. Đo index/storage/write amplification, query latency và candidate count/returned count; oracle ở trusted harness, observer chỉ thấy server-visible projection.

Mitigation thực nghiệm tối thiểu: bỏ index diagnosis hoặc thay query use-case bằng approved aggregate; tenant/key domain separation. Optional padding/bucketing phải báo overhead và leakage còn lại, không claim ORAM/differential privacy.

### E7 — Advanced encrypted aggregate bằng BFV

**Câu hỏi:** cloud worker tính SUM/count mà không có secret key với chi phí nào và giới hạn integrity/privacy nào?

Exact integer semantics 0–1000, cohort ≤10k; t > bound; library parameter validation ở mức 128-bit. So plaintext SUM vs BFV pipeline, không so HE micro-add trực tiếp với DB full query như cùng unit.

Đo encode/encrypt/evaluation (add/rotations)/decrypt separately và end-to-end; bytes ciphertext/public evaluation keys/network; RAM; noise budget chỉ trong trusted debug bench không lộ key; max input test. Tests TC-18/19/30.

Trusted owner chuẩn bị cohort, server không encrypted WHERE. TC-19 phải minh họa ciphertext hợp lệ chứa tổng sai có thể giải mã thành công. Nếu cần claim chống malicious worker, bổ sung cơ chế verification riêng rồi test; không đổi “expected fail” thành “BFV bảo vệ integrity”.

### E8 — PQC key/signature path

**Câu hỏi:** standardized PQ key capsule và signatures ảnh hưởng kích thước/latency và interoperability thế nào?

P4 independent archive, ML-KEM-768 + HKDF + AEAD wrap, ML-DSA-65 authentic descriptor/manifest. Classical baseline cố định được khai báo; report security assumptions không tương đương mọi parameter. Tests TC-20/21/22, signature policy load và current-state validation.

Đo keygen/encap/decap/sign/verify time, raw/wire sizes, end-to-end capsule handling. ML-KEM invalid ciphertext đúng length có implicit rejection; success criterion là protocol không giải mã/trả data, không phải mọi library call throw.

Crypto-agility inventory gồm data cipher, KEM/wrap, signature, ABE, TLS/cert, KMS/auth, backup escrow và recipient historical keys. Không gán “PQC readiness score 100%” chỉ vì library exposes ML-KEM.

### E9 — Rotation/revocation/migration

**Câu hỏi:** quyền bị thu hồi/khóa đổi có semantics và chi phí vận hành nào, đặc biệt với bản sao offline và failure giữa chừng?

Các case: KEK-only rewrap; fresh DEK re-encryption; ABAC revoke; ABE epoch/reissue; search key reindex; classical-to-PQ archive rewrap. Tests TC-06/07/09/13/14/22/23/28. Dùng 100/1000 capsules, 10/50 users cho ABE; concurrency writers/readers có expected_version.

Fault injection tại trước DB write, sau DB trước registry commit, mid-rewrap, sau cutover trước retirement; retry cùng job ID. Đo elapsed/downtime, accepted/rejected/stale operations, rows/capsules/bytes touched, retry count, old/new decryptability online và offline.

KEK-only rewrap phải giữ data ciphertext digest không đổi. DEK/AAD đổi thì ciphertext phải đổi. Revoked user giữ old key + old capsule vẫn đọc được historical data là residual expected; private old capsule harvested trước migration không được “xóa bằng một chữ ký mới”.

## 4. Danh mục security tests TC-01–TC-30

Mỗi TC là một nhóm test có nhiều subcases. Tạo test file khi module tồn tại; tên dưới là kế hoạch, không hàm test đã có. Các cases “LIMIT” xác nhận giới hạn thiết kế, không phải security goal được đáp ứng mạnh hơn.

| ID | Setup / attacker action | Expected và oracle | Evidence khi chạy |
|---|---|---|---|
| TC-01 | Round-trip fields: empty/UTF-8/large allowed/null; SQL/NoSQL | Output đúng typed plaintext oracle; randomized ciphertext khác giữa encryptions | cases/assertions + encoded sizes, không plaintext logs |
| TC-02 | Direct SELECT/find bằng service role rồi DBA | B1 DBA plaintext = LIMIT; P1 protected fields ciphertext; no KMS access | role metadata, access outcome, decrypt permission status |
| TC-03 | Sai tenant/record/field, giả object labels; gọi broker trực tiếp | Deny trước key release, không cross-tenant/field plaintext | policy matrix + broker denial counts |
| TC-04 | Sai role/dept/purpose/time, forged/expired emergency ticket; token issuer/audience/signature/expiry sai | Deny; valid approved break-glass chỉ scope cho phép; no export escalation | expected/observed permit/deny table |
| TC-05 | Flip ciphertext/tag/nonce; swap tenant/record/field/data_version/AAD; swap nguyên envelope | Reject trước plaintext release dựa trusted context; valid control pass | mutation type, assertion và rejection category |
| TC-06 | Replay old valid data/capsule/signed policy hoặc metadata pair | Online reject theo independent current version/hash; không chỉ tag check | version pairs, registry comparison outcome |
| TC-07 | Revoke user khi cache=0; request sau commit; concurrent in-flight | Sau điểm release authorization/revoke tuyến tính hóa phải đúng semantics; old offline bytes không biến mất | ordered event IDs, key-release counters, lag |
| TC-08 | Restore/copy B1 raw volume và P1 dump không unlock/KMS permission | Raw volume locked; P1 fields không decrypt; B1 logical dump plaintext nếu không bọc riêng = LIMIT | restore outcomes, key permission yes/no, backup metadata |
| TC-09 | Rotate KEK vs DEK, wrong/wrong-version wrap key | KEK rewrap giữ data digest; DEK rotation đổi ciphertext; wrong key reject | counts/digests và old/new online behavior |
| TC-10 | Scan constructed logs/CDC/replica/backup artifacts với synthetic canaries | No plaintext protected canary/private secret material in artifacts không được phép; ciphertext preservation | allowlisted file names/counts only, không in matching values |
| TC-11 | CP-ABE authorized/unauthorized/wrong tenant/wrong epoch keys | Chỉ single valid user key recover đúng group secret/share DEK | per-policy pass/deny + sizes/times |
| TC-12 | U1/U2 không đủ policy riêng; component-level key mixing | Không recover đúng secret; U3 valid positive; keygen(union) không được coi là attack | manipulation class và recovery boolean, không secret bytes |
| TC-13 | Epoch increment, revoke U1, reissue U2, fresh share DEK | Revoked old key không đọc new artifact; current valid key đọc được | key/epoch IDs, issuance cost và new decryptability |
| TC-14 | U1 giữ old ciphertext/DEK; đổi online policy hoặc rewrap cùng DEK | LIMIT: old bytes vẫn đọc được; giải thích vì sao cần fresh DEK cho future content | online vs offline matrix, không giả “absolute revoke” |
| TC-15 | Equality duplicates/Unicode/normalization boundaries, update/delete | Matched plaintext set bằng oracle sau authorized projection; unsupported range/text/join reject | expected/actual set hashes, query plan metadata |
| TC-16 | Observer frequency/search/access inference với auxiliary dataset tách biệt | Report accuracy/advantage/CI; không preset phải nhỏ; true labels chỉ cho scorer | observer traces, inference config, aggregate scores |
| TC-17 | Cloud bỏ/thêm/stale index entries, duplicate/missing result | Misbound content rejected; omitted rows có thể không detect = LIMIT; no completeness claim | mutation/outcome, returned vs oracle count |
| TC-18 | BFV SUM empty/min/max/multi-batch/both batching rows | Exact integer sum/count trong bound; wrong parameter/oversize serialization reject | result comparison, public params/noise/resource metrics |
| TC-19 | Worker trả encrypt(giá trị sai), replay wrong cohort result | Manifest/context mismatch có thể reject; valid context encrypted wrong value có thể qua = LIMIT | integrity-gap scenario, oracle discrepancy |
| TC-20 | PQ KAT/round-trip, valid descriptor vs substituted/expired public key; TLS certificate chain/name/expiry sai | Valid operation pass; untrusted descriptor/TLS peer reject trước crypto use | vector provenance, assertion status, raw/wire sizes |
| TC-21 | PQ capsule/signature/context tamper; malformed/invalid ML-KEM ciphertext | No plaintext release; đúng-length implicit rejection đánh giá ở DEM/protocol; unknown inputs bounded | mutation/outcome, no detailed decryption oracle |
| TC-22 | Unknown/retired/mismatched suite, old signed policy, negotiation downgrade | Reject, không tự fallback; dual-read chỉ trong signed migration state | suite/state matrix và decisions |
| TC-23 | Migrate archive classical→PQ, giữ old capsule attack fixture | New reads pass; key-only data digest unchanged; LIMIT: harvested old capsule vẫn là old path | counts/latency/compatibility/historical risk |
| TC-24 | Forced RNG failure, repeated key/nonce test fixture, retries/concurrent writes, malformed sizes | Fail safe/no seed fallback; same-DEK second encryption refused by design; retry exact envelope or fresh key; parser bounded | uniqueness/state assertions; finite sampling không proof RNG |
| TC-25 | Sửa audit event, truncate chain, replay old checkpoint | Detect with independent latest witness; local-only truncate case = LIMIT | hash/sequence verification outcomes |
| TC-26 | Stop lab PDP/KMS, timeout/error, oversized query | Fail closed, no default permit/plaintext fallback; bounded resources/health error | response categories, key-release count zero, resource bounds |
| TC-27 | Field projection/RLS vs table-owner/superuser, Mongo scoped role, caller-set tenant hint | Least privilege enforce đúng; DBA bypass logical layer = LIMIT nhưng keys vẫn tách | role flags, policy false-permit/deny totals |
| TC-28 | Crash at migration/DB-registry boundary, restore stale checkpoint, duplicate job | Reconcile/resume idempotently, no silent version rollback/key loss/nonce reuse; temporary deny allowed | journal states, retry counts, consistency assertions |
| TC-29 | Rebuild workers, verify algorithm IDs/params/KAT/version; rerun manifest | Correct versions/parameters, schema-valid evidence, reproducible logical outcomes; dependency unsupported fails gate | build/config public metadata, test manifest, dependency inventory |
| TC-30 | Analyst arbitrary decrypt request, small/differencing cohorts | Deny unapproved cohort/decrypt oracle; minimum cohort policy; LIMIT: no DP guarantee against all inference | approved/denied matrix, residual aggregate leakage |

### 4.1 Test oracles và pass/fail rules

1. **Functional/security-goal case:** PASS chỉ khi observed assertion đúng expected requirement. Lỗi library không đồng nghĩa secure reject nếu crash làm lộ key hay fail-open ở retry.
2. **LIMIT case:** ghi kết quả observed và requirement scope; “PASS_LIMIT_DEMONSTRATED” trong subcase metadata nghĩa là xác nhận giới hạn, **không** đánh dấu SR mạnh hơn verified.
3. **NOT_RUN/BLOCKED:** không đổi thành PASS dựa code review, mô phỏng hoặc đọc tài liệu.
4. **PARTIAL:** hỗ trợ một số assumptions/subcases, còn gap. Final traceability kết luận partial, không lấy majority tests pass để phủ failure bảo mật quan trọng.
5. **Finite coverage:** 0 false permit/0 nonce duplicates trong test hữu hạn không là xác suất 0 ở production; bổ sung design argument và dependency assumptions.

## 5. Leakage/inference thực nghiệm cấp Master

### 5.1 Tách adversary view khỏi ground truth

Observer đọc projection được whitelist từ **server side**: tenant/record pseudonyms, stable token equality classes, per-query returned record IDs, result counts, operation/timing và ciphertext lengths. Không có search key, DEK, plaintext query string, clinical values hoặc label oracle. TLS packet capture không thấy token nếu không decrypt; phải phân biệt network observer với DB observer có quyền thấy query/token trong engine.

Trusted scorer giữ mapping synthetic plaintext↔category; không đưa mapping này cho attack script. Auxiliary corpus được sinh độc lập với target: cùng category vocabulary và distribution family nhưng khác seed/samples; không dùng histogram chính xác của target làm tri thức mặc định.

### 5.2 Thiết kế tối thiểu có kiểm soát

| Factor | Các mức |
|---|---|
| Distribution target | Uniform 20 labels; skewed Zipf với tham số được lưu (ví dụ 1,2) |
| Auxiliary knowledge | Không có; corpus độc lập cùng phân bố; noisy auxiliary; oracle histogram chỉ upper-bound có nhãn riêng |
| Query repetition | Ít lặp, nhiều lặp; query seed công bố, plaintext không cho observer |
| Index domain | Tenant-scoped correct; shared-domain negative fixture |
| Mitigation | Không index clinical label; index chỉ high-cardinality identifier; optional padding nếu thật sự implement |

Attack baseline: frequency-rank matching hoặc assignment giữa token-class counts và auxiliary category frequencies. Ties xử lý bằng quy tắc deterministic đã ghi hoặc random seed độc lập; không chọn tie thuận lợi sau khi thấy labels. Không có auxiliary → baseline random guessing và majority-class predictor. Known-query samples là attacker model mạnh hơn, lưu riêng mức 0/5/20 known queries nếu thử.

### 5.3 Metrics và diễn giải

- Token/category mapping accuracy (macro, mỗi category một trọng số) và record-weighted accuracy (micro). Báo count/denominator và coverage; frequency attack có thể tốt ở majority categories nhưng kém macro.
- Advantage = accuracy_attack − accuracy_baseline theo cùng split/seed; với category uniform random guess là 1/20, với skew cần report majority baseline riêng, không lấy 1/20 làm baseline duy nhất.
- Repeated-query linkability: precision/recall hoặc exact match rate giữa observed repetition classes và true repeated queries, scorer mới biết ground truth.
- Access-pattern overlap bằng Jaccard trên record-ID sets, result cardinality và length/timing distributions. Observation metric không tự đồng nghĩa plaintext inference.
- Đo 5 dataset/query seeds, bootstrap CI qua các run hoặc paired run differences. Không kết luận scheme an toàn chỉ vì một frequency attack đơn giản thất bại.
- Order leakage: không có order encoding trực tiếp trong blind index; ghi possible auxiliary inference thay “không có bất kỳ order leakage nào”. Token equality/frequency là leakage ở storage view, không phải ciphertext AEAD trùng nhau.

Bảng kết quả cuối có cột threat model, view, auxiliary knowledge, target distribution, algorithm, accuracy/advantage/CI, cost và residual assumptions. Không gộp mọi “encrypted search” thành một nhãn.

## 6. Thiết kế thống kê và đo hiệu năng

### 6.1 Giao thức benchmark

1. Record machine/OS/VM limits, CPU model và acceleration khả dụng, RAM, storage type, compiler/runtime/library/DB/container versions, TLS/auth/policy/KMS cache config, dataset/query/profile IDs. Chỉ allowlist thông tin công khai, không dump environment.
2. Restore cùng dataset state trước mỗi paired run; kiểm tra logical checksums/oracle. Record whether indexes built/analyzed và background compaction/checkpointing.
3. Warm-up 30 giây, đo tối thiểu 120 giây cho main workload; 5 independent runs. Randomize/counterbalance thứ tự B0/B1/P1 và DB để giảm drift/cache bias.
4. Tối thiểu 10.000 completed samples trong nhóm dùng p99 nếu khả thi; nếu không đạt thì vẫn report n và CI rộng/không ổn định, không kéo dài vô hạn. Đặt maximum run duration và budget từ pilot.
5. Record per-op latency bằng monotonic high-resolution timer, start/end semantics rõ (client end-to-end hoặc server stage). Đo scheduled-arrival load khi cần latency dưới offered load; nếu closed-loop thì công bố coordinated-omission limitation.
6. Errors/timeouts được tính error rate và offered/completed throughput riêng. Không chỉ bỏ failed requests rồi gọi p99 thấp là tốt. QPS = completed successful operations / measurement duration, TPS chỉ cho workload transaction đã định.
7. Cold/warm KMS/cache experiment riêng, không so warm baseline với cold protected. Không xóa OS caches bằng privileged disruptive command trên máy làm việc; dùng isolated lab restart nếu cần và mô tả khác biệt.
8. CPU cycles/op chỉ khi PMU/perf counter chạy được trong lab; nếu VM chặn thì N/A kèm ns/op. Không suy cycle = time × nominal GHz. Peak RSS/CPU time/bytes vẫn đo được.

### 6.2 Confidence intervals và tránh pseudo-replication

- Báo p50/p95/p99 per run, central estimate trên runs và 95% CI. Percentile tính trên cùng loại operation, không trộn W1 với W10.
- Latencies trong cùng run có autocorrelation. Dùng run-level bootstrap hoặc block/hierarchical bootstrap khi phân tích sample-level; không coi hàng triệu request cùng một run là hàng triệu independent replicates.
- Minimum 5 independent runs chỉ là baseline feasibility, CI có thể rộng; tăng 10 runs cho kết luận quan trọng nếu budget cho phép. Bootstrap 2000 resamples trên đơn vị độc lập, ghi phương pháp và seed analysis.
- Overhead latency = (protected − baseline) / baseline × 100% theo paired run/config. Throughput change dùng cùng workload và rate/parallelism, không gọi giảm QPS là tăng latency tương đương tuyến tính.
- Storage expansion = total protected bytes / total baseline bytes; tách data/index/capsule/evaluation-key/backup. Network bytes là wire payload thực tế nếu có đo, không chỉ ciphertext length.
- Báo effect size/CI thay chỉ p-value. Không khẳng định nguyên nhân crypto nếu DB engine/query plan/driver/schema khác nhau; within-engine comparison là bằng chứng chính.
- Failed/outlier runs: giữ raw data và lý do exclude đã định (machine suspend, crash ngoài experiment…), không loại run chỉ vì “số liệu xấu”.

### 6.3 Kỳ vọng và ngưỡng không được bịa trước

Security/correctness gates là cứng theo stated scope (no false permit, reject tamper, exact bounded BFV). Latency/storage overhead là **biến kết quả cần đo**, không hứa “dưới 5%” hay “tăng 10 lần” khi chưa chạy. Có thể đặt user-experience target tạm thời sau baseline/pilot bằng ADR; target fail phải báo, không sửa số liệu để đạt.

## 7. Schema artifact và traceability

| Artifact dự kiến | Nội dung công khai được phép | Không được chứa |
|---|---|---|
| run-manifest.json | run_id, UTC, revision, dataset/query seeds, config digest, public params, tool versions, machine allowlist | env dump, credentials, private key paths có nội dung |
| security-results.jsonl | TC/subcase IDs, expected category, observed assertion, status, limitations, artifact refs | plaintext/keys/tokens/headers |
| latency.csv | run/profile/DB/workload/op IDs, latency_ns, status, cache mode | query values/PII |
| crypto-cost.csv | operation, scheme/param IDs, duration_ns, cycles nếu thật, input/output sizes | key bytes/shared secrets |
| leakage-observations.jsonl | Observer projection pseudonyms/equality classes/counts/timing | ground-truth labels hoặc secret key |
| leakage-scores.csv | split/model/seed, accuracy/advantage/CI và denominators | per-record PII thật |
| migration.csv | versions, state, counts, elapsed, failures, data-digest unchanged boolean | DEKs hoặc KMS raw responses |
| evidence-manifest.json | Relative artifact refs + SHA-256 + producer/test IDs | Secret material; hash một secret không thay bảo vệ secret |

Ground truth synthetic dùng riêng tại datasets/oracle trong lab. Public evidence cần đủ tái lập từ generator mà không cần crypto secret hiện tại; re-run sinh khóa mới, không yêu cầu cùng ciphertext bytes giữa hai lần chạy.

Cấu trúc bằng chứng theo run ID do harness sinh, không hard-code một thư mục kết quả giả. Khi test chạy xong mới tạo artifact link vào [traceability matrix](traceability-matrix.md). Trước đó ghi NOT_RUN, evidence chưa tạo. Chữ ký/hash artifact giúp provenance nhưng không bảo đảm experiment được thiết kế đúng.

## 8. Quy trình kết luận theo yêu cầu

1. **Evidence:** raw assertion + run manifest + artifact hash, lấy từ execution thật.
2. **Finding:** mô tả điều được quan sát, không vượt attacker view và sample domain.
3. **Path:** nối finding với T/SR/CR/module/test, cập nhật control hoặc thu hẹp claim nếu cần.
4. **Decision:** verified / partially verified / not verified, kèm assumption và residual risk.

Ví dụ chưa có kết quả: T-05 → SR-05 → CR-02 → trusted AAD + AEAD → TC-05; trạng thái NOT_RUN. Sau implementation phải điền actual run ID và rejected/accepted cases; không copy “expected rejected” sang cột observed.

## 9. Gói nghiệm thu A1–A10

| Artifact guideline | Nội dung cần nộp |
|---|---|
| A1 System model | Architecture/DFD F0–F9, trust zones/assumptions, query support |
| A2 Asset inventory | Fields, credentials, keys, state, impact/cascading compromise |
| A3 Threat model | M0–M4, T-01–T-18, priorities, out-of-scope |
| A4 Security requirements | SR-01–SR-18 có criteria |
| A5 Security architecture | PEP/PDP/key placement, trusted registry, backup/audit |
| A6 Crypto requirements | CR-01–CR-12, formal notion/assumption/constraints |
| A7 Crypto design | Parameters/envelopes/key hierarchy/composition/alternatives |
| A8 Implementation | Source, pinned build/config, setup/run/recovery instructions, critical code walkthrough |
| A9 Security tests | Executable positive/negative/adversarial suite và observed evidence |
| A10 Evaluation | Traceability, statistics/leakage, residual risks, scoped conclusion |

Đủ Markdown không thay A8–A10. Sau mỗi code change cần viết/cập nhật tests, chạy scope nhỏ nhất phù hợp, sửa lỗi và rerun; trước nghiệm thu chạy toàn bộ security suite đã chọn và measurement plan trong lab.
