# SCRIPT THUYẾT TRÌNH
## Proposal – MedShare-Lab | Đề tài 18 – NT2205.11.CH

> **Thời gian đề xuất:** 20–25 phút | `[→ slide X]` = chuyển slide

---

## 💡 KHÁI NIỆM CẦN NẮM

| Thuật ngữ | Giải thích |
|---|---|
| **EHR** | Electronic Health Record – hồ sơ bệnh án điện tử |
| **Multi-tenant** | Nhiều tổ chức dùng chung một hệ thống/DB |
| **Plaintext / Bản rõ** | Dữ liệu gốc chưa mã hoá, đọc được trực tiếp |
| **Ciphertext** | Dữ liệu đã mã hoá, vô nghĩa nếu không có khoá |
| **DEK** | Data Encryption Key – khoá mã hoá dữ liệu (ngắn hạn, per-record) |
| **KEK** | Key Encryption Key – khoá bảo vệ DEK (dài hạn, trong Vault) |
| **KMS** | Key Management System – hệ thống quản lý khoá |
| **AES-256-GCM** | Thuật toán mã hoá đối xứng AEAD 256-bit – vừa mã hoá vừa xác thực toàn vẹn |
| **AAD** | Authenticated Additional Data – ngữ cảnh đính kèm vào mã hoá GCM |
| **ABAC** | Attribute-Based Access Control – kiểm soát truy cập theo thuộc tính |
| **PDP** | Policy Decision Point – nơi ra quyết định Allow/Deny trong ABAC |
| **RLS** | Row-Level Security – bảo mật cấp hàng trong PostgreSQL |
| **HKDF** | HMAC-based Key Derivation Function – hàm dẫn xuất khoá |
| **HMAC** | Hash-based Message Authentication Code – mã xác thực dựa trên hash |
| **Blind Index** | Index tìm kiếm từ hash của plaintext, không lộ bản rõ |
| **Vault Transit** | Tính năng mã hoá/giải mã như dịch vụ của HashiCorp Vault |
| **Trust Zone** | Vùng mạng phân tách theo mức độ tin cậy |
| **mTLS** | Mutual TLS – xác thực hai chiều bằng chứng chỉ |
| **Snapshot attack** | Tấn công bằng cách sao chép toàn bộ ổ đĩa vật lý |
| **Frequency inference** | Phân tích tần suất truy vấn để suy ra nội dung dữ liệu |
| **Defence-in-depth** | Chiến lược bảo mật nhiều lớp độc lập |
| **Deny-by-default** | Mặc định từ chối; chỉ cho phép khi thoả mãn đủ điều kiện |
| **HIPAA / GDPR** | Luật bảo vệ dữ liệu y tế (Mỹ / EU) |
| **CP-ABE** | Ciphertext-Policy ABE – mã hoá nhúng chính sách truy cập vào ciphertext |
| **HE / BFV** | Homomorphic Encryption – tính toán trực tiếp trên ciphertext không cần giải mã |
| **ML-KEM / ML-DSA** | Thuật toán kháng lượng tử: đóng gói khoá (FIPS 203) và chữ ký số (FIPS 204) |

---

## SLIDE 1 – Trang bìa
⏱ *~1 phút*

Kính chào thầy/cô và các bạn.

Nhóm chúng em xin trình bày **Proposal** cho đề tài số **18** của môn **NT2205.11.CH – Bảo mật Cơ sở Dữ liệu Nâng cao**.

Tên đề tài: **"MedShare-Lab"** – Hệ thống quản lý hồ sơ bệnh án điện tử **đa thuê bao** trên nền tảng Cloud DBMS, với trọng tâm là **bảo mật tầng trường dữ liệu**.

Bài trình bày gồm 4 nội dung chính: ngữ cảnh bài toán, các bên liên quan, vấn đề đặt ra, và giải pháp kèm hai sơ đồ kiến trúc trực quan.

`[→ slide 2]`

---

## SLIDE 2 – Nội dung trình bày
⏱ *~30 giây*

Bài trình bày gồm **6 phần**: ngữ cảnh bài toán → bên liên quan → vấn đề đặt ra → giải pháp đề xuất → sơ đồ hệ thống trước và sau khi bảo mật.

`[→ slide 3]`

---

## SLIDE 3 – Ngữ cảnh bài toán
⏱ *~2,5 phút*

**Vấn đề xuất phát từ xu hướng số hoá y tế.**

**EHR – Hồ sơ bệnh án điện tử** đang thay thế hồ sơ giấy. Mỗi bệnh nhân có các thông tin rất nhạy cảm: chẩn đoán bệnh, đơn thuốc, ghi chú lâm sàng của bác sĩ. Nếu bị lộ, có thể ảnh hưởng nghiêm trọng đến danh dự và quyền riêng tư của bệnh nhân.

**Multi-tenant Cloud DBMS:** Để tiết kiệm chi phí, nhiều bệnh viện dùng chung hạ tầng Cloud. Trong đề tài, chúng em mô phỏng hai bệnh viện – **Hospital A** (60%) và **Hospital B** (40%) – cùng chia sẻ một cụm PostgreSQL 16 và MongoDB 7.0 trên Cloud.

Vấn đề ngay lập tức xuất hiện: **DBA của nhà cung cấp Cloud** có quyền `SELECT *` trên toàn bộ database – tức là về mặt kỹ thuật, họ có thể đọc bản rõ mọi hồ sơ bệnh nhân của cả hai bệnh viện.

**Yêu cầu pháp lý:** Điều này vi phạm **HIPAA** *(Mỹ)* và **GDPR** *(EU)*. Cả hai yêu cầu nguyên tắc *"need-to-know"* – chỉ người có chức năng liên quan mới được xem dữ liệu – và mọi truy cập phải có audit log đầy đủ.

**Bài toán cốt lõi:** Làm sao bảo vệ dữ liệu bệnh nhân **ngay cả khi Cloud DBA hoặc Cloud provider có quyền vật lý vào máy chủ DB?** Câu trả lời: bảo mật phải **độc lập hoàn toàn với tầng DB**.

`[→ slide 4]`

---

## SLIDE 4 – Bên liên quan
⏱ *~2,5 phút*

Hệ thống có **7 nhóm bên liên quan** với mức tin cậy khác nhau – và việc xác định mức tin cậy này **quyết định toàn bộ thiết kế bảo mật**.

**Bác sĩ và Điều dưỡng** – người dùng chính. Được tin cậy có điều kiện: chỉ được xem đúng hồ sơ thuộc chuyên khoa và bệnh viện của mình.

**Bệnh viện / Tổ chức y tế** – Data Controller theo GDPR: chịu trách nhiệm pháp lý về toàn bộ chính sách truy cập.

Hai nhóm **bán tin cậy** – đây là trọng tâm thiết kế:

- **DBA của Cloud**: về mặt kỹ thuật có quyền vận hành DB, nhưng về mặt nghiệp vụ và pháp lý **không được phép** đọc nội dung hồ sơ bệnh nhân. Đây là mâu thuẫn giữa quyền kỹ thuật và quyền nghiệp vụ – hệ thống phải giải quyết bằng mã hoá, không thể chỉ dựa vào hợp đồng.

  > **Bán tin cậy** có nghĩa: tin họ không chủ động phá hoại, nhưng **không tin** họ không tò mò xem dữ liệu – hoặc bị bên thứ ba ép buộc tiết lộ.

- **Cloud DBMS Provider**: kiểm soát vật lý ổ đĩa. Có thể sao chép toàn bộ volume – đây là **snapshot attack** – mà không cần credential DB nào.

**Vault KMS** – nằm trong Zone Z1 do bệnh viện kiểm soát. Ranh giới Z1 ≠ Z2 là ranh giới bảo mật quan trọng nhất của toàn hệ thống.

**Kẻ tấn công** được định nghĩa theo 5 mô hình đối thủ:
- **M0** – kẻ ngoài mạng, không có credential
- **M1** – Cloud provider, có quyền đọc vật lý ổ đĩa
- **M2** – DBA nội bộ, có quyền `SELECT *`
- **M3** – Người dùng hợp lệ nhưng sai tenant hoặc sai khoa
- **M4** – Kẻ replay ciphertext cũ hoặc hoán đổi ciphertext giữa các bản ghi

`[→ slide 5]`

---

## SLIDE 5 – Vấn đề đặt ra
⏱ *~2,5 phút*

Hệ thống EHR cơ bản – không có bảo mật tầng trường – có **6 điểm yếu nghiêm trọng**:

**① DBA đọc bản rõ** *(đối thủ M2)*
Chỉ cần `SELECT * FROM patient_records`, DBA đọc được toàn bộ chẩn đoán, đơn thuốc, ghi chú lâm sàng của mọi bệnh nhân, mọi bệnh viện. Không cần tấn công phức tạp – quyền DB là đủ.

**② Snapshot ổ đĩa** *(đối thủ M1)*
Nếu không mã hoá tầng trường, một bản sao ổ đĩa vật lý là đủ để lộ 100% dữ liệu. Cloud provider không cần biết password DB – chỉ cần mount volume.

**③ Không phân tách Tenant** *(đối thủ M3)*
Không có cơ chế ngăn Hospital A truy vấn dữ liệu của Hospital B ở tầng ứng dụng. PostgreSQL RLS có nhưng không đủ nếu bị bypass ở application layer.

**④ Không kiểm soát Trường dữ liệu** *(đối thủ M3)*
Không có **ABAC** – mọi role đều đọc được mọi trường trong mọi hồ sơ, dù không có nhu cầu lâm sàng.

> **ABAC** – Attribute-Based Access Control: kiểm soát truy cập dựa trên tập hợp thuộc tính Role + Department + Tenant + TimeOfDay. Mạnh hơn RBAC vì kết hợp nhiều điều kiện đồng thời.

**⑤ Query lộ bản rõ** *(đối thủ M2)*
Index trực tiếp trên plaintext cho phép **frequency inference attack**: phân tích tần suất xuất hiện của các giá trị để suy ra nội dung bản rõ.

**⑥ Hoán đổi Ciphertext** *(đối thủ M4)*
Nếu có mã hoá nhưng không có **AAD binding** – ciphertext không được ràng buộc vào ngữ cảnh – kẻ tấn công có thể lấy ciphertext của bệnh nhân A gán cho bệnh nhân B mà hệ thống không phát hiện.

> **AAD** – Authenticated Additional Data: dữ liệu ngữ cảnh `tenant_id || record_id || field_name` đính kèm vào GCM. Nếu ciphertext bị di chuyển sang ngữ cảnh khác → GCM tag fail → giải mã bị từ chối.

**Kết luận:** Hệ thống EHR cơ bản không đủ bảo vệ khi Cloud provider là bán tin cậy. Bảo mật phải **độc lập với tầng DB** – không thể chỉ dựa vào quyền DB, firewall hay TLS.

`[→ slide 6]`

---

## SLIDE 6 – Giải pháp đề xuất
⏱ *~3 phút*

Để giải quyết từng vấn đề, chúng em đề xuất **6 kỹ thuật cốt lõi** ở Profile P1:

---

**① AES-256-GCM – Field Envelope Encryption** → giải quyết ① và ②

Thay vì mã hoá toàn bộ ổ đĩa, chúng em mã hoá **từng trường dữ liệu** riêng lẻ bằng một DEK 256-bit ngẫu nhiên.

> **AES-256-GCM** là thuật toán **AEAD** – Authenticated Encryption with Associated Data. Nó vừa mã hoá dữ liệu vừa xác thực tính toàn vẹn. Ai sửa ciphertext mà không có khoá sẽ bị phát hiện ngay.

Kết quả: DBA hay Cloud provider snapshot ổ đĩa chỉ thấy chuỗi hex vô nghĩa.

---

**② AAD Context Binding** → giải quyết ⑥

Mỗi lần mã hoá, đính kèm AAD = `tenant_id || record_id || field_name || schema_version` vào GCM tag. Nếu ciphertext bị cắt dán sang bản ghi khác → **GCM authentication tag fail** → hệ thống từ chối giải mã. Ciphertext swap hoàn toàn bị vô hiệu hoá.

---

**③ HashiCorp Vault Transit KMS** → giải quyết ① và ②

> **Envelope Encryption**: DEK *(ngắn hạn, per-record)* được Vault bọc bằng KEK *(dài hạn)*. DEK sau khi bọc thành **capsule** được lưu cùng bản ghi DB. Khi cần giải mã, ứng dụng gửi capsule lên Vault xin unwrap → nhận DEK → giải mã trường → xoá DEK khỏi bộ nhớ.

Điểm mấu chốt: DEK dạng rõ **không bao giờ lưu ra DB** và **không bao giờ rời khỏi Zone Z1**. DBA ở Zone Z2 chỉ thấy capsule đã mã hoá – vô dụng nếu không có quyền gọi Vault API.

---

**④ ABAC Policy Engine – Deny-by-default** → giải quyết ③ và ④

> **Deny-by-default**: mặc định mọi request đều bị từ chối. Chỉ khi thoả mãn **đồng thời tất cả** điều kiện trong policy mới được phép – ngược với allow-by-default thông thường.

Chính sách ABAC kiểm tra 4 thuộc tính đồng thời: **Role** (DOCTOR/NURSE) + **Department** (đúng khoa của hồ sơ) + **Tenant** (đúng bệnh viện) + **TimeOfDay** (trong giờ hành chính). Thiếu bất kỳ điều kiện → từ chối, ghi audit log ngay lập tức.

---

**⑤ Blind Index – HKDF + HMAC-SHA256** → giải quyết ⑤

> **Blind Index**: thay vì lưu plaintext để index, lưu `blind_token = HMAC(derived_key, plaintext)`. Khi query, ứng dụng tính token từ giá trị tìm kiếm và so sánh token – không bao giờ gửi plaintext vào DB.

Khoá HMAC được dẫn xuất bằng HKDF với **domain separation**: mỗi tenant và mỗi field có khoá riêng, ngăn kẻ tấn công so sánh token giữa các context khác nhau.

---

**⑥ Audit Log – Zone Z3 (Immutable)** → hỗ trợ toàn bộ

Mọi sự kiện – truy cập thành công, bị từ chối, break-glass – đều ghi vào **Audit Log bất biến** tại Zone Z3. Chỉ lưu metadata: `actor + action + resource_id + timestamp` – không lưu bản rõ, không lưu DEK.

`[→ slide 6b]`

---

## SLIDE 6b – Giải pháp đề xuất (tiếp) – Roadmap P2–P4
⏱ *~1,5 phút*

Ngoài 6 kỹ thuật cốt lõi ở Profile P1, đề tài có 3 giai đoạn mở rộng:

---

**P2 – CP-ABE: Chia sẻ dữ liệu liên tổ chức**

> **CP-ABE** – Ciphertext-Policy Attribute-Based Encryption: chính sách truy cập được **nhúng trực tiếp vào ciphertext**. Chỉ ai sở hữu đủ tập thuộc tính thoả mãn chính sách mới giải mã được – không cần server trung gian.

Ứng dụng: bệnh viện mã hoá hồ sơ với chính sách `(Role=RESEARCHER AND Approved=TRUE)`. Nghiên cứu viên đủ attribute thì tự giải mã – bệnh viện không cần cấp credential DB cho bên ngoài.

---

**P3 – Microsoft SEAL BFV: Tính toán trên dữ liệu mã hoá**

> **Homomorphic Encryption (HE)**: mã hoá đặc biệt cho phép **tính toán trực tiếp trên ciphertext** mà không cần giải mã. Kết quả tính toán, khi giải mã, cho ra đúng kết quả như tính trên plaintext.

Ứng dụng: nhóm nghiên cứu tính tổng số bệnh nhân mắc một bệnh mà không cần xem từng hồ sơ. Với schema **BFV**, họ tính `SUM` trực tiếp trên ciphertext – dữ liệu cá nhân không bao giờ bị lộ.

---

**P4 – ML-KEM-768 / ML-DSA-65: Bảo mật kháng lượng tử**

> **Post-Quantum Cryptography (PQC)**: thuật toán chịu được tấn công bởi máy tính lượng tử. Máy tính lượng tử có thể phá RSA và ECC trong thời gian đa thức. NIST đã chuẩn hoá **ML-KEM-768** (FIPS 203) cho key encapsulation và **ML-DSA-65** (FIPS 204) cho chữ ký số.

Ứng dụng: hồ sơ lưu trữ dài hạn 10–20 năm cần chống kịch bản *"Harvest now, decrypt later"* – thu thập ciphertext bây giờ, chờ máy tính lượng tử giải mã sau.

`[→ slide 7]`

---

## SLIDE 7 – Sơ đồ hệ thống TRƯỚC bảo mật
⏱ *~2,5 phút*

Đây là sơ đồ hệ thống **trước khi áp dụng bảo mật** – Baseline B0.

**Tầng Người dùng:** Bác sĩ và Điều dưỡng gửi request qua HTTP đến App Server. DBA và Kẻ tấn công cũng hiện diện ở tầng này với quyền truy cập không bị kiểm soát.

**Tầng Ứng dụng:** App Server không có ABAC, không có Tenant isolation, không có KMS, không có Blind Index. Không có bất kỳ cơ chế bảo vệ tầng trường nào.

**DBA truy cập trực tiếp DB:** DBA có đường truy cập trực tiếp vào PostgreSQL bằng `SELECT *` – không qua App Server, không qua xác thực nghiệp vụ. Kẻ tấn công dùng snapshot attack cũng có đường tương tự.

**Tầng Database:** Toàn bộ dữ liệu lưu bản rõ – `patient_id`, `diagnosis`, `medication`, `notes` – đọc được ngay không cần giải mã.

**5 điểm yếu** tóm tắt: DBA bản rõ · Snapshot 100% · Cross-tenant · Không Blind Index · Không AAD. Đây là trạng thái mà nhiều hệ thống EHR thực tế đang vận hành.

`[→ slide 8]`

---

## SLIDE 8 – Sơ đồ hệ thống SAU bảo mật
⏱ *~3,5 phút*

Đây là hệ thống **MedShare-Lab hoàn thiện** – Profile P1. Kiến trúc tổ chức theo **4 vùng tin cậy (Trust Zones)** – việc phân vùng này là cốt lõi của toàn bộ thiết kế.

---

**Zone Z0 – Internet / Client** *(màu xanh dương)*

Nơi người dùng – Bác sĩ, Điều dưỡng – gửi request. Mọi kết nối qua **HTTPS/mTLS** với JWT authentication. DBA xuất hiện ở đây nhưng bị từ chối – vì lý do sẽ thấy ở Zone Z1.

---

**Zone Z1 – Trusted Application Layer** *(màu xanh lá)*

Vùng **tin cậy cao nhất**, do bệnh viện kiểm soát hoàn toàn. Đây là **ranh giới bảo mật quan trọng nhất** – mọi DEK đều nằm ở đây và không bao giờ rời đi.

5 thành phần hoạt động phối hợp:
- **API Gateway**: xác thực JWT, từ chối request không hợp lệ trước mọi thứ
- **ABAC PDP**: kiểm tra chính sách deny-by-default theo Role + Dept + Tenant + TimeOfDay
- **Key Broker**: thực hiện mã hoá/giải mã AES-256-GCM cho từng trường
- **Vault KMS**: "két sắt" của hệ thống – DEK không bao giờ ra khỏi Z1
- **Blind Engine**: tính `blind_token = HMAC(key, plaintext)` cho request tìm kiếm

DBA cố truy cập bị API Gateway từ chối ngay tại Z1. Dù DBA có quyền SQL vào Z2, họ không có DEK – vì DEK nằm trong Vault, DBA không có quyền gọi Vault API.

---

**Zone Z2 – Cloud DBMS** *(màu vàng)*

Vùng **bán tin cậy**, do Cloud provider vận hành. Toàn bộ dữ liệu ở Z2 đã mã hoá:
- **PostgreSQL 16**: encrypted fields + RLS per tenant
- **Capsule Store**: wrapped DEK – không có khoá gốc
- **search_index**: blind_token HMAC – không suy ra được plaintext
- **MongoDB 7.0**: encrypted documents cho dữ liệu bán cấu trúc

Cloud provider snapshot cả Zone Z2 cũng vô nghĩa – vì DEK nằm ở Z1, không phải Z2.

---

**Zone Z3 – Audit Log** *(màu tím)*

Bất biến và tách biệt hoàn toàn – chỉ nhận sự kiện từ Z1. Chỉ lưu metadata, không bao giờ lưu bản rõ hay DEK.

---

**Tổng kết:** AES-GCM + Vault KMS + ABAC + Blind Index + AAD Binding + Audit Z3 hoạt động đồng thời như hệ thống **phòng thủ nhiều lớp** *(defence-in-depth)* – một lớp bị phá không có nghĩa toàn bộ hệ thống thất thủ.

`[→ slide 9]`

---

## SLIDE 9 – So sánh Trước & Sau
⏱ *~1,5 phút*

**Trước – Baseline B0:** Dữ liệu bản rõ. DBA một câu `SELECT *` là xong. Snapshot = mất 100%. Không phân tách tenant. Không ABAC. Không Blind Index. Không AAD.

**Sau – Profile P1:** DBA chỉ thấy chuỗi hex. DEK trong Vault Z1 – ngoài tầm Cloud provider. ABAC chặn sai tenant/khoa. Blind Index bảo vệ tìm kiếm. AAD ngăn ciphertext swap.

Đây không đơn thuần là thêm một tính năng – mà là **thay đổi toàn bộ mô hình tin cậy**: từ *"tin Cloud provider"* sang *"Cloud provider chỉ thấy ciphertext vô nghĩa"*.

`[→ slide 10]`

---

## SLIDE 10 – Cảm ơn & Q&A
⏱ *~30 giây + Q&A*

Trên đây là toàn bộ Proposal cho đề tài MedShare-Lab. Tóm lại, hệ thống bảo mật EHR đa lớp với 4 điểm mạnh cốt lõi:

- **AES-256-GCM + Vault KMS** – DBA không thể đọc bản rõ dù có toàn quyền DB
- **ABAC deny-by-default** – kiểm soát truy cập chính xác đến từng trường
- **Blind Index HMAC** – tìm kiếm an toàn không lộ plaintext ra DB
- **Audit Log bất biến Z3** – mọi truy cập đều có thể truy vết

**Xin chân thành cảm ơn thầy/cô và các bạn!**

---

## 📝 Q&A – Câu hỏi thường gặp

### ❓ Vault (KMS) bị tấn công thì sao?

Vault nằm trong Zone Z1 do bệnh viện kiểm soát – không phải Cloud provider – và không được expose ra internet. Nếu Vault bị compromise thì đó là vấn đề ở tầng infrastructure, nằm ngoài threat model M0–M4 của đề tài. Ở production, Vault hỗ trợ tích hợp **HSM** *(Hardware Security Module)* để bảo vệ KEK ở tầng phần cứng, và chạy **HA cluster** để tránh single point of failure.

### ❓ Hiệu năng có bị ảnh hưởng không?

Có ảnh hưởng nhỏ: mỗi write thêm 1 lần wrap DEK (~1–3ms), mỗi read thêm 1 lần unwrap (~1–3ms) – tổng thêm khoảng **2–6ms** per request. Giảm thiểu bằng **DEK caching** trong bộ nhớ ứng dụng (TTL ngắn) và Vault connection pooling. Trade-off hoàn toàn chấp nhận được trong context y tế – bác sĩ chờ thêm 5ms còn hơn lộ dữ liệu 10,000 bệnh nhân.

### ❓ Tại sao không dùng mã hoá toàn bộ DB (TDE) thay vì từng trường?

**TDE** *(Transparent Data Encryption)* và LUKS chỉ bảo vệ khi ổ đĩa **offline**. Khi DB đang chạy, dữ liệu được giải mã tự động cho tất cả người có quyền DB – bao gồm DBA. Field-level encryption giải quyết điều này vì **DEK nằm trong Vault Z1, không phải trong DB**. DBA có toàn quyền DB vẫn không lấy được DEK.

### ❓ ABAC và PostgreSQL RLS có trùng lặp không?

Không trùng lặp – chúng bổ sung theo **defence-in-depth**:
- **ABAC** (Zone Z1): kiểm tra Role + Dept + Tenant + Time *trước khi* truy cập DB
- **RLS** (Zone Z2): lọc hàng theo `tenant_id` tại tầng DB – lớp phòng thủ cuối cùng

Nếu có lỗ hổng SQL injection vượt qua ABAC, RLS vẫn ngăn data của tenant khác bị lộ.

### ❓ Blind Index có thể bị crack không?

HMAC-SHA256 là one-way – không thể reverse toán học. Tuy nhiên kẻ tấn công có thể thực hiện **offline dictionary attack**: tính HMAC của toàn bộ mã ICD-10 (~70,000 mã) và so sánh với token. Giảm thiểu bằng **HKDF domain separation** (mỗi tenant + field có khoá riêng → dictionary của tenant A không dùng được cho tenant B) và **định kỳ xoay vòng domain key**.

### ❓ Break-Glass là gì? Có phải lỗ hổng bảo mật không?

Break-Glass là cơ chế truy cập khẩn cấp – ví dụ bác sĩ trực cấp cứu cần xem hồ sơ nhưng bác sĩ phụ trách không có mặt. Không phải lỗ hổng – vì yêu cầu: (1) tạo **ticket** với lý do cụ thể, (2) có **thời hạn hết hạn** (thường 4 giờ), (3) ghi **audit log ngay lập tức** và gửi notification đến quản lý. Sau khi hết hạn, quyền truy cập tự động thu hồi. Đây là cân bằng giữa **bảo mật và tính khả dụng** trong y tế.

### ❓ Tại sao dùng cả PostgreSQL lẫn MongoDB?

PostgreSQL 16 cho dữ liệu **có cấu trúc cố định** (demographics, diagnoses, medications) – tận dụng ACID, RLS, B-tree indexing. MongoDB 7.0 cho dữ liệu **bán cấu trúc linh hoạt** (clinical notes, imaging metadata, custom fields theo từng khoa) – schema không cố định, dễ mở rộng. Cả hai đều ở Zone Z2 và đều lưu ciphertext – **chiến lược bảo mật không thay đổi** giữa hai DB.

---

*Đề tài 18 – NT2205.11.CH | Học kỳ 1 – 2025–2026 | MedShare-Lab*
