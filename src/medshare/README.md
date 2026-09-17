# Python core — khung khởi tạo

- gateway/: xác thực, query planning, field projection và PEP.
- crypto/: envelope, AAD/nonce, adapters; không tự viết primitive.
- broker/: key release, current-state, lifecycle và PEP độc lập.
- policy/: thuộc tính tin cậy và ABAC decisions.
- storage/: schema/adapter SQL và NoSQL, RLS bổ trợ, equality index.

Các thư mục là ranh giới trách nhiệm dự kiến, không hàm đã implement. Xem [thiết kế](../../docs/design/crypto-and-protocol-design.md) và [plan](../../docs/planning/implementation-plan.md).
