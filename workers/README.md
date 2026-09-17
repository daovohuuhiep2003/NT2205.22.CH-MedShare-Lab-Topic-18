# Independent crypto workers

P2 CP-ABE, P3 BFV và P4 PQC chạy riêng khỏi Python core. Mỗi worker phải có exact scheme/parameters, version pin, positive/negative tests và protocol boundary trước tích hợp. Không cài chung mọi dependency nghiên cứu vào gateway.

Chưa có runtime, container image hoặc crypto implementation. Feasibility gate tuần 1–2 quyết định stack và lockfile bằng package manager.
