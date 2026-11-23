"""
Unit tests for Synthetic EHR Dataset Generator (Topic 18 — NT2205.11.CH).
"""

import sys
import unittest
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from datasets.generate_datasets import generate_dataset, build_oracle


class DatasetGeneratorTests(unittest.TestCase):
    def test_record_structure_and_types(self):
        records = generate_dataset(size=50, seed=1801, distribution="uniform")
        self.assertEqual(len(records), 50)

        required_fields = [
            "record_id", "tenant_id", "department", "classification",
            "external_patient_id", "name", "email", "diagnosis_code",
            "note", "amount_units", "created_at", "version"
        ]

        for r in records:
            for field in required_fields:
                self.assertIn(field, r)
            self.assertIn(r["tenant_id"], ["tenant_hospital_a", "tenant_hospital_b"])
            self.assertIn(r["classification"], ["CONFIDENTIAL", "RESTRICTED"])
            self.assertTrue(50 <= r["amount_units"] <= 1000)
            self.assertEqual(r["version"], 1)

    def test_record_id_uniqueness(self):
        records = generate_dataset(size=200, seed=1801, distribution="uniform")
        ids = [r["record_id"] for r in records]
        self.assertEqual(len(ids), len(set(ids)), "record_id must be completely unique")

    def test_oracle_consistency(self):
        records = generate_dataset(size=100, seed=1801, distribution="uniform")
        oracle = build_oracle(records)

        self.assertEqual(oracle["record_count"], 100)
        self.assertEqual(len(oracle["by_record_id"]), 100)
        self.assertEqual(sum(r["amount_units"] for r in records), oracle["total_amount_units"])

    def test_distribution_modes(self):
        uniform_records = generate_dataset(size=500, seed=1801, distribution="uniform")
        skewed_records = generate_dataset(size=500, seed=1801, distribution="skewed")

        # In skewed distribution, the top code should have significantly higher frequency
        skewed_oracle = build_oracle(skewed_records)
        diag_counts = list(skewed_oracle["diagnosis_counts"].values())
        max_freq = max(diag_counts)
        min_freq = min(diag_counts)
        self.assertGreater(max_freq, min_freq * 2, "Skewed distribution must exhibit power-law frequency difference")


if __name__ == "__main__":
    unittest.main()

