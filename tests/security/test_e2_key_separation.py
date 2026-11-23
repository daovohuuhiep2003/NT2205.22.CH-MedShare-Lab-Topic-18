"""
Adversarial security tests for Experiment E2: Key Separation & Storage Isolation.
Validates TC-02, TC-06, TC-09, and TC-10.
"""

import unittest
from benchmarks.run_e2_field_overhead import E2BenchmarkRunner


class E2KeySeparationSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = E2BenchmarkRunner(n_samples=10)
        cls.runner.setup()

    def test_tc02_direct_dba_query_returns_only_ciphertext(self):
        """TC-02: Verifies DBA query bypass vulnerability is eliminated."""
        res = self.runner.test_tc02_dba_bypass_mitigation()
        self.assertTrue(res["passed"])
        self.assertFalse(res["plaintext_exposed_to_dba"])
        self.assertEqual(res["status"], "PASSED")

    def test_tc06_multi_tenant_and_anti_replay_isolation(self):
        """TC-06: Verifies tenant boundary and stale version replay are rejected."""
        res = self.runner.test_tc06_tenant_isolation_and_replay()
        self.assertTrue(res["passed"])
        self.assertTrue(res["cross_tenant_blocked"])
        self.assertTrue(res["record_context_swap_blocked"])
        self.assertTrue(res["stale_version_replay_blocked"])
        self.assertEqual(res["status"], "PASSED")

    def test_tc09_kek_rotation_zero_data_mutation(self):
        """TC-09: Verifies KEK rotation and rewrap preserves data ciphertext hash."""
        res = self.runner.test_tc09_kek_rotation_and_rewrap()
        self.assertTrue(res["passed"])
        self.assertTrue(res["data_ciphertext_hash_preserved"])
        self.assertTrue(res["decrypt_succeeded_with_v2"])
        self.assertEqual(res["status"], "PASSED")

    def test_tc10_canary_plaintext_leakage_scan(self):
        """TC-10: Verifies 0 plaintext canary strings leak into database storage."""
        res = self.runner.test_tc10_canary_leakage_scan()
        self.assertTrue(res["passed"])
        self.assertEqual(res["plaintext_leaks_detected"], 0)
        self.assertEqual(res["status"], "PASSED")


if __name__ == "__main__":
    unittest.main()

