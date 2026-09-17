# Phân tích tài liệu nguồn và căn cứ thiết kế

Ngày lập: 10/09/2026. Phạm vi: đọc toàn bộ hai tài liệu hiện có trong thư mục dự án, không phải audit một hệ thống đã triển khai.

## 1. Kiểm kê và độ tin cậy của đầu vào

| Mã | File nguồn | Kích thước | Nội dung đã đọc |
|---|---|---:|---|
| G | [Course guideline](course-guideline.md) | 32.987 byte | 316 dòng, từ Core project philosophy đến Final principle |
| T | [Topic 18](topic-18.md) | 39.350 byte | 344 dòng, toàn bộ 18 mục và Final project logic |

SHA-256 của G: `749487E95FF70D91289FD31BF1C3F43A689E3E849BF5845734D34FF11EE9E0D6`.

SHA-256 của T: `057CA6227FECCD370BB1F8DA02863EC6988689859DCF0D41B6C7899FCB597CF4`.

Không có source code, schema, dependency manifest, cấu hình hạ tầng, dữ liệu benchmark hoặc bài kiểm thử ứng dụng tại thời điểm khảo sát. Vì vậy mọi cấu trúc triển khai trong bộ tài liệu mới là **thiết kế đề xuất**, không phải mô tả tính năng đã tồn tại. Giữ nguyên hai file nguồn.

## 2. Đọc guideline thành các nghĩa vụ cụ thể

| Phần nguồn | Ý nghĩa đối với đồ án | Quyết định trong đề xuất |
|---|---|---|
| G dòng 5–26 | Bắt đầu từ hệ thống; cấm nhảy trực tiếp Threat → Algorithm | Đặt bài toán hồ sơ y tế đa tenant trước lựa chọn primitive; tách SR và CR |
| G Phase 1 | Ranh giới hệ thống và tin cậy phải rõ | Phân biệt miền tổ chức tin cậy, cloud DB không tin cậy về bí mật, endpoint người nhận và miền kiểm toán |
| G Phase 2 | Khóa và protocol state là tài sản | Inventory cả DEK, KEK, AA master secret, trust anchor, phiên bản chống rollback, nonce state |
| G Phase 3 | Nêu năng lực/tri thức kẻ tấn công | Tách snapshot thief, direct-query user, DBA, active storage attacker, revoked user, future quantum attacker |
| G Phase 4 | SR đánh số và kiểm thử được | Mỗi SR có điều kiện, phạm vi và tiêu chí đạt; không chỉ ghi CIA |
| G Phase 5 | Đặt control trước lựa chọn primitive | PEP tại gateway và broker, PDP độc lập, khóa ngoài DB, registry phiên bản ngoài quyền DBA |
| G Phase 6 | CR là thuộc tính, không phải danh sách thuật toán | AEAD confidentiality/integrity, context binding, authenticity, freshness state, key separation, bounded leakage |
| G Phase 7 | So sánh phương án và composition | Phân biệt TDE/field/ABAC/ABE/search/HE/PQC; không ghép tất cả trên mọi đường đọc |
| G Phase 8 | API, nonce, lỗi, lifecycle quyết định an toàn | Chốt contracts trước implementation; fail closed; kiểm soát log, serialization, dependency |
| G Phase 9 | Happy path không chứng minh bảo mật | Test giả mạo, tráo ciphertext, bypass, revoked key, downgrade và inference |
| G Phase 10 | Kết luận theo evidence và giả định | Trạng thái NOT_RUN/PASS/FAIL/PARTIAL; kết luận theo từng SR và từng cấu hình |
| G mục 4–5 | Traceability và A1–A10 bắt buộc | Ma trận truy vết riêng, đầu ra từng sprint gắn A1–A10 |
| G mục 7 | Master cần phân tích mạnh hơn | Alternative threat models, giới hạn chứng minh, compromise graph và thống kê đa lần chạy |
| G mục 8 | Rubric có thể được giảng viên điều chỉnh | Dùng đúng trọng số gợi ý, không diễn giải thành bảo đảm điểm |
| G dòng 314–316 | Không tối đa hóa số thuật toán | Mỗi nhánh nâng cao phải trả lời một câu hỏi nghiên cứu, dùng tập dữ liệu nhỏ phù hợp |

## 3. Đọc Topic 18 theo từng nhóm nội dung

| Phần T | Phát hiện | Hệ quả triển khai |
|---|---|---|
| Mục 1–2 | Data protection ≠ access control ≠ secure query | Ba hợp đồng riêng: mã hóa byte; quyết định cấp quyền; chức năng/rò rỉ truy vấn |
| Mục 3 | F0–F9 là các luồng cần phân tích | Đưa cả provisioning, backup/CDC, rotation và audit vào DFD, không chỉ read/write |
| Mục 4 | L0–L9 là phân cấp phạm vi bảo vệ, không phải checklist lắp mọi công nghệ | Chọn volume baseline, field/core, ABAC, ABE, equality search, HE, PQC; TEE chỉ đối chiếu |
| Mục 5 | ABAC động và CP-ABE bền vững có ngữ nghĩa khác nhau | ABAC xử lý purpose/time/emergency; ABE chỉ tenant/department/role/epoch ổn định |
| Mục 6 | Có nhiều mẫu SQL/NoSQL | Dùng PostgreSQL và MongoDB với cùng envelope và token index để hạn chế yếu tố gây nhiễu |
| Mục 7 | Query phải đi cùng leakage catalogue | Đo equality/frequency/search/access/volume/timing/update; range/text unsupported trong profile chính |
| Mục 8 | PQC ưu tiên key/signature path; ABE cổ điển vẫn yếu trước lượng tử | E8 riêng, inventory mọi đường giải mã, không tuyên bố end-to-end PQ-safe |
| Mục 9 | Baseline và ít nhất ba hướng bảo vệ khác logic | Cấu hình B0, B1, P1, P2, P3, P4; 8 thí nghiệm E1/E2/E3/E4/E5/E7/E8/E9 |
| Mục 9.1 | Bypass/snapshot/AAD/revocation/context/collusion/leakage/downgrade là mandatory tests | Mỗi nhóm có TC cụ thể và đầu ra dự kiến |
| Mục 10 | W1–W10, cùng semantics khi so sánh | Lập support matrix; không âm thầm tải mọi dữ liệu về rồi gọi là truy vấn mã hóa |
| Mục 11 | Không gộp bảo mật thành một latency score | Báo cáo coverage, leakage, correctness, overhead và vận hành riêng |
| Mục 12 | Master: all Bachelor + các yêu cầu bổ sung | Giữ cả SQL/NoSQL, ABE revocation, HE, PQ migration và thống kê; không chỉ đạt đủ 5 experiment |
| Mục 13 | 12 tuần là lịch gợi ý | Dồn dependency spike vào tuần 1–2, HE không để sát ngày nộp |
| Mục 14–15 | Artifact và tính tái lập quan trọng | Source/config/tests/raw data/report/demo là các deliverable khác nhau |
| Mục 16 | Không dùng PII/secret thật; mô phỏng phải ghi rõ | Lab synthetic; volume thật nếu claim at-rest; không claim TEE nếu không có phần cứng/attestation |
| Mục 17–18 | Cần kiểm tra phiên bản nguồn và checklist | Giữ primary references, đánh dấu nội dung chưa kiểm chứng runtime |

### 3.1 Những chỗ cần diễn giải thận trọng

1. T mục 9 ghi E7 HE/FHE “optional” trong danh mục chung, nhưng T mục 12 yêu cầu Master có **TEE hoặc HE/FHE advanced query**. Đề xuất chọn BFV exact SUM; chỉ bỏ TEE, không bỏ cả hai.
2. “Ít nhất 5 experiments” không thay thế các yêu cầu định tính Master. Đủ số lượng vẫn chưa đủ nếu thiếu SQL/NoSQL hay leakage inference.
3. CP-ABE được ghi optional ở một số phần dùng chung; với scope Master của mục 12, đề xuất giữ prototype KEM/DEM và revocation.
4. “Rewrap without bulk re-encryption” chỉ đúng khi DEK và data AAD không thay đổi. Đổi DEK hoặc trường AAD bắt buộc tạo ciphertext mới; thu hồi người đã biết DEK không giải quyết bằng rewrap đơn thuần.
5. AAD ngăn tráo ngữ cảnh nếu expected context đến từ nguồn tin cậy. Nếu nhận cả ciphertext và toàn bộ AAD do DB đưa mà không kiểm chứng, attacker có thể tráo nguyên cặp.
6. AEAD/signature không tự phát hiện replay nguyên bản hợp lệ. Cần trạng thái phiên bản mới nhất ngoài miền bị rollback.
7. “Immediate revoke” chỉ nói về yêu cầu online chưa được cấp tiếp. Không có cơ chế thu hồi một bản plaintext hoặc DEK đã bị người nhận giữ lại.
8. Nhiều lớp wrap cùng DEK theo kiểu OR làm độ bí mật dài hạn phụ thuộc đường yếu nhất. CP-ABE và PQC được đánh giá trên artifact tách biệt, không lấy lớp PQ phủ nhận đường ABE cổ điển.
9. RLS PostgreSQL không chống được superuser/BYPASSRLS; một session variable tự set không là bằng chứng tenant đáng tin.
10. Chính sách đúng purpose không thể chỉ dựa vào chuỗi “treatment” do người gọi tự gửi. Cần nguồn workflow được xác thực; không chứng minh động cơ thực tế của con người.

## 4. Phủ yêu cầu Master và rubric

| Nghĩa vụ | Phạm vi chốt | Artifact/bằng chứng khi thực hiện |
|---|---|---|
| Baseline plaintext và at-rest | B0/B1, encrypted lab volume, DB thật | E1, TC-08, đo QPS/latency/backup |
| Field envelope + KMS + ABAC | P1 trên SQL/NoSQL | E2/E3, TC-01–10, TC-27 |
| Secure query | Equality-only blind index, mô hình SSE giới hạn | E5, leakage traces/inference, unsupported matrix |
| CP-ABE + revocation | P2 export/share capsule độc lập | E4/E9, TC-11–14 |
| SQL vs NoSQL | Cùng logical schema/workload/core controls | So sánh B0/P1 trên cả hai DB |
| TEE hoặc HE/FHE | P3: SEAL BFV, exact SUM/count | E7, TC-18–19, TC-30; không claim full FHE OLTP |
| PQC/crypto-agile migration | P4: ML-KEM, ML-DSA, migration state | E8/E9, TC-20–23 |
| Rigor Master | Leakage + statistical CI + alternative assumptions | E5, mục thống kê và residual risks |

| Rubric G mục 8 | Trọng số gợi ý | Tài liệu/công việc ưu tiên |
|---|---:|---|
| System/assets/threat model | 15% | Phân tích miền tin cậy, asset dependency và T-01–T-18 |
| Requirements/architecture | 15% | SR-01–SR-18, DFD F0–F9, placement PEP/broker |
| Crypto requirements/design | 20% | CR-01–CR-12, mechanism rationale, parameters và composition |
| Secure implementation | 20% | API contracts, nonce, lifecycle, review code và build tái lập |
| Security tests | 15% | TC-01–TC-30, adversarial evidence, không chỉ round-trip |
| Evaluation/evidence | 10% | Traceability, CI, residual risk, scoped claim |
| Report/demo | 5% | Demo 12 phút, script tái lập, source/log/chart liên kết |

**Không có bảo đảm điểm số.** Đây là cách phân bổ công sức theo rubric gợi ý; kết quả phụ thuộc implementation và evidence thực tế.

## 5. Nguồn ngoài đã đối chiếu và giới hạn xác minh

Đối chiếu trực tuyến ngày 10/09/2026; đây là xác minh xuất xứ/tình trạng tài liệu, không phải chứng nhận một thư viện.

| Nguồn chính | Thông tin được đối chiếu | Cách dùng |
|---|---|---|
| [NIST IR 8611](https://csrc.nist.gov/pubs/ir/8611/final) | Có bản final về m-NGAC; danh mục NIST ghi 27/08/2026 | Related work; không giả định PostgreSQL mặc định có m-NGAC |
| [SP 800-227](https://csrc.nist.gov/pubs/sp/800/227/final) | Final 18/09/2025; khuyến nghị dùng KEM | Cơ sở key encapsulation, khác bulk encryption |
| [CSWP 39upd1](https://csrc.nist.gov/pubs/cswp/39/upd1/considerations-for-achieving-crypto-agility/final) | Final update 29/06/2026 | Inventory và migration |
| [FIPS 203](https://csrc.nist.gov/pubs/fips/203/final) | ML-KEM-512/768/1024 | Chọn ML-KEM-768 trong E8 |
| [FIPS 204](https://csrc.nist.gov/pubs/fips/204/final) | Nguồn chuẩn ML-DSA | Kiểm tra errata khi khóa dependency; chưa xác minh bản binary |
| [MongoDB QE](https://www.mongodb.com/docs/manual/core/queryable-encryption/) | Equality/range production; text preview ở 8.2 trong manual được tìm thấy | Chỉ làm alternative; không gắn tên MongoDB QE cho HMAC blind index |
| [MongoDB limitations](https://www.mongodb.com/docs/manual/core/queryable-encryption/reference/limitations/) | Giới hạn phụ thuộc phiên bản | Nếu mở rộng QE phải khóa server/driver/config cụ thể |
| [Charm documentation](https://jhuisi.github.io/charm/) | Có CPabe_BSW07 và ví dụ pairing | Candidate research library; ví dụ SS512 không chứng minh mức 128-bit |
| [IACR 2024/821](https://eprint.iacr.org/2024/821) | Framework lattice ABE, tiêu đề đầy đủ có “Using Evasive…” | Đọc đầy đủ giả định, không gộp mọi lattice ABE thành standard-LWE |
| [IACR 2025/001](https://eprint.iacr.org/2025/001) | ABE cho Turing machines từ lattices | Survey ngắn; không cam kết implement nghiên cứu này |
| [Microsoft SEAL](https://github.com/microsoft/SEAL) | Kho nguồn tham chiếu trong T | Candidate BFV; pin release, build và xác nhận parameter API trong spike |
| [NIST SP 800-162](https://csrc.nist.gov/pubs/sp/800/162/upd2/final) | Nguồn ABAC trong T | Subject/object/action/environment model |
| [NIST IR 8450](https://csrc.nist.gov/pubs/ir/8450/final) | Nguồn attribute-encryption access control trong T | Phân biệt authorization và possession of key |
| [NIST IR 8504](https://csrc.nist.gov/pubs/ir/8504/final) | Nguồn NoSQL access control trong T | SQL/NoSQL discussion |

Các nguồn kế thừa trong T không có snapshot toàn văn trong bộ tài liệu này. Trước khi nộp báo cáo cuối: tải bản công khai, ghi ngày truy cập và revision, đối chiếu đúng trang/định lý được trích, kiểm tra errata FIPS; không dẫn kết quả tìm kiếm thay cho đọc bài.

## 6. Evidence → Finding → Path của lần phân tích này

| Evidence | Finding | Path/quyết định |
|---|---|---|
| G dòng 7, 26, 316 | Giảng viên ưu tiên chuỗi lập luận có kiểm chứng | Hai file chính theo đủ 10 phase; ma trận không bỏ tầng CR |
| T mục 12, dòng 257–258 | Scope Master rộng hơn một PoC AES + ABAC | 8 thí nghiệm có HE, ABE, PQC; SQL/NoSQL chung core |
| T mục 5.2–5.3, 8 | Thu hồi và quantum claims có giới hạn cấu trúc | Tách online/offline, tách P2 khỏi P4, ghi residual decryptability |
| T mục 9.1, 10.1, 11 | Security/leakage/correctness là bắt buộc | Negative tests + supported-query matrix + raw evidence schema |
| Kiểm kê chỉ có G/T | Chưa có implementation/evidence | Tất cả kết quả test ban đầu là NOT_RUN; không điền số benchmark giả |

## 7. Hướng dẫn sử dụng bộ tài liệu

1. Nộp [project proposal](../proposal/project-proposal.md) để đăng ký; bổ sung thông tin hành chính theo mẫu của lớp.
2. Dùng [Detailed project implementation](../planning/implementation-plan.md) để triển khai và xây dựng các chương báo cáo.
3. Dùng [experiments and validation](../testing/experiments-and-validation.md) làm kế hoạch test/benchmark.
4. Cập nhật [traceability matrix](../testing/traceability-matrix.md) sau mỗi test, không chỉ lúc gần nộp.
5. Sửa sơ đồ nguồn trong thư mục diagrams khi trust boundary hoặc luồng thay đổi.

Trạng thái hoàn thành của **lần lập kế hoạch**: đã đọc G/T, lập bản phân tích, thiết kế và tiêu chí kiểm chứng. Trạng thái **đồ án**: chưa triển khai, chưa có bằng chứng bảo mật thực nghiệm.
