# PQC worker — P4 (smoke test)

liboqs + liboqs-python: ML-KEM-768 (FIPS 203) và ML-DSA-65 (FIPS 204). Hiện chỉ có `smoke_test.py` (positive + negative: capsule 1.088 bytes, chữ ký 3.309 bytes).

Chưa tích hợp vào Gateway/Broker. WP9 (Tuần 11): descriptor/chữ ký cho manifest và checkpoint, archive ML-KEM, E8, TC-20 → TC-23. Không coi dual wrap cổ điển/PQ là end-to-end PQ security.
