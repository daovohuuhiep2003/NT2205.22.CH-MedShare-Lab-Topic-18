"""
Homomorphic Encryption (HE) Client & Gateway Adapter for MedShare-Lab.
Topic 18 — NT2205.11.CH (Master of Information Assurance).
WP7 — Microsoft SEAL v4.1.2 BFV Integer Aggregation (SUM/Count).

Coordinates:
- Zone Z1 (Data Owner / Hospital): BFV Key generation, plaintext encoding, and decryption.
- Zone Z2 (Untrusted Cloud Worker): Homomorphic addition (evaluator.add) on ciphertexts.
- Security Policies:
  - TC-18: BFV Exact integer semantics within modulus bounds.
  - TC-19: Integrity-gap demonstration (malicious worker tamper detection / limit).
  - TC-30: Differencing attack mitigation (minimum cohort threshold & overlap guard).
"""

import json
import os
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional, Set, Tuple

from medshare.crypto.errors import AccessDeniedError, CryptoError

ROOT_DIR = Path(__file__).resolve().parents[3]
HE_BIN_PATH = ROOT_DIR / "workers" / "he" / "seal_bfv_engine"
DEFAULT_MIN_COHORT_SIZE = 5


class HomomorphicEncryptionError(CryptoError):
    """Raised when HE evaluation, encryption, or parameters fail."""
    pass


class DifferencingAttackError(AccessDeniedError):
    """Raised when an analyst query attempts differencing inference on individuals (TC-30)."""
    pass


class HeBfvClient:
    """
    Client adapter communicating with the SEAL BFV Homomorphic Encryption engine.
    """

    def __init__(self, binary_path: Optional[Path] = None, min_cohort_size: int = DEFAULT_MIN_COHORT_SIZE):
        self.binary_path = binary_path or HE_BIN_PATH
        self.min_cohort_size = min_cohort_size
        self._cached_queries: List[Set[str]] = []

    def _execute_engine(self, args: List[str]) -> Dict[str, Any]:
        """Executes the C++ SEAL engine binary and parses JSON response."""
        cmd = [str(self.binary_path)] + args
        if not self.binary_path.exists():
            # If native binary not found on host, fallback to Docker container
            cmd = ["docker", "run", "--rm", "medshare-he-worker:latest", "/app/build/seal_bfv_engine"] + args

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(res.stdout)
        except subprocess.CalledProcessError as e:
            raise HomomorphicEncryptionError(
                f"SEAL BFV engine failed (code {e.returncode}): {e.stderr}"
            ) from e
        except json.JSONDecodeError as e:
            raise HomomorphicEncryptionError(
                f"Failed to parse BFV engine output JSON: {e}"
            ) from e

    def aggregate_sum(self, values: List[int]) -> Dict[str, Any]:
        """
        Executes homomorphic SUM across an array of integer values (TC-18).
        Enforces integer exactness: Decrypt(Enc(v1) + ... + Enc(vn)) == sum(vi).
        """
        if not values:
            return {
                "n_items": 0,
                "expected_sum": 0,
                "actual_sum": 0,
                "exact_match": True,
                "noise_budget_remaining": 145,
            }

        args = ["aggregate"] + [str(v) for v in values]
        raw = self._execute_engine(args)
        run_data = raw["runs"][0]
        return {
            "n_items": run_data["cohort_size"],
            "expected_sum": run_data["expected_sum"],
            "actual_sum": run_data["actual_sum"],
            "exact_match": run_data["exact_match"],
            "noise_budget_remaining": run_data["noise_budget_remaining"],
            "timings_ms": run_data["timings_ms"],
            "ciphertext_bytes": run_data["total_ciphertext_bytes"],
            "expansion_ratio": run_data["expansion_ratio"],
        }

    def run_benchmark(self, cohort_sizes: List[int]) -> Dict[str, Any]:
        """Runs the multi-cohort benchmark for Experiment E7."""
        args = ["benchmark"] + [str(sz) for sz in cohort_sizes]
        return self._execute_engine(args)

    def run_tamper_test(self, tamper_offset: int = 500) -> Dict[str, Any]:
        """
        Executes TC-19: Malicious worker tamper scenario.
        Demonstrates that an unauthenticated malicious cloud worker can tamper with
        the homomorphic sum ciphertext, proving the theoretical LIMIT of BFV.
        """
        args = ["tamper_test", str(tamper_offset)]
        return self._execute_engine(args)

    def evaluate_cohort_privacy(
        self,
        current_cohort_patient_ids: List[str],
        query_id: Optional[str] = None,
    ) -> bool:
        """
        TC-30: Enforces Differencing Attack Mitigation & Minimum Cohort Policy.
        
        Rules:
        1. Cardinality Rule: Cohort size must be >= min_cohort_size (e.g., N >= 5).
        2. Differencing Overlap Rule: If the symmetric difference between this query and
           any previously cached query is exactly 1 (or isolates a single individual),
           reject with DifferencingAttackError (HTTP 403 / 422 equivalent).
        """
        cohort_set = set(current_cohort_patient_ids)

        # 1. Check minimum cohort threshold
        if len(cohort_set) < self.min_cohort_size:
            raise DifferencingAttackError(
                f"Query rejected by privacy policy: Cohort size ({len(cohort_set)}) is below "
                f"the minimum threshold of {self.min_cohort_size} patients (TC-30)."
            )

        # 2. Check for differencing attack against prior query history
        for prior_set in self._cached_queries:
            # If prior set is a subset or superset with a single element difference
            diff = cohort_set.symmetric_difference(prior_set)
            if len(diff) == 1:
                victim_id = list(diff)[0]
                raise DifferencingAttackError(
                    f"Differencing attack detected: Query differs from prior query by exactly 1 patient "
                    f"('{victim_id}'). Access denied to protect individual confidentiality (TC-30)."
                )

        # Store in query history
        self._cached_queries.append(cohort_set)
        # Keep query history bounded
        if len(self._cached_queries) > 100:
            self._cached_queries.pop(0)

        return True

