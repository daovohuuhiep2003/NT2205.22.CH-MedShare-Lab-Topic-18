# Tests

- `tooling/`: parser/renderer, đồng bộ proposal và cấu trúc repository (16 tests, chạy trong CI qua `scripts/check_repo.py`).
- `unit/`: module ứng dụng — field crypto, KMS/broker, ABAC, blind index, dataset generator, Portal API.
- `security/`: test đối kháng theo TC (TC-01 → TC-19, TC-24, TC-27, TC-30).
- `integration/`: chưa có test riêng.

Chạy toàn bộ (cần Mongo + Vault + MinIO + abe-worker đang chạy):

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/ -q   # 100 passed (23/11/2026)
```

CI hiện chỉ chạy `tooling/`; unit/security cần lab nên chạy thủ công. Không dùng secret thật trong fixture.
