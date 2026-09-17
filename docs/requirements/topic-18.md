**CAPSTONE PROJECT - TOPIC 18**

**Cryptographic Data Protection, Fine-Grained Access Control  
and Post-Quantum Secure Query Architecture for Cloud DBMS**

_Bảo vệ dữ liệu, kiểm soát truy cập và truy vấn an toàn cho hệ quản trị CSDL SQL/NoSQL cloud-native_

| **ĐỊNH HƯỚNG CỐT LÕI**                                                                                                                                                                                                                                                                                                                                                                                                              |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Đề tài không yêu cầu xây dựng một DBMS mới. Sinh viên phải phân tích kiến trúc, threat model và các luồng dữ liệu/truy vấn; sau đó lựa chọn đúng lớp bảo vệ: mã hóa volume/database, mã hóa field/client-side, ABAC, CP-ABE, searchable/queryable encryption, TEE/FHE và lớp quản lý khóa/chính sách sẵn sàng cho PQC. Mọi khẳng định về bảo mật phải được liên kết theo chuỗi: requirement -> mechanism -> experiment -> evidence. |

|**From**|**To**|
|---|---|
|"Encrypt the database with AES"|Layered data protection + policy-enforced access + secure query|
|DB-centric roles only|Subject/object/action/environment attributes + row/column/field enforcement|
|AES as access-control mechanism|AES/AEAD for confidentiality; ABAC/CP-ABE for authorization semantics|
|One security boundary|Client, application, DBMS, KMS/HSM, policy engine, attribute authority, cloud admin|
|Classical key wrapping only|PQC-ready key distribution, signatures and crypto-agility|

Course: NT219/NT2205 - Cryptography | Level: Bachelor / Master | Recommended duration: 12 weeks

Primary systems: PostgreSQL / SQL Server / MongoDB (or equivalent managed SQL/NoSQL).
# 1. Project Synopsis

Đề tài nghiên cứu cách sử dụng mật mã như một thành phần của kiến trúc bảo vệ Cloud DBMS, thay vì xem mã hóa là một tính năng độc lập. Sinh viên bắt đầu từ phân loại dữ liệu, chủ thể, ranh giới tin cậy (trust boundary) và các truy vấn cần hỗ trợ; sau đó thiết kế một hệ phân cấp bảo vệ (protection hierarchy) từ mã hóa volume/database đến mã hóa field/client-side, kiểm soát truy cập chi tiết, kiểm soát truy cập bằng mật mã và truy vấn an toàn.

Hai nhóm mục tiêu phải được phân biệt rõ: (i) tính bí mật/toàn vẹn của dữ liệu (data confidentiality/integrity) và (ii) ngữ nghĩa cấp quyền/truy vấn (authorization/query semantics). AES/AEAD là cơ chế phù hợp để bảo vệ byte hoặc bản ghi khi khóa được quản lý đúng, nhưng AES không thể biểu diễn chính sách kiểu “bác sĩ A được xem trường chẩn đoán của bệnh nhân thuộc khoa B trong giờ làm việc”. Các quyết định như vậy cần ABAC/NGAC hoặc policy engine; nếu cần cưỡng chế chính sách trực tiếp trên bản mã, kể cả trước DBA/cloud operator, có thể nghiên cứu CP-ABE/attribute encryption theo mô hình lai KEM/DEM [2,4].

**_Data protection != Access control != Secure query_**

**_C_data = AEAD_Encrypt(DEK, Plaintext, AAD)_**

**_Permit = Policy(SubjectAttr, ObjectAttr, Action, Environment)_**

**_C_DEK = CP-ABE_Encrypt(Policy, DEK)   [research / advanced track]_**

# 2. Learning Objectives
1.  Phân tích các lớp mã hóa trong Cloud DBMS: disk/volume, file/tablespace, TDE, column/field, client-side và application-level envelope encryption.
2.  Phân biệt tính bí mật/toàn vẹn do AES/AEAD cung cấp với authentication, authorization, access control và chính sách chia sẻ dữ liệu (data-sharing policy).
3.  Thiết kế ABAC/NGAC cho SQL/NoSQL theo các thuộc tính subject-object-action-environment; kiểm tra khả năng cưỡng chế ở mức row/column/field.
4.  Hiểu CP-ABE/KP-ABE và cách sử dụng ABE để bảo vệ DEK thay vì mã hóa trực tiếp từng bản ghi bằng một primitive khóa công khai.
5.  Phân tích truy vấn trên bản mã: deterministic/searchable encryption, SSE/queryable encryption, rò rỉ thứ tự/phạm vi (range/order leakage), TEE và FHE.
6.  Thiết kế hệ phân cấp khóa (key hierarchy), KMS/HSM, rotation, revocation, phân tách tenant và bảo vệ backup/replication.
7.  Xây dựng kiến trúc dữ liệu/khóa sẵn sàng cho PQC với ML-KEM, ML-DSA và crypto-agility; phân biệt các chuẩn PQC đã ban hành với lattice-based ABE còn ở giai đoạn nghiên cứu.
8.  Đánh giá phạm vi bảo vệ (security coverage), mức rò rỉ (leakage), tính đúng đắn của truy vấn, p50/p95/p99, QPS, chi phí lưu trữ/index, chi phí thao tác khóa/chính sách và khả năng phục hồi vận hành.
# 3. System Analysis: Assets, Actors, Trust Boundaries and Data Flows
## 3.1 Assets and secure objects

| **Class**                 | **Examples**                                   | **Primary requirement**                               |
| ------------------------- | ---------------------------------------------- | ----------------------------------------------------- |
| Public/low sensitivity    | catalog/reference data, schema metadata        | Integrity, availability                               |
| Sensitive fields          | PII, salary, diagnosis, account identifiers    | Field confidentiality + fine-grained access           |
| Transactional state       | orders, balances, workflow state               | Integrity + authorization + concurrency correctness   |
| Searchable sensitive data | email, name, range values, tags                | Confidentiality + bounded leakage + query correctness |
| Keys and policy secrets   | CMK/KEK/DEK, ABE master secret, attribute keys | Non-exportability / least privilege / rotation        |
| Evidence                  | audit, policy decision, key-use logs           | Integrity, provenance, retention                      |
## 3.2 Actors and trust zones
·        End user / data owner / analyst / service account.
·        Client SDK or application service that may encrypt/decrypt selected fields.
·        API/service tier and query middleware.
·        DBMS engine, DBA and managed-cloud control plane.
·        KMS/HSM and key broker.
·        Policy Decision Point (PDP), Policy Enforcement Point (PEP), attribute sources / Attribute Authority.
·        Optional searchable-encryption index service, TEE/confidential query worker or FHE service.
·        Backup/replication/CDC/analytics pipeline and SIEM.

| **Threat-model rule**                                                                                                                                                                                                                                                                                                                                                |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TDE assumes the DB engine can see plaintext during normal operation. Client-side/field encryption changes that trust assumption. CP-ABE changes it further by embedding access policy into cryptographic protection. Secure query mechanisms trade functionality, leakage and cost differently; therefore there is no single "most secure" layer for every workload. |
## 3.3 Required data/query flows

|**Flow**|**Description**|**Security questions**|
|---|---|---|
|F0|Key/attribute provisioning|Who creates CMK/DEK/ABE keys? Where are private inputs stored?|
|F1|User/workload authentication|How is identity established before DB/API access?|
|F2|Authorization decision|Which subject may perform which action on which row/field and context?|
|F3|Write path|Where is plaintext visible? Who encrypts? What AAD binds tenant/table/field/version?|
|F4|Point/equality query|Can DB compare ciphertext? What equality/frequency leakage occurs?|
|F5|Range/text query|What order/search/access-pattern information is revealed?|
|F6|Aggregation/join|Client-side, enclave, HE/FHE, or controlled plaintext?|
|F7|Backup/replication/CDC|Are snapshots, logs and replicas protected under correct key domains?|
|F8|Rotation/revocation|How are keys/policies changed without uncontrolled plaintext exposure?|
|F9|Audit/SIEM|Can key use and policy decisions be proven without logging plaintext?|
# 4. Protection Hierarchy: From Coarse-Grained Encryption to Cryptographic Access Control

| **Layer** | **Mechanism**                          | **Protects against**                                       | **Does NOT solve**                                                  |
| --------- | -------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------- |
| L0        | Disk/volume encryption                 | Lost disk, detached volume, raw snapshot theft             | DBA/admin/query misuse; row/field policy                            |
| L1        | DB/TDE/tablespace encryption           | DB files, logs/backups at rest when keys separated         | DB engine compromise; authorized-but-curious DBA                    |
| L2        | Column/field encryption                | Selected sensitive columns/fields                          | Fine-grained authorization by itself; query functionality           |
| L3        | Client-side encryption + envelope keys | Cloud/DB operator may not see plaintext                    | Dynamic policy and encrypted search unless additional mechanisms    |
| L4        | ABAC/NGAC/RLS/field policy             | Fine-grained logical authorization                         | Confidentiality from DB/admin if enforcement layer can decrypt      |
| L5        | CP-ABE / attribute encryption          | Cryptographic one-to-many policy enforcement               | Efficient general SQL; easy revocation; mature PQ standardization   |
| L6        | SSE/queryable encryption               | Selected queries without plaintext-at-server               | All leakage; arbitrary SQL                                          |
| L7        | TEE / secure enclave query             | Rich query over plaintext in attested protected memory     | TEE side channels / TCB / attestation risks                         |
| L8        | HE/FHE/MPC                             | Computation without plaintext disclosure to compute server | Low-cost general OLTP; simple operations and engineering            |
| L9        | PQC key/policy layer                   | Quantum-resistant key establishment/signatures             | Does not automatically make classic CP-ABE or DB encryption PQ-safe |
## 4.1 Why AES alone is not access control
AES-256 with an authenticated mode is appropriate for bulk database encryption. The problem is not that AES is "weak"; the problem is that a symmetric key represents possession of a secret, not a rich authorization policy. If every application process receives the same AES key, every process with that key can potentially decrypt every protected value. Therefore key distribution becomes the de facto access-control system, usually with poor granularity and difficult revocation.

**_AES key possession -> decryption capability; it does not encode subject/object/action/environment policy_**

Recommended pattern: use AEAD for data and a separate policy/key-release layer. At minimum, separate keys by tenant / data class / purpose. For high-value fields, derive or issue short-lived DEKs only after an authorization decision, or wrap the DEK under a policy-controlled cryptographic mechanism.
## 4.2 Envelope encryption model

**_DEK <- CSPRNG;   C = AEAD_Encrypt(DEK, P, AAD)_**

**_WrappedDEK = KMS_Encrypt(KEK, DEK)_**

AAD should bind non-secret context such as tenant_id, table/collection, field name, record/version identifier and crypto-policy version. This prevents ciphertext from being silently moved to another context and accepted as valid.
# 5. Fine-Grained Authorization: ABAC, NGAC and CP-ABE
## 5.1 ABAC/NGAC as the logical policy plane
NIST SP 800-162 defines ABAC using attributes of subject, object, requested operation and environment [1]. For database systems this can be implemented in application middleware, API gateway, query proxy, DB row-level security, or directly in/near the DB engine. NIST IR 8611 (August 2026) is particularly relevant: m-NGAC embeds fine-grained NGAC enforcement within the database down to column data, reducing dependence on the calling application or SQL tool [4].

**_Permit(s,o,a,e) = Policy(Attr_s, Attr_o, Action_a, Env_e)_**

|**Attribute class**|**Examples for DBMS**|
|---|---|
|Subject|role, department, clearance, tenant, project, device posture|
|Object/resource|table, column, row owner, sensitivity, tenant, retention class|
|Action|SELECT, INSERT, UPDATE, DELETE, EXPORT, DECRYPT, AGGREGATE|
|Environment|time, region, network zone, incident state, purpose-of-use, risk score|
## 5.2 CP-ABE as a cryptographic policy plane
In Ciphertext-Policy Attribute-Based Encryption, the ciphertext carries an access policy and the user secret key carries attributes. Decryption succeeds only when the attributes satisfy the policy. NIST IR 8450 discusses attribute-encryption based access control as a one-to-many cryptographic authorization mechanism [2]. For database use, CP-ABE should normally protect a DEK or a small key capsule, not megabytes of database rows directly.

**_Policy P = (role = doctor AND dept = cardiology) OR emergency = true_**

**_C_DEK = CPABE_Enc(P, DEK);   Data = AEAD_Enc(DEK, record, AAD)_**

| **Important limitation**                                                                                                                                                                                                                                                                                                                                                                                        |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Classical CP-ABE implementations commonly rely on bilinear pairings / discrete-log assumptions and are not post-quantum. Lattice/LWE-based ABE is an active research direction, including new general frameworks (2024) and more expressive ABE from lattice assumptions (2025), but it is not a NIST-standardized drop-in replacement. Treat PQ-ABE as an advanced research track, not as production standard. |
## 5.3 ABAC + CP-ABE hybrid logic

|**Decision stage**|**ABAC/NGAC role**|**CP-ABE role**|
|---|---|---|
|Request time|Evaluate dynamic attributes, context, action, risk, purpose|Not ideal for rapidly changing online context|
|Ciphertext persistence|Policy metadata may guide DB filtering|Enforces a durable cryptographic access condition on the DEK|
|Revocation|Immediate deny at PDP/PEP|Needs epoch/time attributes, re-key, proxy update or other revocation design|
|DB/admin compromise|May be bypassed if attacker controls enforcement engine|Ciphertext remains protected if ABE secret material is outside DB|
|Auditability|Produces explicit decision and policy trace|Proves only cryptographic decryptability, not business-purpose correctness|
# 6. SQL and NoSQL Architecture Patterns
## 6.1 Pattern A - Baseline full-volume / TDE
Deploy PostgreSQL/SQL Server/managed DB with encrypted storage, backups and TLS. This is a necessary baseline for most cloud databases, but the report must state its trust model: the DB engine and identities that can legitimately execute queries still see plaintext. Benchmark mainly operational overhead, key rotation and backup/restore behavior.
## 6.2 Pattern B - Client-side field encryption + KMS + ABAC
Sensitive fields are encrypted in a client SDK or trusted service before reaching the DB. The DB stores ciphertext; the application requests a DEK only after ABAC approval. This pattern is practical for fields that are rarely queried, exported or searched. SQL and NoSQL schemas should be compared because document stores often make field-level encryption easier to integrate but have different native access-control capabilities [3].
## 6.3 Pattern C - SQL: Always Encrypted / secure enclave
Microsoft Always Encrypted protects selected columns from highly privileged DB/server administrators by keeping keys and plaintext outside the normal Database Engine path. With secure enclaves, richer confidential computations and in-place cryptographic operations can be performed inside a protected memory region [13]. This is an excellent implementation track for showing the trade-off between client-side confidentiality and query functionality.
## 6.4 Pattern D - NoSQL: MongoDB Queryable Encryption
MongoDB Queryable Encryption encrypts fields on the client side and supports queries over randomized encrypted data. Current production support covers equality and range queries; text-oriented prefix/suffix/substring query modes are still documented as preview features in the current manual [12]. The server does not need plaintext keys, but encrypted-query indexes and metadata add storage/write overhead and the scheme still has a defined leakage profile.
## 6.5 Pattern E - CP-ABE wrapped field/tenant DEKs
Use this as a research-oriented data-sharing layer: each sensitive dataset/field family has a DEK. The DEK is wrapped under a CP-ABE policy such as department, clearance and tenant. A conventional ABAC engine still handles dynamic session/action/context conditions. This design demonstrates how cryptography can enforce data sharing beyond ordinary DB GRANT/RBAC.
## 6.6 Pattern F - TEE/FHE for selected secure query
Use TEE for joins/aggregates that cannot be supported efficiently on ciphertext, or use HE/FHE for narrowly defined arithmetic analytics. Full FHE is not a default replacement for OLTP. The project must define exactly which queries are delegated to encrypted compute and what leakage / trust remains.
# 7. Secure Query: Functionality, Leakage and Cost

|**Query need**|**Candidate mechanism**|**Main leakage / limitation**|**Recommended use**|
|---|---|---|---|
|Exact equality|Deterministic encryption or modern queryable/SSE scheme|Equality/frequency or structured index leakage|IDs/tags with controlled domain; prefer purpose-built QE|
|Range|ORE/OPE, range-query QE, TEE|Order/distribution leakage or heavier index|Use only when business need justifies leakage|
|Prefix/text|SSE / queryable text index|Search/access pattern, index overhead|Document search; measure repeated-query leakage|
|Join|Deterministic tokenization, TEE, client-side join|Equality linkage or transfer cost|Narrow joins on stable identifiers|
|SUM/AVG/count|TEE, HE/CKKS/BFV/BGV, partial client compute|TEE trust or HE compute/accuracy cost|Analytics, not general OLTP|
|Arbitrary SQL|TEE/confidential DB|TCB, side channel, attestation, memory/IO|When rich SQL is required over protected plaintext|
## 7.1 Leakage catalogue
·        Equality leakage: two ciphertext/index tokens correspond to the same logical value.
·        Frequency leakage: histogram of encrypted values can correlate with predictable plaintext distributions.
·        Order leakage: relative ordering of protected values is visible.
·        Search pattern: repeated queries can be linked.
·        Access pattern: server sees which records are touched.
·        Volume/size/timing: result size, record length and query timing reveal information.
·        Update pattern: inserts/deletes may reveal relationships over time.
**_Secure-query evaluation = Correctness + Performance + Explicit Leakage Profile_**
# 8. Post-Quantum and Crypto-Agile DBMS Protection
## 8.1 What quantum computing changes - and what it does not
A future large-scale quantum computer threatens RSA/ECC-based key establishment, signatures and classical pairing-based ABE. It does not imply that AES must be replaced: symmetric cryptography remains appropriate with adequate key size (AES-256 is a natural long-term baseline). Therefore the PQ migration target for cloud DBMS is mainly key establishment/wrapping, service identity, signatures, certificate chains and any public-key-based policy encryption.
## 8.2 Recommended standardized PQC layer

| **Function**          | **Current recommendation**                  | **DBMS role**                                                                            |
| --------------------- | ------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Key encapsulation     | ML-KEM (FIPS 203)                           | Establish/wrap session or tenant key material between clients, key broker and services   |
| Digital signature     | ML-DSA (FIPS 204)                           | Sign policy bundles, DB migration packages, audit checkpoints, key-rotation approvals    |
| Alternative signature | SLH-DSA (FIPS 205)                          | Conservative hash-based option for limited/offline signing where size/cost is acceptable |
| Future backup KEM     | HQC - selected 2025; standard not final yet | Crypto-agility research track; do not treat as production FIPS algorithm yet             |
|                       |                                             |                                                                                          |

**_PQC KEM -> shared KEK/session key -> AEAD for bulk DB data_**

Do not encrypt every record directly with ML-KEM. Use KEM/DEM: ML-KEM establishes or encapsulates a symmetric key; AES-GCM/another approved AEAD encrypts bulk data. NIST SP 800-227 provides KEM guidance [10].
## 8.3 Post-quantum ABE: research track
Recent lattice-based ABE work continues to improve expressiveness. A 2024 general framework systematizes lattice-based ABE constructions, while 2025 work constructs highly expressive ABE from lattice/LWE-family assumptions [19,20]. These works are useful for a Master-level survey/prototype, but there is currently no NIST-standardized CP-ABE equivalent to FIPS 203/204. The correct engineering recommendation is therefore: standardized PQC for key distribution/signatures now; crypto-agile interface for ABE; optional experimental lattice-based CP-ABE/KP-ABE behind a replaceable policy-crypto module.
## 8.4 Crypto-agility requirements
·        Store algorithm identifier, key version and policy version with each wrapped key/ciphertext.
·        Separate data cipher, KEM, signature and ABE algorithms in configuration.
·        Support dual/hybrid migration without re-encrypting bulk database payloads when only key wrapping changes.
·        Inventory RSA/ECC dependencies in drivers, KMS/HSM, backup/replication and attribute-authority services; measure migration time, rotation failures and old/new decryptability.
# 9. Methodology and Experimental Tracks
Sinh viên không cần triển khai tất cả các kiến trúc. Một đề tài tốt cần có một cấu hình nền (baseline) và ít nhất ba hướng bảo vệ/truy vấn có logic khác nhau, sau đó sử dụng cùng một workload và threat model để so sánh một cách nhất quán.

|**Experiment**|**Required setup**|**Evidence to collect**|
|---|---|---|
|E1 - Baseline at-rest|Plain DB vs volume/TDE encrypted DB|QPS, p95/p99, backup/restore, stolen-snapshot threat coverage|
|E2 - Field/client encryption|AEAD + KMS envelope encryption for selected fields|Encrypt/decrypt cycles, KMS latency, storage overhead, DB/admin plaintext exposure|
|E3 - ABAC enforcement|PDP/PEP + row/column/field policies|Permit/deny correctness, direct-query bypass tests, policy latency|
|E4 - CP-ABE DEK wrapping|Small CP-ABE prototype or library; policy over attributes|Enc/dec time, ciphertext/key size, collusion test, revocation/epoch cost|
|E5 - Secure query|MongoDB QE or SSE prototype for equality/range/text|Query latency, index size, leakage traces, inference test|
|E6 - Confidential query|Always Encrypted secure enclave / TEE query service|Attestation cold/warm, query latency, TCB/trust comparison|
|E7 - HE/FHE optional|SEAL BFV/BGV/CKKS on 1-2 aggregates|Compute expansion, ciphertext size, numerical error if approximate|
|E8 - PQC key path|ML-KEM key encapsulation + AEAD field encryption; ML-DSA signed policy/audit|Cycles/op, sizes, end-to-end latency, migration compatibility|
|E9 - Rotation/revocation|Rotate KMS/DEK/attribute epoch and re-test|Downtime, rows touched, stale-key failures, residual decryptability|
## 9.1 Mandatory security tests
·        Attempt direct DB query using a credential that bypasses the normal application path; verify whether policy remains enforced.
·        Restore/copy an encrypted snapshot without KMS permissions; verify data remains unavailable.
·        Move a valid ciphertext to a different tenant/field/version; AEAD AAD validation must reject it.
·        Replay or use stale wrapped keys after rotation/revocation.
·        Test ABAC with wrong tenant, wrong role, wrong purpose, out-of-window time and emergency/break-glass context.
·        For CP-ABE, combine attributes from multiple unauthorized users to test collusion resistance of the selected implementation.
·        For searchable encryption, repeat predictable queries and quantify observable equality/search/access patterns.
·        For PQC track, test old/new algorithm identifiers and downgrade/misconfiguration behavior.
# 10. Dataset and Workload Design
Use synthetic or public non-sensitive data. The dataset must be intentionally structured so that different protection layers can be measured. Recommended domains: healthcare records, multi-tenant HR/finance, or e-commerce/customer records.

|**Field**|**Example classification**|**Query need**|**Candidate protection**|
|---|---|---|---|
|tenant_id|Internal identifier|Equality/filter|Clear/AAD/tokenized depending threat model|
|user_id / patient_id|Sensitive linkable ID|Equality/join|Queryable encryption / deterministic token with leakage analysis|
|name/email|PII|Equality or prefix search|Client-side randomized + QE/SSE if search required|
|salary/amount|Confidential numeric|Range/aggregate|TEE / range QE / HE experiment|
|diagnosis/note|Highly sensitive text|Text search|Randomized encryption; SSE/QE for approved search|
|document/blob|High sensitivity|No DB query|AEAD field/object encryption|
|policy attributes|role/dept/clearance/purpose|Authorization|ABAC metadata; optionally CP-ABE policy|
|DEK metadata|Crypto control|Key lookup|Wrapped key + key_id/version/algorithm|
## 10.1 Workload suite
·        W1 point lookup; W2 equality filter; W3 range query; W4 join; W5 text search; W6 aggregate; W7 insert/update; W8 bulk export; W9 backup/restore; W10 key rotation.
·        Run every supported query on plaintext baseline and protected architecture with identical result semantics where possible.
·        Report unsupported queries explicitly rather than silently decrypting everything in the application.
# 11. Evaluation Metrics and Decision Framework

|**Dimension**|**Metrics**|
|---|---|
|Security coverage|Threats blocked; plaintext exposure components; key-access surface; direct-query bypass outcome|
|Leakage|Equality, frequency, order, search, access, volume, timing, update pattern|
|Authorization correctness|False permit / false deny; tenant isolation; row/column/field policy coverage|
|Cryptographic cost|CPU hardware cycles/op, enc/dec/encap/decap/sign/verify time, KMS/HSM latency|
|DB/query performance|p50/p95/p99, QPS/TPS, query planning behavior, index/write amplification|
|Storage/network|Ciphertext/index/key-metadata expansion; backup size; replication bandwidth|
|Operations|Key rotation/revocation time; availability impact; recovery from stale key/policy|
|PQC readiness|RSA/ECC dependencies remaining; dual-version compatibility; crypto-agility score|

**_Architecture score must not collapse security into a single latency number_**

The final recommendation should be workload-specific. For example, TDE may be sufficient for public catalog data; client-side AEAD + ABAC may be appropriate for PII; MongoDB QE/SSE may be justified for a small number of searchable fields; a secure enclave may be better for rich SQL; CP-ABE may be justified for durable cross-organization sharing policies; HE/FHE should be confined to operations where its cost is defensible.
# 12. Scope by Academic Level

|**Bachelor**|**Master**|
|---|---|
|System/threat analysis + protection hierarchy; implement baseline/TDE and field-level envelope encryption; ABAC row/field policy; one secure-query mechanism; basic PQC key-wrapping benchmark; final leakage table.|All Bachelor requirements plus rigorous leakage/inference analysis; CP-ABE KEM/DEM prototype with revocation strategy; comparison SQL vs NoSQL; TEE or HE/FHE advanced query; lattice-based PQ-ABE survey/prototype or crypto-agile PQ migration; statistical performance analysis.|
|Minimum 3 protected architectures / experiments beyond plaintext baseline.|Minimum 5 experiments including one advanced cryptographic access/query track and one PQC/crypto-agility track.|
# 13. Suggested 12-Week Plan

| **Week** | **Main work**                                                                                                   |
| -------- | --------------------------------------------------------------------------------------------------------------- |
| 1-2      | System analysis, data classification, threat model, SQL/NoSQL choice, query workload and security requirements. |
| 3        | Plaintext baseline + volume/TDE baseline; measurement harness.                                                  |
| 4-5      | Field/client-side AEAD + KMS envelope encryption; key hierarchy and rotation.                                   |
| 6        | ABAC/NGAC row/column/field policy and bypass tests.                                                             |
| 7-8      | Secure-query track: MongoDB QE/SSE or Always Encrypted/TEE.                                                     |
| 9        | CP-ABE DEK-wrapping research prototype or advanced policy encryption.                                           |
| 10       | PQC key/signature track using ML-KEM/ML-DSA; crypto-agility tests.                                              |
| 11       | Leakage analysis, performance experiments, rotation/revocation and mitigation re-test.                          |
| 12       | Final comparison, deployment recommendation, report, repository and demo.                                       |
# 14. Deliverables
1.  System architecture package: assets, actors, trust boundaries, F0-F9 data/query flows and threat model.
2.  Protection-layer matrix mapping each sensitive field/query to encryption, access-control and key-management mechanisms.
3.  Reproducible prototypes for the selected architectures with Docker/Compose/Kubernetes scripts.
4.  Policy artifacts: ABAC/NGAC rules and, if selected, CP-ABE access structures / attribute-key plan.
5.  Benchmark and leakage datasets (CSV/JSON) with scripts/notebooks for analysis.
6.  PQC readiness report: ML-KEM/ML-DSA integration point, remaining classical dependencies and crypto-agility plan.
7.  Final technical report and demo showing at least one unauthorized-access denial, one secure query and one key/policy rotation event.
# 15. Suggested Repository Structure

```bash
project-root/  
  infra/                  # DB, KMS, PDP/PEP, optional enclave  
  sql/                    # PostgreSQL/SQL Server schemas, RLS/NGAC policies  
  nosql/                  # MongoDB schemas / Queryable Encryption configs  
  client-sdk/             # AEAD field encryption + envelope key logic  
  access-control/         # ABAC/NGAC policies and test cases  
  abe/                    # CP-ABE / lattice-ABE research prototype (optional)  
  secure-query/           # SSE/QE / enclave / HE-FHE track  
  pqc/                    # ML-KEM / ML-DSA key-policy experiments  
  benchmarks/             # workloads, raw CSV/JSON, plots  
  attacks/                # leakage/inference + bypass tests, lab only  
  docs/                   # architecture, threat model, report, runbook  
```
# 16. Safety, Ethics and Limitations
·        Use only synthetic, anonymized or explicitly permitted datasets. Do not test leakage inference against real personal data without authorization.
·        Do not expose production database keys, cloud credentials or real attribute-authority master secrets in repositories or benchmark artifacts.
·        ABE, searchable encryption and FHE have strong model assumptions; the report must document the exact scheme/version and leakage/security model instead of using labels such as "encrypted query" generically.
·        Simulation must be labeled as simulation. TEE security claims require actual attestation/hardware evidence if presented as hardware-backed.
·        PQC ABE is research-stage; do not claim NIST compliance for a lattice-based ABE prototype.
# 17. Updated References and Technical Sources
[1] NIST SP 800-162, Guide to Attribute Based Access Control (ABAC) Definition and Considerations, final update 2019.
[2] NIST IR 8450, Overview and Considerations of Access Control Based on Attribute Encryption, updated final, Dec. 2023.
[3] NIST IR 8504, Access Control on NoSQL Databases, May 2024.
[4] NIST IR 8611, m-NGAC: Transcending Traditional Database Security Models, Aug. 2026.
[5] NIST SP 800-210, General Access Control Guidance for Cloud Systems, 2020.
[6] NIST SP 800-38D, Recommendation for GCM and GMAC (revision work announced by NIST).
[7] NIST FIPS 203, Module-Lattice-Based Key-Encapsulation Mechanism Standard (ML-KEM), Aug. 2024.
[8] NIST FIPS 204, Module-Lattice-Based Digital Signature Standard (ML-DSA), Aug. 2024; current NIST errata notes should be checked.
[9] NIST FIPS 205, Stateless Hash-Based Digital Signature Standard (SLH-DSA), Aug. 2024.
[10] NIST SP 800-227, Recommendations for Key-Encapsulation Mechanisms, Sept. 2025.
[11] NIST CSWP 39upd1, Considerations for Achieving Crypto Agility: Strategies and Practices, final update 2026.
[12] MongoDB Documentation, Queryable Encryption: client-side randomized encrypted fields with production equality/range query support; current text-query status must be checked against the deployed version.
[13] Microsoft Learn, Always Encrypted with Secure Enclaves for SQL Server / Azure SQL Database, current documentation 2026.
[14] R. A. Popa et al., CryptDB: Protecting Confidentiality with Encrypted Query Processing, SOSP 2011.
[15] R. Curtmola et al., Searchable Symmetric Encryption: Improved Definitions and Efficient Constructions, CCS 2006.
[16] D. Cash et al., Highly-Scalable Searchable Symmetric Encryption with Support for Boolean Queries, CRYPTO 2013.
[17] J. Bethencourt, A. Sahai, B. Waters, Ciphertext-Policy Attribute-Based Encryption, IEEE S&P 2007.
[18] B. Waters, Ciphertext-Policy Attribute-Based Encryption: An Expressive, Efficient, and Provably Secure Realization, PKC 2011.
[19] A General Framework for Lattice-Based ABE, IACR ePrint 2024/821.
[20] Attribute Based Encryption for Turing Machines from Lattices, IACR ePrint 2025/001.
[21] NIST, HQC announced as a Fourth-Round PQC selection for standardization, Mar. 2025. HQC is not yet a final FIPS standard.
[22] Microsoft SEAL documentation and source code for BFV/BGV/CKKS homomorphic encryption experiments.
# 18. Final Checklist
☐ System assets, actors and trust boundaries are explicit.
☐ Every sensitive field is classified and mapped to a protection layer.
☐ Volume/TDE protection is not presented as protection from authorized DB queries or DBA plaintext access.
☐ AES/AEAD confidentiality is clearly separated from authorization/access control.
☐ ABAC/NGAC policy includes subject, object, action and environment attributes where relevant.
☐ If CP-ABE is used, it wraps a DEK/key capsule and its revocation/collusion model is documented.
☐ SQL and/or NoSQL query requirements are listed before choosing encryption/query mechanisms.
☐ Queryable encryption leakage (equality/order/search/access/size/timing) is explicitly measured or catalogued.
☐ Key hierarchy, KMS/HSM boundary, key versioning, rotation and backup/restore are tested.
☐ Direct-DB / bypass scenarios are tested, not only the normal application path.
☐ PQC layer uses final standards correctly: ML-KEM for KEM, ML-DSA/SLH-DSA for signatures as appropriate.
☐ Lattice-based PQ ABE is clearly labeled research-stage, not NIST-standardized.
☐ Performance reports include p50/p95/p99 and, where relevant, CPU hardware cycles/op and storage/index overhead.
☐ Bachelor/Master scope is identified and feasible within the selected 12-week plan.
☐ All experiments use permissioned lab data and contain no production secrets.

| **FINAL PROJECT LOGIC**                                                                                                                                                                                                                                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| System Analysis -> Data Classification -> Threat Model -> Security Requirements -> Protection Layer -> Access Policy -> Cryptographic Mechanisms -> Secure Query -> Implementation -> Security/Leakage Tests -> Performance Evidence -> PQC/Crypto-Agility Recommendation |
