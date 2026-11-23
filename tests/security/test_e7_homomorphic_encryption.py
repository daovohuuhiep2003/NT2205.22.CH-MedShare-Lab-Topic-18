"""
Security and Integrity Tests for Homomorphic Encryption (SEAL BFV) — Experiment E7.
Part of MedShare-Lab (Topic 18 — NT2205.11.CH).
Validates:
- TC-18: BFV Exact integer semantics within modulus bounds (Integer Exactness).
- TC-19: Theoretical Limit demonstration (Malicious worker tamper scenario).
- TC-30: Differencing attack mitigation (Minimum cohort threshold & overlap guard).
"""

import pytest
from medshare.crypto.he_client import (
    DifferencingAttackError,
    HeBfvClient,
    HomomorphicEncryptionError,
)


@pytest.fixture
def he_client():
    return HeBfvClient(min_cohort_size=5)


def test_tc18_integer_exactness_basic(he_client):
    """
    TC-18: Validates exact integer arithmetic over small and medium cohorts.
    Proves Integer Exactness: Decrypt(Enc(v1) + ... + Enc(vn)) == sum(vi).
    """
    values = [150, 350, 500, 1000]
    res = he_client.aggregate_sum(values)

    assert res["exact_match"] is True
    assert res["expected_sum"] == 2000
    assert res["actual_sum"] == 2000
    assert res["noise_budget_remaining"] > 100


def test_tc18_integer_exactness_edge_cases(he_client):
    """
    TC-18: Tests edge cases: single value, zeros, large numbers.
    """
    # 1. Single value
    res_single = he_client.aggregate_sum([54321])
    assert res_single["exact_match"] is True
    assert res_single["actual_sum"] == 54321

    # 2. Large numbers with zeros
    large_vals = [0, 125000, 350000, 500000]
    res_large = he_client.aggregate_sum(large_vals)
    assert res_large["exact_match"] is True
    assert res_large["actual_sum"] == 975000

    # 3. Empty list
    res_empty = he_client.aggregate_sum([])
    assert res_empty["actual_sum"] == 0
    assert res_empty["exact_match"] is True


def test_tc19_malicious_worker_tamper_limit_demonstrated(he_client):
    """
    TC-19: Simulates an untrusted / malicious cloud worker tampering with the sum ciphertext.
    Demonstrates the theoretical LIMIT boundary:
    BFV provides Confidentiality (cloud worker cannot read input costs),
    but BFV alone DOES NOT guarantee computation result authenticity.
    """
    tamper_offset = 750
    tamper_report = he_client.run_tamper_test(tamper_offset=tamper_offset)

    assert tamper_report["integrity_gap_demonstrated"] is True
    assert tamper_report["expected_honest_sum"] == 2000
    # Decrypted sum is tampered by exactly the offset without raising a decryption error
    assert tamper_report["decrypted_tampered_sum"] == 2000 + tamper_offset


def test_tc30_differencing_attack_under_threshold_rejected(he_client):
    """
    TC-30: Tests that cohort sizes below the minimum threshold (N < 5) are rejected.
    """
    small_cohort = ["rec-pt-001", "rec-pt-002", "rec-pt-003"]
    with pytest.raises(DifferencingAttackError, match="below the minimum threshold"):
        he_client.evaluate_cohort_privacy(small_cohort)


def test_tc30_differencing_attack_single_patient_isolated_rejected(he_client):
    """
    TC-30: Tests that an analyst cannot submit two overlapping cohorts differing by 1 patient
    to isolate that victim's private treatment cost via subtraction.
    """
    cohort_a = ["rec-pt-001", "rec-pt-002", "rec-pt-003", "rec-pt-004", "rec-pt-005"]
    # First query is approved
    assert he_client.evaluate_cohort_privacy(cohort_a) is True

    # Second query adds 1 new patient ("rec-pt-006") to the existing 5 patients
    # Difference is exactly 1 patient -> Isolates rec-pt-006!
    cohort_b = cohort_a + ["rec-pt-006"]
    with pytest.raises(DifferencingAttackError, match="Differencing attack detected"):
        he_client.evaluate_cohort_privacy(cohort_b)


def test_tc30_approved_independent_cohort_permitted(he_client):
    """
    TC-30: Validates that compliant, independent cohorts (>= 5 patients) are permitted.
    """
    cohort_1 = ["rec-pt-010", "rec-pt-011", "rec-pt-012", "rec-pt-013", "rec-pt-014"]
    assert he_client.evaluate_cohort_privacy(cohort_1) is True

    # Independent cohort with multiple differing patients
    cohort_2 = ["rec-pt-020", "rec-pt-021", "rec-pt-022", "rec-pt-023", "rec-pt-024"]
    assert he_client.evaluate_cohort_privacy(cohort_2) is True

