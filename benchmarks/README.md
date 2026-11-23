# Benchmark harness

| Script | Thí nghiệm | Ghi chú |
|---|---|---|
| `run_e1_baseline.py` | E1 — B0 plaintext vs B1 LUKS | TC-02, TC-08 |
| `run_e2_field_overhead.py` | E2 — field envelope + Vault KMS | TC-02, TC-06, TC-09, TC-10 |
| `run_e3_abac_bypass.py` | E3 — ABAC, break-glass, DBA bypass | TC-03, TC-04, TC-07, TC-27 |
| `run_e4_cpabe_sharing.py` | E4 — CP-ABE AC17 | cần `abe-worker` :9002 |
| `run_e5_leakage_analysis.py` | E5 — blind index leakage | TC-15 → TC-17 |
| `run_e7_homomorphic_sum.py` | E7 — BFV SUM | TC-18, TC-19, TC-30 |

Chạy: `PYTHONPATH=src:. .venv/bin/python benchmarks/<script>`. Output JSON ghi vào `results/` và evidence Markdown vào `evidence/runs/` — cả hai **không commit**. E8, E9 chưa có harness. Kế hoạch: [experiments](../docs/testing/experiments-and-validation.md).
