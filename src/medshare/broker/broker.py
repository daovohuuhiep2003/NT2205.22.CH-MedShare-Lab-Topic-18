"""
Key Broker module for MedShare-Lab.
Operates inside Zone Z1 as an independent Policy Enforcement Point (PEP).
Manages DEK generation, authenticated KMS wrapping, unwrap validation, and tenant isolation.
"""

import secrets
from typing import Any, Optional
import uuid

from medshare.broker.capsule import KeyCapsule
from medshare.broker.kms import KmsClientBase
from medshare.crypto.context import canonicalize_jcs
from medshare.crypto.errors import (
    AccessDeniedError,
    ContextMismatchError,
    InvalidKeyError,
    TenantIsolationViolationError,
)


class KeyBroker:
    """
    Key Broker PEP (Zone Z1).
    Ensures strict tenant isolation (TC-06), independent ABAC verification,
    and contextual binding before key release.
    """

    def __init__(
        self,
        kms_client: KmsClientBase,
        registry: Optional[dict[str, Any]] = None,
        pdp: Optional[Any] = None,
        master_search_secret: Optional[bytes] = None,
    ):
        self.kms = kms_client
        self.registry = registry if registry is not None else {}
        self.pdp = pdp
        self.master_search_secret = (
            master_search_secret
            if master_search_secret is not None
            else b"medshare_lab_master_search_root_secret_2026_z1_seed!"
        )

    def get_search_key(self, tenant_id: str, field_name: str, search_epoch: int = 1) -> bytes:
        """
        Derives an isolated search key for a tenant and field under the current search epoch.
        Enforces cryptographic separation via HKDF-SHA256 (CR-07 / M-06).
        """
        from medshare.crypto.blind_index import derive_search_key
        return derive_search_key(
            master_secret=self.master_search_secret,
            tenant_id=tenant_id,
            field_name=field_name,
            search_epoch=search_epoch,
        )

    @staticmethod
    def get_kek_name(tenant_id: str, data_class: str = "clinical") -> str:
        """Derives standard KEK identifier for a tenant and data classification."""
        clean_tenant = tenant_id.lower().replace("-", "_")
        clean_class = data_class.lower().replace("-", "_")
        return f"kek_{clean_tenant}_{clean_class}_v1"


    def issue_dek_and_capsule(
        self,
        tenant_id: str,
        record_id: str,
        data_class: str = "clinical",
        extra_context: Optional[dict[str, Any]] = None,
    ) -> tuple[bytes, KeyCapsule]:
        """
        Generates a fresh 256-bit CSPRNG DEK and wraps it under the tenant's KEK via KMS.
        DEK is released only in Z1 memory.
        Returns: (plaintext_dek_bytes, key_capsule)
        """
        if not tenant_id or not isinstance(tenant_id, str):
            raise InvalidKeyError("tenant_id must be a non-empty string")
        if not record_id or not isinstance(record_id, str):
            raise InvalidKeyError("record_id must be a non-empty string")

        kek_name = self.get_kek_name(tenant_id, data_class)

        # 1. Generate 32-byte CSPRNG DEK
        dek = secrets.token_bytes(32)

        # 2. Construct bound context for wrap domain
        bound_context: dict[str, Any] = {
            "data_class": data_class,
            "domain": "medshare/wrap/v1",
            "record_id": record_id,
            "tenant_id": tenant_id,
        }
        if extra_context:
            for k, v in extra_context.items():
                if k not in bound_context:
                    bound_context[k] = v

        # 3. Canonicalize context bytes for KMS AAD
        ctx_bytes = canonicalize_jcs(bound_context)

        # 4. Wrap DEK via Software KMS
        wrapped_dek, kek_version = self.kms.wrap_dek(kek_name, dek, context=ctx_bytes)

        # 5. Build KeyCapsule
        capsule_id = f"cap_{uuid.uuid4().hex}"
        capsule = KeyCapsule(
            capsule_id=capsule_id,
            capsule_version=1,
            tenant_id=tenant_id,
            kek_id=kek_name,
            kek_version=kek_version,
            wrapped_dek=wrapped_dek,
            bound_object_context=bound_context,
        )

        return dek, capsule

    def unwrap_dek(self, capsule: KeyCapsule, requesting_context: dict[str, Any]) -> bytes:
        """
        Unwraps DEK from KeyCapsule under strict context validation.
        Enforces TC-06 Tenant Isolation and anti-swapping boundary.
        """
        if not isinstance(capsule, KeyCapsule):
            raise ValueError("capsule must be a KeyCapsule instance")
        if not isinstance(requesting_context, dict):
            raise ValueError("requesting_context must be a dictionary")

        # 1. TC-06: Strict Multi-tenant boundary check
        requesting_tenant = requesting_context.get("tenant_id")
        if not requesting_tenant:
            raise TenantIsolationViolationError("Requesting context missing required 'tenant_id'")
        if requesting_tenant != capsule.tenant_id:
            raise TenantIsolationViolationError(
                f"Cross-tenant access blocked: Requesting tenant '{requesting_tenant}' "
                f"attempted to unwrap capsule belonging to tenant '{capsule.tenant_id}' (TC-06 violation)"
            )

        # 2. Independent Broker PEP verification (TC-27 Defense-in-depth)
        if self.pdp is not None:
            subject = requesting_context.get("subject")
            if subject is None:
                raise AccessDeniedError(
                    "Broker PEP: Direct unauthenticated unwrap request rejected without trusted subject (TC-27)"
                )
            from medshare.policy.abac import Action, ObjectAttributes
            obj_kind = capsule.bound_object_context.get("object_kind")
            action = Action.READ_ATTACHMENT if obj_kind == "medical_attachment" else Action.READ
            obj_dept = capsule.bound_object_context.get("department", "CARDIOLOGY")
            obj_attrs = ObjectAttributes(
                record_id=capsule.bound_object_context.get("record_id", ""),
                tenant_id=capsule.tenant_id,
                department=obj_dept,
                attachment_id=capsule.bound_object_context.get("attachment_id"),
                attachment_type=capsule.bound_object_context.get("modality"),
                sensitivity=capsule.bound_object_context.get("sensitivity", "CONFIDENTIAL"),
            )
            env_context = requesting_context.get("env")
            decision = self.pdp.evaluate(subject, obj_attrs, action, env=env_context)
            if not decision.is_permitted:
                raise AccessDeniedError(f"Broker PEP rejected unwrap: {decision.reason} (TC-03/TC-27)")

        # 3. Bound Record/Object Context Validation
        requesting_record = requesting_context.get("record_id")
        bound_record = capsule.bound_object_context.get("record_id")
        if requesting_record and bound_record and requesting_record != bound_record:
            raise ContextMismatchError(
                f"Record context mismatch: Capsule bound to record '{bound_record}', "
                f"but caller requested record '{requesting_record}'"
            )

        # 4. Freshness / Version Registry Check (TC-06 Anti-replay)
        if self.registry:
            registered_version = self.registry.get(capsule.capsule_id)
            if registered_version is not None and capsule.capsule_version < registered_version:
                raise ContextMismatchError(
                    f"Replay detected: Capsule {capsule.capsule_id} version {capsule.capsule_version} "
                    f"is stale (current registry version is {registered_version})"
                )

        # 5. Compute wrap context bytes
        ctx_bytes = capsule.compute_wrap_context_bytes()

        # 6. Call KMS to unwrap DEK
        plaintext_dek = self.kms.unwrap_dek(capsule.kek_id, capsule.wrapped_dek, context=ctx_bytes)
        return plaintext_dek

    def rewrap_capsule(self, capsule: KeyCapsule) -> KeyCapsule:
        """
        Rewraps capsule under the latest KEK version without exposing plaintext DEK (TC-09).
        Preserves data ciphertext digest while advancing key lifecycle.
        """
        ctx_bytes = capsule.compute_wrap_context_bytes()
        new_wrapped_dek, new_kek_version = self.kms.rewrap_dek(
            capsule.kek_id, capsule.wrapped_dek, context=ctx_bytes
        )

        return KeyCapsule(
            capsule_id=capsule.capsule_id,
            capsule_version=capsule.capsule_version + 1,
            tenant_id=capsule.tenant_id,
            kek_id=capsule.kek_id,
            kek_version=new_kek_version,
            wrapped_dek=new_wrapped_dek,
            bound_object_context=capsule.bound_object_context,
        )

