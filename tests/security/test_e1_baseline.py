"""
Security tests for Experiment E1 (Baseline B0 vs B1) and Security Boundaries.
Topic 18 — NT2205.11.CH (MedShare-Lab).

Tests:
- TC-08: Stolen snapshot volume encryption check (Threat T-01).
- TC-02: Direct DBA query bypass vulnerability verification (Threat T-02).
- Differential Plaintext Oracle integrity check.
"""

import math
import random
import sys
import unittest
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from benchmarks.run_e1_baseline import compute_shannon_entropy, E1BaselineHarness


class E1SecurityBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.harness = E1BaselineHarness()

    def test_tc08_stolen_snapshot_offline_confidentiality(self):
        """TC-08: Encrypted volume snapshot without key must exhibit near-ideal entropy and no plaintext."""
        res = self.harness.test_security_boundary_tc08()
        self.assertTrue(res["offline_disk_confidentiality"])
        self.assertGreater(res["volume_entropy_bits_per_byte"], 7.99)
        self.assertEqual(len(res["plaintext_canaries_found"]), 0)

    def test_tc02_direct_dba_query_bypass_vulnerability(self):
        """
        TC-02: Direct DBA query bypasses volume encryption (B1 limitation).
        Verifies that active database queries by DBA directly leak plaintext.
        """
        res = self.harness.test_fatal_limitation_tc02()
        self.assertTrue(res["vulnerability_confirmed"])
        self.assertEqual(res["plaintext_exposure_rate"], "100.0%")
        self.assertGreater(len(res["leaked_plaintext_samples"]), 0)

    def test_shannon_entropy_calculation(self):
        """Verify Shannon entropy helper accurately detects uniform vs biased bytes."""
        # High entropy: purely random bytes
        rng = random.Random(123)
        random_bytes = rng.randbytes(10000)
        self.assertGreater(compute_shannon_entropy(random_bytes), 7.9)

        # Low entropy: repeated byte
        repeated_bytes = b"A" * 10000
        self.assertAlmostEqual(compute_shannon_entropy(repeated_bytes), 0.0, places=3)


if __name__ == "__main__":
    unittest.main()

