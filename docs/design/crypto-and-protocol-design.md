# Thiết kế mật mã, format và lifecycle

Tài liệu kỹ thuật kèm [kế hoạch triển khai](../planning/implementation-plan.md). **Trạng thái:** đặc tả cần triển khai, không phải code/API đã được kiểm chứng. Các identifier trong bảng là tên contract dự kiến. Mọi secret trong đồ án phải được sinh runtime; không commit key mẫu, không dùng seed synthetic dataset để sinh khóa.

## 1. Primitive/parameter profile và mức claim

| Mã cơ chế | Thành phần | Profile đề xuất | Claim/giới hạn cần ghi |
|---|---|---|---|
| M-01 | At-rest baseline | Encrypted dedicated lab volume; metadata ghi thuật toán thực tế của volume | Không tự có field integrity/ABAC; DB engine đọc plaintext |
| M-02 | Data AEAD | AES-256-GCM; key 32 byte; nonce 12 byte; tag 16 byte | Confidentiality + integrity khi API/nonce/AAD đúng; không replay protection |
| M-03 | Key protection | Authenticated KMS wrap hoặc AEAD wrap với key tách domain | Software KMS không HSM/non-exportable trước root; cần context validation |
| M-04 | ABAC | PDP deny-by-default; PEP gateway/broker; trusted attribute sources | Đây là control logic, không primitive mật mã |
| M-05 | Freshness/manifests | Current-state registry + canonical manifest + signatures/checkpoints | Signature bản cũ vẫn hợp lệ; phải so version/hash từ nguồn current |
| M-06 | Equality token | HMAC-SHA-256, full 32-byte output, key ngẫu nhiên riêng | PRF token không che equality/frequency/search/access pattern |
| M-07 | CP-ABE | Candidate BSW07, exact scheme/backend/parameters được pin sau spike | Research-only; không tự claim CCA, 128-bit hay PQ; không copy SS512 thành security level |
| M-08 | KDF | HKDF-SHA-256, 32-byte output, typed/domain-separated info | Không dùng cùng derived key cho wrap/sign/token; KDF không sửa entropy nguồn yếu |
| M-09 | PQ KEM | ML-KEM-768 final FIPS 203 | Category 3 cho primitive theo chuẩn, không tự authentication/forward secrecy |
| M-10 | Signatures | ML-DSA-65 final FIPS 204 trong P4 policy/manifests/checkpoints | Category 3; module/library không mặc nhiên FIPS validated |
| M-11 | HE | SEAL BFV; polynomial degree 8192; library-supported 128-bit security profile; batching prime khoảng 30 bit | Integer modulo t, chỉ claim exact trong miền chống overflow; không authenticated ciphertext |
| M-12 | Channels/identities | TLS với kiểm tra chain/name; service mTLS hoặc authenticated channel tương đương | Inventory nếu certificate/handshake còn RSA/ECC; không tự có PQ TLS |

Core manifest signer có thể dùng Ed25519 qua thư viện tiêu chuẩn trước E8. E8 đối chiếu chuyển sang ML-DSA-65, chữ ký/descriptor có suite ID. Không ghi “toàn hệ thống category 3” khi CP-ABE, HE và TLS có giả định/mức khác nhau. Ghi RSA/ECC còn lại trong crypto inventory.

## 2. Key hierarchy và inventory bắt buộc

Xem [key-hierarchy.mmd](../diagrams/key-hierarchy.mmd). KMS root **bảo vệ**, không nhất thiết derive mọi KEK. DEK được sinh độc lập ngẫu nhiên; không dùng hash(record ID) làm DEK.

| Khóa/state | Sinh ở đâu | Lưu/backup | Rotation/revocation đề xuất |
|---|---|---|---|
| KMS root/unseal material | KMS bootstrap tin cậy | Restricted secret store, backup riêng; không DB backup | Theo sự cố/quy trình admin; ghi khả năng recovery |
| KEK tenant/class/version | KMS | KMS persistence; public key ID trong capsule | E9 rotate theo đợt; lịch 90 ngày chỉ là chính sách lab đề xuất, không NIST mandate |
| Data DEK | Gateway SDK CSPRNG | Chỉ wrapped ở Z2; plaintext transient Z1 | Fresh key mỗi field-value/version; thay đổi nội dung sinh mới |
| Nonce data | CSPRNG khi encrypt | Public trong envelope | Một encryption per DEK; retry dùng lại cùng envelope đã tạo, không mã hóa lại với cùng cặp key/nonce |
| Search key tenant/field/epoch | Trusted key manager | KMS protected, không đặt cạnh index | Rotate cần rebuild/dual index; không giải quyết leaked old index |
| Share DEK | Data owner export worker | CP-ABE-wrapped P2 capsule; không thêm KMS fallback copy cùng key vào Z2 | Thay DEK khi thay audience cần chặn future content; bản cũ không thu hồi được |
| AA master secret/public parameters | AA isolated research worker | Secret ở AA, protected offline backup; public parameters có authenticated descriptor | Master compromise cần re-setup/reissue và rewrap/re-encrypt theo threat |
| Attribute secret key | AA keygen cho từng user với randomness riêng | Recipient store qua provisioning bảo vệ | Epoch mới chỉ cấp non-revoked user; không xóa bản key họ đã copy |
| ML-KEM keypair | P4 archive recipient | Private key ở recipient, encrypted backup; public descriptor signed/pinned | Versioned recipient rotation; long-lived private key compromise ảnh hưởng old capsules |
| ML-DSA signing key | Policy/audit admin domain | Private signing key tách KEM/HE; backup/revocation log | Offline root hoặc pinned bootstrap; key rollover có signed link + minimum version |
| BFV secret/public/evaluation keys | Trusted HE owner | Secret không worker; evaluation/Galois keys public theo scheme | Per tenant/cohort experiment; không share HE secret với analyst |
| Registry current versions | Trusted Z1 store | Independent backup/checkpoint, không rollback bởi DBA | Monotonic version/CAS; recovery reconcile với witness |

Runtime TTL profile security tests: decision cache = 0; DEK persistent cache = 0; key sống trong một operation. Benchmark cache-enabled là cấu hình phụ riêng, ghi TTL/revocation lag. Python/GC không bảo đảm zeroization tuyệt đối; giảm lifetime/copies/core dumps, không tự tuyên bố secure erase trong RAM.

## 3. Data envelope và capsule không bị trộn version

### 3.1 Schema bytes cần chốt trước implement

| Record field envelope | Ý nghĩa |
|---|---|
| format_version | Version format, allowlist; unknown → reject |
| data_suite_id | Ví dụ logical ID cho AES256GCM-v1; không negotiation tự do |
| tenant_id, object_kind, record_id, field_id | Context không bí mật; expected values lấy từ request/registry tin cậy |
| data_version, data_policy_version | Version nội dung và nhãn crypto policy **bất biến trong ciphertext này** |
| dek_id | Random key identifier, không chứa PII hoặc key bytes |
| nonce, ciphertext, tag | Byte strings có encoding/length xác định; tag không truncate |
| capsule_id | Reference tới capsule hiện hành; không quyết định trust một mình |

| Key capsule/manifest | Ý nghĩa |
|---|---|
| capsule_id, capsule_version | Version wrap độc lập với data version |
| wrap_suite_id, wrap_key_id, wrap_key_version | Exact algorithm/profile/key reference |
| bound_object_context, dek_id | Capsule chỉ áp dụng đúng DEK/context |
| data_envelope_digest | Digest canonical encrypted object, không plaintext hash thấp entropy |
| policy_bundle_version, recipient_or_abe_policy_digest | Current key-release/sharing binding; không tự thay immutable data AAD |
| kem_ciphertext hoặc abe_ciphertext | Nếu profile sử dụng; bounded parser |
| wrap_nonce, wrapped_dek, wrap_tag | DEM wrap output và integrity |
| issuer_id, issued_at, manifest_signature | Authenticity/provenance; signature không tự bảo đảm currentness |

**Không dùng một version cho mọi thứ.** data_version thay khi dữ liệu thay; capsule_version khi rewrap; policy_bundle_version khi ABAC rule thay; search_epoch khi index key thay; abe_epoch khi nhóm thuộc tính thay. Đổi ABAC policy không mặc nhiên đổi data_policy_version đã nằm trong AAD. Nếu muốn đổi immutable AAD, re-encrypt bằng fresh DEK/nonce.

### 3.2 Canonicalization và domain separation

Chọn một encoding deterministic có spec, ví dụ deterministic CBOR hoặc JSON Canonicalization Scheme qua implementation có kiểm thử. Không tự nối chuỗi bằng dấu gạch hoặc dùng JSON dump tùy ý giữa hai ngôn ngữ. Typed fields và length framing phải loại bỏ ambiguity, Unicode/number normalization được chốt. Đặt byte-length limits trước parser/library; không deserialize pickle hoặc object arbitrary từ cloud.

Data AAD là canonical encoding của domain = medshare/data/v1; format/data suite; tenant/object kind/record/field; data_version; data_policy_version; dek_id. Không đưa capsule_version, mutable wrap_key_version hoặc signature bytes vào data AAD nếu muốn key-only rewrap.

Wrap AAD là domain riêng medshare/wrap/v1; full bound data context/digest; capsule ID/version; wrap suite/key ID/version; policy/recipient digest. Nếu suite đổi, wrap AAD đổi và phải tạo wrap ciphertext/tag mới.

Expected AAD phải được tái tạo từ **nguồn tin cậy**. Đọc envelope rồi dùng toàn bộ header tự khai làm AAD chỉ kiểm tra internal consistency, không chống full-record swapping. Kiểm tra digest/version với trusted registry, và bind request tenant/record/field trước decrypt.

## 4. Write/read protocol của P1

### 4.1 Write mới hoặc update

1. Gateway xác thực identity và workflow; giải quyết tenant từ identity, lấy object labels/version từ registry; không nhận quyền từ request body.
2. PDP kiểm tra WRITE_FIELD theo từng field; expected_version/CAS ngăn lost update. Reserve unique operation ID và pending version trong trusted journal.
3. SDK sinh fresh 32-byte DEK và 12-byte nonce cho mỗi changed field. CSPRNG failure phải abort, không dùng time/random seed/dataset seed fallback.
4. Tạo immutable AAD; encrypt bằng high-level AEAD API. Bọc DEK qua KMS bằng authenticated wrap context; tạo capsule/manifest, không lưu plaintext DEK ra file.
5. Ghi ciphertext/capsule vào DB theo transaction/atomic document update. Registry chuyển pending → committed với hash/version khi lưu thành công. Vì hai store không có distributed transaction mặc định, dùng journal và reconciliation; pending state không được phục vụ như current.
6. Khi timeout chưa rõ commit: retry theo idempotency ID với đúng envelope bytes đã lưu pending, hoặc hủy/reconcile rồi cấp fresh DEK/version. Không sinh plaintext mới dưới cặp key/nonce cũ.
7. Audit metadata; xóa reference key/plaintext transient trong giới hạn runtime. Sanitized errors, không log envelope chứa key material riêng.

Nếu crash giữa DB commit và registry commit, reader từ chối current không nhất quán; recovery job xác minh signed pending manifest rồi hoàn tất hoặc quarantine. Chấp nhận temporary unavailability để không nhận dữ liệu không rõ phiên bản.

### 4.2 Read có cấp khóa

1. Xác thực session, scope, authoritative object labels và requested field projection.
2. PDP quyết định; deny/error → không request key. Với search: cấp search capability/key use đúng tenant/field trước tạo token, rồi lọc quyền theo từng kết quả.
3. Đọc ciphertext/capsule từ DB; validate schema/size, known suites, current manifest hash/version ở Z1.
4. Broker xác thực service và bound user request; tự kiểm tra PDP/current policy/revocation epoch. Không accept boolean permit do caller gửi làm quyết định cuối.
5. Broker unwrap đúng capsule dưới key ID/context được allowlist. Cấp DEK qua internal authenticated confidential channel chỉ cho gateway tin cậy.
6. SDK verify AEAD dưới trusted AAD; chỉ sau tag thành công mới trả plaintext các field được phép. Hết thời gian/exception → không partial plaintext/debug dump.
7. Ghi correlation ID của PDP decision, key-use và response category.

**Revocation race:** serialize key-release authorization với revocation epoch commit trong trusted state (lock/transaction hoặc compare-and-check tương đương). Điểm tuyến tính hóa là lúc quyền release được commit. Request đã được cấp trước thời điểm revoke có thể hoàn tất; request sau commit phải deny. Không hứa dừng plaintext đã được cấp giữa flight hoặc ngoài hệ thống.

## 5. ABAC, stale state và nguồn context

- JWT/OIDC nếu dùng: verify chữ ký bằng issuer allowlist/JWKS được xác thực; issuer/audience/expiry/not-before; không trust algorithm từ token tùy ý. Token hợp lệ không tự chứng minh attributes còn current; broker/PDP đọc active/epoch cho quyền nhạy cảm.
- Purpose được bind vào approved workflow ticket/assignment, không chỉ chuỗi do client khai. Emergency cần incident approval có actor/scope/expiry và step-up marker từ IdP; nếu mô phỏng nguồn này phải ghi simulation.
- Policy bundle signature được kiểm tra trước load; current minimum version ở registry. Signed old policy vẫn reject sau cutover.
- Labels ở DB có thể lộ hoặc sửa. Registry có trusted record/label mapping và digest. Không đọc clinical field rồi mới quyết định ai có quyền nhận field đó ở API.
- Audit deny/error không ghi value tìm kiếm, diagnosis, token, private key hoặc credential. Hash low-entropy plaintext cũng có thể lộ; dùng opaque IDs, không coi hashing là ẩn danh tuyệt đối.

## 6. Equality query và leakage contract

### 6.1 Cấu trúc tối thiểu

Token = HMAC với search key riêng theo tenant/field/search_epoch, trên canonical tuple(domain, tenant, field, normalization_version, normalized typed value). Output dùng đủ 32 byte. AEAD ciphertext luôn randomized; deterministic token là **chỉ mục bổ sung**, không deterministic encryption của field.

Normalization: Unicode NFC cho chuỗi; external ID có quy tắc case rõ; email demo lower-case theo convention của synthetic dataset, không tự suy ra mọi mailbox thực tế case-insensitive; số là integer typed, không format float/string tùy ý. Store normalization_version trong index và query plan; đổi rule cần rebuild.

SQL compound index hoặc Mongo index trên tenant/field/epoch/token; response record IDs + encrypted fields. Decrypt và kiểm tra equality plaintext tại trusted gateway để loại collision/stale wrong candidate; report chi phí post-filter. Điều này không tìm được row bị server bỏ sót, nên không có completeness claim trước T-10.

### 6.2 Leakage function đã chấp nhận

- Setup: schema, tenant groups, record IDs, field/index existence, ciphertext length; frequency histogram/token equality trong mỗi domain.
- Search: repeated token linkage, matching record IDs, result cardinality, timing/size; current set of rows touched.
- Update: thời điểm insert/update/delete, stable IDs và token equality theo epoch; đối thủ có thể liên kết trước/sau qua record ID/timing.
- Không chủ động cung cấp order token, nhưng không khẳng định không thể suy luận order bằng auxiliary information. Không claim forward-private/backward-private SSE.
- Bị lộ search key hoặc chosen-input oracle thì dictionary attacks mạnh hơn passive frequency model; báo cáo model riêng, không trộn với no-key model.

P1 core chỉ index external ID/email nếu cần. Diagnosis categorical index chỉ trong experiment kiểm soát để minh họa tại sao low-entropy sensitive fields không nên index mặc định. Không quảng bá blind index là MongoDB Queryable Encryption.

## 7. CP-ABE KEM/DEM research profile P2

### 7.1 Mục tiêu, thư viện và thông số cần xác minh

Dùng CP-ABE để chia sẻ encrypted export cho nhiều người nhận theo điều kiện ổn định. Candidate có tồn tại là Charm CPabe_BSW07; trước dùng cần đọc implementation, exact paper/security model, backend/group serialization, group membership checks, maintained status và parameter security. Default example SS512 không là bằng chứng đạt 128-bit; **không dùng tên đó để claim an toàn triển khai thực tế**. Nếu chỉ chạy được profile mức demo, ghi nhãn research demonstration và không đưa vào production recommendation.

API adapter dự kiến: setup, issue_user_key, encrypt_key_capsule, decrypt_key_capsule, serialize/parse; đây là interface thiết kế, không giả định chữ ký hàm thư viện. Mapping tới library functions phải xác minh trong spike trước code.

### 7.2 Construction và policy

1. AA tạo master secret/public parameters và authenticated public descriptor cho một sharing domain. Master secret không ở DB/KMS cloud.
2. Data owner tạo export manifest đã được ABAC phê duyệt và fresh independent share DEK; dùng AES-GCM mã hóa export.
3. Vì một số CP-ABE API nhận phần tử nhóm đích, chọn random secret Z trong message space được scheme hỗ trợ; CP-ABE encrypt Z dưới policy. Không truyền tùy ý raw 32-byte DEK vào API chỉ chấp nhận group element.
4. Derive wrap key từ canonical serialization của Z bằng KDF với domain riêng, authenticated policy/parameter/tenant/share context. AEAD wrap share DEK dưới key này.
5. Sign manifest chứa digest ABE ciphertext, AEAD-wrapped key, parameter/authority IDs, canonical policy, share/data context, epoch và suite IDs. Recipient verify manifest/trust anchor/bounds trước pairing/decrypt; policy key release không dựa chuỗi tự sửa.
6. Recipient dùng **một user-bound attribute secret key** để recover Z, derive wrap key, unwrap DEK và AEAD decrypt data. Public error không lộ chi tiết pairing/key oracle.

Ví dụ policy ổn định: TENANT_H1 AND EPOCH_07 AND ((ROLE_DOCTOR AND DEPT_CARDIOLOGY) OR ROLE_REVIEWER). Tất cả token được chuẩn hóa theo grammar AND/OR/parentheses allowlist. BSW-style monotone access structure không tự có NOT, so sánh clearance số hay ngữ nghĩa đồng hồ; nếu biểu diễn clearance cần mapping attributes và test riêng.

Không đưa emergency=true, time_now hoặc purpose=treatment vào ABE như thể giải quyết được context động offline. CP-ABE chỉ chứng minh khả năng giải mã theo key attributes; ABAC kiểm soát download/issue/reissue, không kiểm soát động cơ người nhận sau khi đã có key/ciphertext.

### 7.3 Collusion test đúng bản chất

AA cấp U1 = tenant H1, epoch 07, role doctor, dept neurology; U2 = tenant H1, epoch 07, role nurse, dept cardiology. Mỗi key riêng không thỏa nhánh doctor AND cardiology, nhưng union tên thuộc tính thì thỏa. Thử decrypt riêng, ghép các thành phần serialized key theo parser/backend cho phép, và xác nhận không recover đúng secret/DEK. Có U3 = doctor+cardiology làm positive control.

**Không** gọi AA keygen trên union rồi kết luận scheme “không chống collusion”: AA tạo một key hợp lệ mới từ master secret là một capability khác. Ngược lại, chỉ từ chối list hai key ở wrapper chưa đủ để test cryptographic collusion; cần test component mixing qua research harness và trình bày giới hạn. Negative result thực nghiệm không chứng minh toán học; viện dẫn security theorem đúng scheme/model.

### 7.4 Epoch, revoke và data policy change

- Khi revoke: ABAC/AA chặn download/key issuance mới; tăng epoch, chỉ cấp keys epoch mới cho non-revoked users.
- Dữ liệu/share mới dùng fresh share DEK và policy epoch mới. Người giữ key epoch cũ không giải mã artifact mới.
- Rewrap **cùng DEK** dưới policy mới không thu hồi người đã biết DEK. Muốn bảo vệ current/future export trước người đó phải fresh DEK + re-encrypt; bản cũ họ đã giữ vẫn đọc được.
- Ghi chính xác số user reissued keys, capsule bytes, rows/bytes re-encrypted, downtime và residual access. Không có “thu hồi tuyệt đối sau X giây” đối với offline copies.
- Một fallback KMS capsule cùng share DEK cho DBA sẽ phá mục đích độc lập ABE. P2 artifact không xuất kèm alternate non-policy wrapper. Trusted owner có plaintext gốc là trust assumption, không “zero trust” tuyệt đối.

## 8. BFV aggregate profile P3

### 8.1 Query semantics và tham số

Một query SUM(amount_units) và count trên **cohort được phê duyệt trước**, cùng tenant. amount_units là số nguyên không âm 0–1000; cohort tối đa 10.000 record trong profile này, nên tổng tối đa 10.000.000. Không dùng floating-point currency hoặc từ “exact” khi có overflow modulo.

SEAL BFV: polynomial modulus degree 8192; coefficient modulus do library-supported default tương ứng mức 128-bit chọn; batching plaintext prime khoảng 30 bit, thỏa t ≡ 1 mod 2N và **t > N_records × max_amount**. Xác minh giá trị t thực tế, security-level parameter check và noise budget trên job lớn nhất. Không vô hiệu security checks để chạy nhanh. Lưu toàn bộ parameters (không secret) trong run manifest. Nếu không dùng API Batching/default đúng release, phải kiểm tra tương đương trước code.

### 8.2 Flow và computation boundary

1. Trusted owner lập cohort manifest (tenant, approved record/version IDs, count, parameter hash) và materialize integer values từ nguồn được phép. Authorization của owner khác analyst chỉ nhận scalar.
2. Owner tạo BFV keypair và Galois/evaluation keys cần thiết; secret key chỉ tại owner. Encode batches có slot padding zero theo manifest, encrypt và gửi worker.
3. Worker cộng ciphertext batches theo slot, rồi dùng rotations/additions để reduce tổng hai hàng batching slots về cùng một giá trị ở các slots. Với batching SEAL có hai hàng, phải xử lý cả row rotations và column swap; chỉ reduce một hàng là bug cần test. Không cần multiplication/relinearization cho SUM nếu không dùng chúng.
4. Worker trả encrypted total, count/manifest reference và operation metadata. Count có thể công khai do server thấy cohort size; nếu encrypt count để minh họa, không claim che count khỏi observer khi volume đã lộ.
5. Owner decrypt total, kiểm tra parsing/parameter IDs và miền số, rồi công bố scalar theo policy cho analyst. Test oracle độc lập so exact result với plaintext sum; **oracle là dụng cụ đánh giá, không phải integrity mechanism của deployment**.

Chi phí bao gồm encoding/encryption, public evaluation key sizes, upload, worker rotations/add, download và decrypt; không chỉ report add time. Cohort selection ở trusted side phải tính chi phí riêng, không nói BFV thực hiện encrypted WHERE/range/join.

### 8.3 Integrity và inference limitations

BFV ciphertext cố ý malleable. Public/evaluation keys không cho decrypt nhưng có thể cho attacker tạo ciphertext tổng giả hợp lệ. Chữ ký của input manifest xác thực tập input, không chứng minh worker đã tính đúng. Test malicious result chỉ ra output sai có thể được decrypt thành công. Không claim verifiable computation nếu chưa thêm proof/recompute/quorum tin cậy.

Analyst có thể suy luận dữ liệu cá nhân bằng các aggregate rất nhỏ hoặc differencing giữa các cohort. MVP áp dụng approved fixed cohorts, minimum cohort size 10 và kiểm soát query lặp; **k-minimum không phải differential privacy** và không loại trừ toàn bộ differencing. Owner được phép thấy raw input; analyst không có HE secret/decrypt oracle. Không phục vụ tùy ý ciphertext do client nộp để tránh chosen-ciphertext oracle.

## 9. PQC key/signature profile P4

### 9.1 Construction KEM/DEM có authentication

ML-KEM encapsulation tạo shared secret và KEM ciphertext; không mã hóa bản ghi trực tiếp. Recipient public descriptor chứa subject/tenant/purpose/key ID/version/algorithm/expiry/public key và được provision bằng pinned trust anchor hoặc chuỗi xác thực đáng tin. Kiểm tra descriptor trước encapsulation, không lấy public key cùng ciphertext từ DB rồi tự tin.

Sender encapsulate với ML-KEM-768 public key, lấy shared secret. HKDF derive wrap key 32 byte với public salt và info domain medshare/pq-wrap/v1, descriptor digest, sender/recipient IDs, capsule/data context, KEM ciphertext digest, suite IDs. AEAD wrap **independent archive DEK**; bulk archive dùng AES-256-GCM. Sender ký full canonical capsule/manifest bằng ML-DSA-65. Recipient verify issuer, signature, current allowed versions, schema/bounds, rồi decapsulate/derive/unwrap/decrypt.

Shared secret không lưu/log. KEM ciphertext cùng manifest là public nhưng còn metadata privacy. Không dùng ML-DSA private key làm KEM key hoặc reuse HKDF output làm data DEK/search key. Authentication của người phát/request vẫn cần channel/identity; KEM đơn độc không chứng minh ai gửi.

**Implicit rejection:** ML-KEM với ciphertext đúng chiều dài nhưng invalid có thể decapsulate thành secret thay thế mà không báo lỗi trực tiếp. Test phải kỳ vọng toàn protocol không trả plaintext (signature hoặc DEM tag fail), không mặc định API decapsulation luôn throw exception. Không phân biệt lỗi chi tiết để tạo oracle.

### 9.2 Kích thước chuẩn và số liệu đo

ML-KEM-768 trong FIPS 203 có encapsulation key 1184 byte, decapsulation key 2400 byte, ciphertext 1088 byte, shared secret 32 byte. ML-DSA-65 có public key 1952 byte, private key 4032 byte, signature 3309 byte. Đây là **kích thước raw theo chuẩn**, không phải benchmark đã chạy; serialized package/certificate/base64 còn overhead. Khi implementation dùng container format khác phải report cả raw và wire bytes và đối chiếu chuẩn/errata.

Đo keygen/encap/decap/sign/verify riêng, warm-up, distribution/cycles khi counter có sẵn; đo end-to-end cấp capsule, verify policy và migration. Không so performance của research CP-ABE ở mức security thấp với ML-KEM category 3 như cùng mức an toàn.

### 9.3 Migration và PQ claim

E8 baseline archive có thể dùng classical RSA-OAEP với SHA-256 trong library chuẩn (RSA 3072-bit, plaintext DEK 32 byte), hoặc authenticated classical key-wrap profile đã chốt; chọn một baseline và không thay giữa runs. Không gọi RSA-OAEP là KEM tương đương formal. P4 final dùng KEM/DEM đã nêu.

Migration states: planned → prepared → explicitly allowed dual-read → rewrap → verify → cutover → retired → destruction-eligible. Ghi signed plan, version allowlist, counters/checkpoints, per-capsule CAS và idempotent retries. New writes dùng new suite; readers chỉ dùng suite ID đã xác thực, không thử tuần tự mọi private key/algorithm khi fail.

- **Key-only rewrap:** owner lấy DEK từ old capsule, tạo new PQ capsule; data ciphertext/AAD/digest không đổi. Test hash ciphertext trước/sau bằng nhau và new key decrypt đúng.
- **Downgrade resistance:** unknown, mismatched hoặc retired suite/key/policy version → reject. Không “fallback cho tương thích” nếu chưa có migration state cho phép.
- **Historical weakness:** nếu attacker đã giữ old classical capsule, rewrap hôm nay không xóa nó. Ngay cả fresh-DEK re-encryption hôm nay cũng không cứu plaintext tương ứng của old snapshot đã bị harvest. Chỉ dữ liệu mới độc lập không bị old-key derivation/reuse và không có old alternate decrypt path có thể có claim dài hạn mạnh hơn.
- **Dual wrap OR:** trong thời kỳ cả old/new capsule còn dùng được, confidentiality bị giới hạn bởi đường yếu nhất. Không mô tả dual-wrap OR là hybrid AND security.
- **Không mặc định forward secrecy:** long-lived KEM private key bị lộ cho phép decapsulate historical capsules; ML-KEM tự nó không authenticated ephemeral session protocol.
- **Crypto inventory toàn đường:** TLS/certificates, IdP signing, KMS auth/backup, classical manifest signer, ABE exports, recovery escrows, search keys và bản plaintext gốc. CP-ABE cổ điển vẫn không PQ-safe. Mọi claim ghi “PQC key/signature prototype”, không “end-to-end PQ-secure cloud DBMS”.

Hybrid classical+PQ KEM chỉ là extension nếu có construction/protocol được chỉ định và thư viện tương thích; không tự nối hai shared secrets rồi gọi là chuẩn quốc tế.

## 10. Rotation, backup và operational failure

### 10.1 Những thao tác không được nhập nhằng

| Thay đổi | Có cần mã hóa lại bulk data? | Giới hạn |
|---|---|---|
| Rotate KEK/wrap key, giữ DEK/AAD | Không, chỉ tạo capsule/tag/manifest mới | Không chữa leaked DEK hoặc old capsule đã bị copy |
| Rotate DEK | Có cho field/export dùng key đó | Old plaintext/ciphertext + old key đã lộ không thu hồi được |
| Change mutable ABAC policy | Thường không | Phải cập nhật current policy/registry và recheck; offline copies không bị áp policy |
| Change immutable data_policy_version/AAD | Có | Không sửa header AAD rồi giữ nguyên tag |
| ABE epoch cho dữ liệu mới | Fresh share DEK/content profile | Reissue non-revoked keys; key cũ còn đọc old artifacts |
| Search key/normalization epoch | Rebuild index, không nhất thiết data cipher | Existing leakage/old index remains; dual index tăng leakage/overhead |
| Signing key | Re-sign manifests khi policy yêu cầu, không data encryption | Old trust root transition phải authenticated, chống rollback |

### 10.2 Backup/restore

B1 raw encrypted volume copy không kèm unlock material: restore không mount/read được. Logical dump từ DB đang chạy vẫn plaintext nếu B1-only, phải bọc backup độc lập; thực nghiệm phải minh họa khác biệt. P1 SQL dump/Mongo export chứa ciphertext cho protected fields, nhưng routing/tokens/metadata vẫn lộ.

Backup keys/KMS persistence ở miền và quyền riêng; encryption của backup key store cần independent recovery material không đặt cùng snapshot. Restore lab vào isolated target, không overwrite DB đang làm việc. Restore DB, KMS và registry theo compatible checkpoint; nếu registry mới hơn DB thì stale data bị reject, không hạ minimum version chỉ để demo pass. Recovery workflow phê duyệt dữ liệu restore thành version mới hoặc reconcile theo signed journal; audit cả quyết định.

Replication/CDC chỉ kéo ciphertext/metadata trong P1; connector không có decrypt privilege. Log/debug của driver và change stream phải kiểm tra không đưa plaintext trở lại. Backup/snapshot GC không có nghĩa xóa mọi bản đã bị attacker copy; cryptographic erasure chỉ áp dụng khi mọi bản key cần thiết thực sự bị hủy và không ai giữ plaintext.

### 10.3 Audit và parser/error hygiene

Audit chain gồm event hash, previous hash và signed checkpoint có sequence/count/time. Witness độc lập giữ checkpoint mới nhất để phát hiện truncation/replay; local hash chain một mình không phát hiện xóa cả suffix rồi replay checkpoint cũ. Logger bị compromise trước khi ghi có thể bỏ sự kiện, signer có thể ký lời nói dối; không gọi đây là non-repudiation pháp lý.

Bounds trước xử lý: request payload, number of fields, ciphertext/capsule bytes, attribute count/policy depth, HE parameter IDs/serialized size, query result size, timeout. Test resource limits ở lab bằng giá trị nhỏ, không gây DoS máy thật. Certificate/public-key/signature/tag lỗi → reject fail closed; public error nhất quán, internal metrics chỉ category/IDs.

Không xuất environment dump, Authorization header, cookies, secrets, private keys, raw clinical bodies hoặc full KMS responses ra command logs. File secret hạn chế quyền, stdin/config restricted thay argv; core dump/debug endpoint disabled. Side-channel analysis ở mức dependency/API/error/timing observation; không claim constant-time toàn Python/service.

## 11. Security-critical code walkthrough phải có trong báo cáo

Trình bày tối thiểu bảy đoạn code thật sau khi implement: trusted context resolution; ABAC/broker release; AAD canonicalization/AEAD usage; nonce/retry handling; signature/current-version check; ABE/PQC adapter composition; BFV parameter/serialization validation. Với mỗi đoạn ghi invariant, dependency signature đã xác minh, negative test tương ứng và failure behavior. Không chỉ chụp màn hình ciphertext rồi kết luận an toàn.

Trước đưa vào báo cáo: cập nhật exact library versions và parameters bằng kết quả feasibility/build; chạy TC liên quan ở [experiments-and-validation](../testing/experiments-and-validation.md); ghi [traceability](../testing/traceability-matrix.md). Chưa có bước nào ở tài liệu này là bằng chứng security test đã chạy.
