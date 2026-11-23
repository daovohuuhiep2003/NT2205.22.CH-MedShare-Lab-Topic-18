# Unit tests

`test_field_crypto.py` (TC-01, TC-24), `test_kms_broker.py` (TC-09), `test_abac_gateway.py` (TC-04, TC-07, TC-27), `test_blind_index.py` (TC-15, TC-17), `test_dataset_generator.py`, `test_portal_api.py` (đăng nhập, cấp/thu hồi tài khoản, tách tenant). `test_portal_api.py` cần Vault + MongoDB vì `gateway/api.py` seed dữ liệu khi import.

Xem [test catalog](../../docs/testing/experiments-and-validation.md).
