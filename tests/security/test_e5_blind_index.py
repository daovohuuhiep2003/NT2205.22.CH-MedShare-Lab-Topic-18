"""
Security tests for Experiment E5: Equality Blind Index & Leakage Inference.
Validates TC-15, TC-16, and TC-17.
"""

import unittest
from benchmarks.run_e5_leakage_analysis import E5BenchmarkRunner


class E5BlindIndexSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = E5BenchmarkRunner()
        cls.runner.setup()

    def test_tc15_equality_correctness_and_unsupported_rejection(self):
        """TC-15: Verifies exact equality correctness, Unicode NFC, update/delete, and 422 rejections."""
        res = self.runner.test_tc15_equality_correctness_and_unsupported_rejections()
        self.assertTrue(res["passed"])
        self.assertTrue(res["exact_match_pass"])
        self.assertTrue(res["unicode_norm_pass"])
        self.assertTrue(res["delete_lifecycle_pass"])
        self.assertTrue(res["all_unsupported_queries_rejected_422"])
        self.assertEqual(res["status"], "PASSED")

    def test_tc16_frequency_inference_leakage_advantage(self):
        """TC-16: Verifies frequency inference on skewed vs uniform distribution with independent auxiliary data."""
        res = self.runner.test_tc16_frequency_inference_and_leakage_advantage()
        self.assertTrue(res["passed"])
        self.assertGreaterEqual(res["skewed_distribution"]["micro_accuracy"], 0.50)
        self.assertTrue(res["skewed_distribution"]["top_1_token_inferred_correct"])
        self.assertGreater(
            res["skewed_distribution"]["micro_accuracy"],
            res["uniform_distribution"]["micro_accuracy"],
        )
        self.assertEqual(res["status"], "PASSED")

    def test_tc17_active_tampering_post_filter_rejection(self):
        """TC-17: Verifies Gateway post-filter drops spurious candidates and acknowledges omission limits."""
        res = self.runner.test_tc17_active_tampering_and_omission_limits()
        self.assertTrue(res["passed"])
        self.assertTrue(res["spurious_candidate_rejected_by_post_filter"])
        self.assertTrue(res["design_limit_omission_acknowledged"])
        self.assertEqual(res["status"], "PASSED")


if __name__ == "__main__":
    unittest.main()

