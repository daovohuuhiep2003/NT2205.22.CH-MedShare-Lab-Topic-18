"""
Attribute-Based Access Control (ABAC) Engine for MedShare-Lab.
Operates in Zone Z1 under strict Deny-by-Default security principle.
Supports multi-tenant isolation, role-based field projection, emergency break-glass,
and immediate user revocation (TC-03, TC-04, TC-07, TC-27).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Set


class Action(str, Enum):
    """Allowed medical data actions."""
    READ = "READ"
    WRITE = "WRITE"
    SEARCH = "SEARCH"
    EXPORT = "EXPORT"
    READ_ATTACHMENT = "READ_ATTACHMENT"
    WRITE_ATTACHMENT = "WRITE_ATTACHMENT"


class DecisionOutcome(str, Enum):
    """ABAC Decision outcome."""
    PERMIT = "PERMIT"
    DENY = "DENY"


@dataclass(frozen=True)
class SubjectAttributes:
    """Attributes of the entity making the access request."""
    user_id: str
    tenant_id: str
    role: str               # e.g., "DOCTOR", "NURSE", "RESEARCHER", "ADMIN", "PATIENT"
    department: str         # e.g., "CARDIOLOGY", "ONCOLOGY", "EMERGENCY", "PATIENT_PORTAL"
    clearance: str = "CONFIDENTIAL"
    patient_id: Optional[str] = None


@dataclass(frozen=True)
class ObjectAttributes:
    """Attributes of the target clinical record or resource."""
    record_id: str
    tenant_id: str
    department: str         # e.g., "CARDIOLOGY", "ONCOLOGY"
    sensitivity: str = "CONFIDENTIAL"
    data_class: str = "clinical"
    attachment_id: Optional[str] = None
    attachment_type: Optional[str] = None  # e.g., "XRAY", "CT", "MRI", "ULTRASOUND", "LAB_REPORT"
    patient_id: Optional[str] = None


@dataclass(frozen=True)
class EnvironmentContext:
    """Environmental context during evaluation."""
    current_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_emergency: bool = False
    break_glass_ticket_id: Optional[str] = None
    ip_address: Optional[str] = None


@dataclass
class BreakGlassTicket:
    """Emergency break-glass authorization ticket."""
    ticket_id: str
    subject_id: str
    approver_id: str
    tenant_id: str
    record_id: str          # Specific record_id or "*" for emergency ward
    reason: str
    valid_from: datetime
    valid_until: datetime
    revoked: bool = False

    def is_valid(self, at_time: datetime, subject_id: str, tenant_id: str, record_id: str) -> tuple[bool, str]:
        if self.revoked:
            return False, "Break-glass ticket has been revoked"
        if at_time < self.valid_from:
            return False, "Break-glass ticket is not yet active"
        if at_time > self.valid_until:
            return False, "Break-glass ticket has expired"
        if self.subject_id != subject_id:
            return False, f"Ticket subject mismatch: expected {self.subject_id}, got {subject_id}"
        if self.tenant_id != tenant_id:
            return False, f"Ticket tenant mismatch: expected {self.tenant_id}, got {tenant_id}"
        if self.record_id != "*" and self.record_id != record_id:
            return False, f"Ticket record scope mismatch: expected {self.record_id}, got {record_id}"
        return True, "Valid ticket"


@dataclass(frozen=True)
class PolicyDecision:
    """ABAC Decision result containing allowed field projection."""
    outcome: DecisionOutcome
    allowed_fields: Set[str]
    reason: str
    policy_version: int = 1
    is_break_glass: bool = False

    @property
    def is_permitted(self) -> bool:
        return self.outcome == DecisionOutcome.PERMIT


class AbacPolicyEngine:
    """
    Policy Decision Point (PDP) executing ABAC rules.
    Default Deny principle: No access is granted unless an explicit rule matches.
    """

    POLICY_VERSION = 1
    ALL_CLINICAL_FIELDS = {"name", "dob", "gender", "diagnosis", "notes"}
    DEMOGRAPHIC_FIELDS_ONLY = {"name", "dob", "gender"}
    DE_IDENTIFIED_FIELDS = {"dob", "gender"}
    ATTACHMENT_FIELDS = {"attachment_data", "metadata"}

    def __init__(self):
        # User revocation list for immediate offboarding (TC-07)
        self.revocation_list: set[str] = set()
        # Storage for registered break-glass tickets (TC-04)
        self.break_glass_tickets: dict[str, BreakGlassTicket] = {}

    def revoke_user(self, user_id: str) -> None:
        """Immediately revokes access for a user (TC-07)."""
        self.revocation_list.add(user_id)

    def restore_user(self, user_id: str) -> None:
        """Restores a revoked user."""
        self.revocation_list.discard(user_id)

    def register_break_glass_ticket(self, ticket: BreakGlassTicket) -> None:
        """Registers an approved break-glass ticket."""
        self.break_glass_tickets[ticket.ticket_id] = ticket

    def revoke_break_glass_ticket(self, ticket_id: str) -> None:
        """Revokes an emergency break-glass ticket."""
        if ticket_id in self.break_glass_tickets:
            self.break_glass_tickets[ticket_id].revoked = True

    def evaluate(
        self,
        subject: SubjectAttributes,
        obj: ObjectAttributes,
        action: Action,
        env: Optional[EnvironmentContext] = None,
    ) -> PolicyDecision:
        """
        Evaluates an access request against ABAC rules.
        Enforces TC-03, TC-04, TC-07, and TC-27.
        """
        if env is None:
            env = EnvironmentContext()

        # 1. TC-07: Immediate User Revocation Check
        if subject.user_id in self.revocation_list:
            return PolicyDecision(
                outcome=DecisionOutcome.DENY,
                allowed_fields=set(),
                reason=f"Subject '{subject.user_id}' has been revoked (TC-07)",
                policy_version=self.POLICY_VERSION,
            )

        # 2. TC-27: Administrator / DBA Restriction
        # System administrators and DBAs NEVER have clinical data read access.
        if subject.role.upper() in ("ADMIN", "DBA", "SYSADMIN"):
            return PolicyDecision(
                outcome=DecisionOutcome.DENY,
                allowed_fields=set(),
                reason=f"Role '{subject.role}' is restricted from clinical medical records (TC-27)",
                policy_version=self.POLICY_VERSION,
            )

        # 3. Emergency Break-Glass Evaluation (TC-04)
        if env.is_emergency and env.break_glass_ticket_id:
            ticket = self.break_glass_tickets.get(env.break_glass_ticket_id)
            if not ticket:
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    allowed_fields=set(),
                    reason=f"Break-glass ticket '{env.break_glass_ticket_id}' not found",
                    policy_version=self.POLICY_VERSION,
                )
            is_valid, validation_msg = ticket.is_valid(
                at_time=env.current_time,
                subject_id=subject.user_id,
                tenant_id=obj.tenant_id,
                record_id=obj.record_id,
            )
            if not is_valid:
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    allowed_fields=set(),
                    reason=f"Break-glass validation failed: {validation_msg} (TC-04)",
                    policy_version=self.POLICY_VERSION,
                )
            # Valid Break-Glass override: Permit full clinical fields with emergency flag
            return PolicyDecision(
                outcome=DecisionOutcome.PERMIT,
                allowed_fields=self.ALL_CLINICAL_FIELDS,
                reason=f"Emergency Break-Glass authorized by {ticket.approver_id}: {ticket.reason}",
                policy_version=self.POLICY_VERSION,
                is_break_glass=True,
            )

        # 4. TC-03: Strict Multi-Tenant Boundary
        if subject.tenant_id != obj.tenant_id:
            return PolicyDecision(
                outcome=DecisionOutcome.DENY,
                allowed_fields=set(),
                reason=f"Cross-tenant access forbidden: {subject.tenant_id} != {obj.tenant_id} (TC-03)",
                policy_version=self.POLICY_VERSION,
            )

        # 5. Rule Evaluation by Role and Department
        role = subject.role.upper()
        subj_dept = subject.department.upper()
        obj_dept = obj.department.upper()

        # Rule 5.1: DOCTOR Access
        if role == "DOCTOR":
            if action in (Action.READ, Action.WRITE, Action.SEARCH):
                if subj_dept == obj_dept or subj_dept == "EMERGENCY":
                    return PolicyDecision(
                        outcome=DecisionOutcome.PERMIT,
                        allowed_fields=self.ALL_CLINICAL_FIELDS,
                        reason=f"Doctor authorized for {subj_dept} department clinical record",
                        policy_version=self.POLICY_VERSION,
                    )
                # TC-03: Department Mismatch
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    allowed_fields=set(),
                    reason=f"Doctor department '{subj_dept}' does not match record department '{obj_dept}' (TC-03)",
                    policy_version=self.POLICY_VERSION,
                )
            if action in (Action.READ_ATTACHMENT, Action.WRITE_ATTACHMENT):
                if subj_dept == obj_dept or subj_dept == "EMERGENCY":
                    return PolicyDecision(
                        outcome=DecisionOutcome.PERMIT,
                        allowed_fields=self.ATTACHMENT_FIELDS,
                        reason=f"Doctor authorized for {subj_dept} department medical attachment",
                        policy_version=self.POLICY_VERSION,
                    )
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    allowed_fields=set(),
                    reason=f"Doctor department '{subj_dept}' mismatch with record '{obj_dept}' for attachment",
                    policy_version=self.POLICY_VERSION,
                )

        # Rule 5.2: NURSE Access (Role-based field projection & attachment restrictions)
        if role == "NURSE":
            if action in (Action.READ, Action.WRITE):
                if subj_dept == obj_dept or subj_dept == "EMERGENCY":
                    # Nurses are restricted from sensitive psychiatric/oncology diagnosis details
                    return PolicyDecision(
                        outcome=DecisionOutcome.PERMIT,
                        allowed_fields=self.DEMOGRAPHIC_FIELDS_ONLY,
                        reason="Nurse authorized for demographic fields only (Field Projection)",
                        policy_version=self.POLICY_VERSION,
                    )
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    allowed_fields=set(),
                    reason=f"Nurse department '{subj_dept}' mismatch with '{obj_dept}'",
                    policy_version=self.POLICY_VERSION,
                )
            if action == Action.READ_ATTACHMENT:
                if subj_dept == obj_dept or subj_dept == "EMERGENCY":
                    # Nurse allowed for routine attachments (Lab reports, ultrasound, routine X-ray)
                    att_type = (obj.attachment_type or "").upper()
                    if att_type in ("LAB_REPORT", "ULTRASOUND", "XRAY") and obj.sensitivity != "CRITICAL":
                        return PolicyDecision(
                            outcome=DecisionOutcome.PERMIT,
                            allowed_fields=self.ATTACHMENT_FIELDS,
                            reason="Nurse authorized for routine medical attachment",
                            policy_version=self.POLICY_VERSION,
                        )
                    return PolicyDecision(
                        outcome=DecisionOutcome.DENY,
                        allowed_fields=set(),
                        reason=f"Nurse restricted from specialized/critical attachment type '{att_type}'",
                        policy_version=self.POLICY_VERSION,
                    )
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    allowed_fields=set(),
                    reason=f"Nurse department '{subj_dept}' mismatch with '{obj_dept}'",
                    policy_version=self.POLICY_VERSION,
                )
            if action == Action.WRITE_ATTACHMENT:
                if subj_dept == obj_dept or subj_dept == "EMERGENCY":
                    att_type = (obj.attachment_type or "").upper()
                    if att_type == "LAB_REPORT":
                        return PolicyDecision(
                            outcome=DecisionOutcome.PERMIT,
                            allowed_fields=self.ATTACHMENT_FIELDS,
                            reason="Nurse authorized to upload lab report",
                            policy_version=self.POLICY_VERSION,
                        )
                    return PolicyDecision(
                        outcome=DecisionOutcome.DENY,
                        allowed_fields=set(),
                        reason="Nurses are permitted to upload lab reports only",
                        policy_version=self.POLICY_VERSION,
                    )
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    allowed_fields=set(),
                    reason=f"Nurse department '{subj_dept}' mismatch with '{obj_dept}'",
                    policy_version=self.POLICY_VERSION,
                )

        # Rule 5.3: PATIENT / PATIENT_FAMILY Access (Self-access portal)
        if role in ("PATIENT", "PATIENT_FAMILY"):
            is_own_record = (
                subject.user_id == obj.record_id
                or (subject.patient_id and subject.patient_id == obj.patient_id)
                or (subject.patient_id and subject.patient_id == obj.record_id)
            )
            if not is_own_record:
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    allowed_fields=set(),
                    reason="Patient portal access strictly denied for other patients' records",
                    policy_version=self.POLICY_VERSION,
                )
            if action == Action.READ:
                return PolicyDecision(
                    outcome=DecisionOutcome.PERMIT,
                    allowed_fields=self.ALL_CLINICAL_FIELDS,
                    reason="Patient authorized to view own clinical record",
                    policy_version=self.POLICY_VERSION,
                )
            if action == Action.READ_ATTACHMENT:
                return PolicyDecision(
                    outcome=DecisionOutcome.PERMIT,
                    allowed_fields=self.ATTACHMENT_FIELDS,
                    reason="Patient authorized to view own medical attachments",
                    policy_version=self.POLICY_VERSION,
                )
            if action == Action.WRITE_ATTACHMENT:
                att_type = (obj.attachment_type or "").upper()
                if att_type in ("LAB_REPORT", "PATIENT_DOCUMENT", "HOME_HEALTH"):
                    return PolicyDecision(
                        outcome=DecisionOutcome.PERMIT,
                        allowed_fields=self.ATTACHMENT_FIELDS,
                        reason="Patient authorized to upload personal/lab documents",
                        policy_version=self.POLICY_VERSION,
                    )
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    allowed_fields=set(),
                    reason="Patient cannot upload clinical diagnostic radiology scans",
                    policy_version=self.POLICY_VERSION,
                )

        # Rule 5.4: RESEARCHER Access
        if role == "RESEARCHER":
            if action in (Action.READ, Action.EXPORT):
                # Researchers only receive de-identified cohorts
                return PolicyDecision(
                    outcome=DecisionOutcome.PERMIT,
                    allowed_fields=self.DE_IDENTIFIED_FIELDS,
                    reason="Researcher authorized for de-identified fields only",
                    policy_version=self.POLICY_VERSION,
                )
            return PolicyDecision(
                outcome=DecisionOutcome.DENY,
                allowed_fields=set(),
                reason="Researchers are not permitted to write records or access identifiable attachments",
                policy_version=self.POLICY_VERSION,
            )

        # 6. Default Deny Fallback
        return PolicyDecision(
            outcome=DecisionOutcome.DENY,
            allowed_fields=set(),
            reason="Access denied by default policy",
            policy_version=self.POLICY_VERSION,
        )

