"""
Security tests for Experiment E3: ABAC Bypass & Gate Tuần 6 Verification.
Validates TC-03, TC-04, TC-07, and TC-27.
"""

import unittest
from benchmarks.run_e3_abac_bypass import E3BenchmarkRunner


class E3AbacBypassSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = E3BenchmarkRunner()
        cls.runner.setup()

    def test_tc03_department_mismatch_and_cross_tenant_denied(self):
        """TC-03: Verifies department mismatch and cross-tenant requests are blocked."""
        res = self.runner.test_tc03_department_and_cross_tenant_rejection()
        self.assertTrue(res["passed"])
        self.assertTrue(res["dept_mismatch_denied"])
        self.assertTrue(res["cross_tenant_denied"])
        self.assertEqual(res["status"], "PASSED")

    def test_tc04_emergency_break_glass_lifecycle(self):
        """TC-04: Verifies break-glass permissions and expired/forged ticket rejections."""
        res = self.runner.test_tc04_emergency_break_glass_lifecycle()
        self.assertTrue(res["passed"])
        self.assertTrue(res["valid_break_glass_permitted"])
        self.assertTrue(res["expired_break_glass_denied"])
        self.assertTrue(res["forged_ticket_denied"])
        self.assertEqual(res["status"], "PASSED")

    def test_tc07_immediate_user_revocation_linearity(self):
        """TC-07: Verifies revoked users are blocked immediately."""
        res = self.runner.test_tc07_immediate_user_revocation()
        self.assertTrue(res["passed"])
        self.assertTrue(res["access_blocked_after_revocation"])
        self.assertEqual(res["status"], "PASSED")

    def test_tc27_dba_bypass_fails_at_broker_pep(self):
        """TC-27: Critical Gate Tuần 6 - DBA bypasses DB RLS but fails at Key Broker PEP."""
        res = self.runner.test_tc27_dba_bypass_fails_at_broker()
        self.assertTrue(res["passed"])
        self.assertTrue(res["direct_broker_invoke_blocked"])
        self.assertTrue(res["dba_role_subject_blocked"])
        self.assertEqual(res["status"], "PASSED")


if __name__ == "__main__":
    unittest.main()

