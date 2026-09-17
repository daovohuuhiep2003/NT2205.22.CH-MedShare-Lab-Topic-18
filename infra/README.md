# Hạ tầng lab — chưa triển khai

Dự kiến Ubuntu Server/VM, Docker Compose, PostgreSQL/MongoDB, gateway, broker/software KMS, PDP/attribute sources, registry và audit độc lập về quyền quản trị.

Chưa có Compose hoặc container image đã kiểm chứng; không đặt service placeholder/password mặc định để tạo cảm giác stack chạy được. Tạo cấu hình thật sau feasibility spike, pin image/dependency và thêm health/config tests.

Runtime volumes chỉ lưu trong infra/runtime/ (gitignored). Secrets cấp qua secret file/store cục bộ, không commit hoặc truyền trong command-line. Lab volume encryption không thay field encryption và container không chống host administrator.
