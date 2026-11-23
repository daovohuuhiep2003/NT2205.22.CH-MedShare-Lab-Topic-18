"""
Unit tests for ABAC Policy Engine, Break-Glass, and Clinical Gateway Service.
"""

from datetime import datetime, timezone, timedelta
import unittest

from medshare.broker import KeyBroker, MockKmsClient
from medshare.crypto import FieldCipherEngine
from medshare.crypto.errors import AccessDeniedError
from medshare.gateway import ClinicalGatewayService
from medshare.policy import (
    AbacPolicyEngine,
    Action,
    BreakGlassTicket,
    DecisionOutcome,
    EnvironmentContext,
    ObjectAttributes,
    SubjectAttributes,
)


class AbacAndGatewayUnitTests(unittest.TestCase):
    def setUp(self):
        self.pdp = AbacPolicyEngine()
        self.mock_kms = MockKmsClient()
        self.broker = KeyBroker(self.mock_kms, pdp=self.pdp)
        self.engine = FieldCipherEngine()

    def test_abac_doctor_same_dept_permit(self):
        doc = SubjectAttributes("d1", "hospital_a", "DOCTOR", "CARDIOLOGY")
        obj = ObjectAttributes("r1", "hospital_a", "CARDIOLOGY")
        decision = self.pdp.evaluate(doc, obj, Action.READ)
        self.assertTrue(decision.is_permitted)
        self.assertIn("diagnosis", decision.allowed_fields)

    def test_abac_doctor_diff_dept_deny_tc03(self):
        doc = SubjectAttributes("d1", "hospital_a", "DOCTOR", "CARDIOLOGY")
        obj = ObjectAttributes("r2", "hospital_a", "ONCOLOGY")
        decision = self.pdp.evaluate(doc, obj, Action.READ)
        self.assertFalse(decision.is_permitted)
        self.assertIn("does not match", decision.reason)

    def test_abac_cross_tenant_deny_tc03(self):
        doc = SubjectAttributes("d1", "hospital_b", "DOCTOR", "CARDIOLOGY")
        obj = ObjectAttributes("r1", "hospital_a", "CARDIOLOGY")
        decision = self.pdp.evaluate(doc, obj, Action.READ)
        self.assertFalse(decision.is_permitted)
        self.assertIn("Cross-tenant", decision.reason)

    def test_abac_nurse_field_projection(self):
        nurse = SubjectAttributes("n1", "hospital_a", "NURSE", "CARDIOLOGY")
        obj = ObjectAttributes("r1", "hospital_a", "CARDIOLOGY")
        decision = self.pdp.evaluate(nurse, obj, Action.READ)
        self.assertTrue(decision.is_permitted)
        self.assertIn("name", decision.allowed_fields)
        self.assertNotIn("diagnosis", decision.allowed_fields)
        self.assertNotIn("notes", decision.allowed_fields)

    def test_abac_admin_denied_tc27(self):
        admin = SubjectAttributes("adm1", "hospital_a", "ADMIN", "IT")
        obj = ObjectAttributes("r1", "hospital_a", "CARDIOLOGY")
        decision = self.pdp.evaluate(admin, obj, Action.READ)
        self.assertFalse(decision.is_permitted)
        self.assertIn("restricted", decision.reason.lower())

    def test_abac_user_revocation_tc07(self):
        doc = SubjectAttributes("d1", "hospital_a", "DOCTOR", "CARDIOLOGY")
        obj = ObjectAttributes("r1", "hospital_a", "CARDIOLOGY")
        self.pdp.revoke_user("d1")
        decision = self.pdp.evaluate(doc, obj, Action.READ)
        self.assertFalse(decision.is_permitted)
        self.assertIn("revoked", decision.reason.lower())
        self.pdp.restore_user("d1")

    def test_abac_break_glass_valid_and_expired_tc04(self):
        doc = SubjectAttributes("d1", "hospital_a", "DOCTOR", "CARDIOLOGY")
        obj = ObjectAttributes("r2", "hospital_a", "ONCOLOGY")
        now = datetime.now(timezone.utc)

        ticket = BreakGlassTicket(
            ticket_id="bg_unit_01",
            subject_id="d1",
            approver_id="head_physician",
            tenant_id="hospital_a",
            record_id="r2",
            reason="Acute trauma",
            valid_from=now - timedelta(minutes=5),
            valid_until=now + timedelta(minutes=30),
        )
        self.pdp.register_break_glass_ticket(ticket)

        # Valid ticket
        env_valid = EnvironmentContext(is_emergency=True, break_glass_ticket_id="bg_unit_01", current_time=now)
        d_valid = self.pdp.evaluate(doc, obj, Action.READ, env=env_valid)
        self.assertTrue(d_valid.is_permitted)
        self.assertTrue(d_valid.is_break_glass)

        # Expired ticket
        env_exp = EnvironmentContext(is_emergency=True, break_glass_ticket_id="bg_unit_01", current_time=now + timedelta(hours=1))
        d_exp = self.pdp.evaluate(doc, obj, Action.READ, env=env_exp)
        self.assertFalse(d_exp.is_permitted)


if __name__ == "__main__":
    unittest.main()

