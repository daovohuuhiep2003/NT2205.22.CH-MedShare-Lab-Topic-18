"""
Integration & Security Tests for the Authenticated MedShare-Lab Web Portal API.

Covers:
- Unauthenticated & spoofed-header rejection (401)
- Strict HS256 JWT validation (wrong secret, tampered signature, alg=none)
- Role-based login determining real ABAC subjects (Doctor, Nurse, Patient, Family, Analyst, DBA, Admin)
- Multi-patient ABAC isolation (patient_alice vs patient_bob vs family_alice)
- Cloud DBA & Admin separation-of-duty restrictions (TC-27)
- Zone Z1 Admin account provisioning, immediate revocation (TC-07), restore, password rotation, and logout JTI revocation
- Zone Z1 HMAC-SHA-256 protection detecting DB-level role tampering
- CP-ABE export/decrypt & SEAL BFV homomorphic sum access controls
"""

import base64
import json
import uuid

from fastapi.testclient import TestClient
import pytest

from medshare.gateway.api import app, auth_service, mongo_storage, pdp


client = TestClient(app)


def _login(username: str, password: str):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    return resp


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ephemeral_users():
    """Tracks test-provisioned usernames and ensures clean teardown from MongoDB."""
    created_usernames = []
    yield created_usernames
    for uname in created_usernames:
        doc = auth_service.accounts_col.find_one({"username": uname})
        if doc and "user_id" in doc:
            pdp.restore_user(doc["user_id"])
        auth_service.accounts_col.delete_one({"username": uname})
        auth_service.revoked_tokens_col.delete_many({"username": uname})


# -----------------------------------------------------------------------------
# 1. Authentication & Spoofing Defense Tests
# -----------------------------------------------------------------------------

def test_unauthenticated_and_spoofed_headers_rejected():
    """Portal must reject unauthenticated requests and refuse legacy spoofable X-Role/X-Profile-Id headers."""
    assert client.get("/api/v1/patients").status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/dba/raw-records").status_code == 401
    assert client.get("/api/v1/audit/logs").status_code == 401
    assert client.get("/api/v1/auth/accounts").status_code == 401

    spoof_resp = client.get(
        "/api/v1/patients",
        headers={"X-Profile-Id": "doctor_cardio", "X-Role": "DOCTOR", "X-Department": "CARDIOLOGY"},
    )
    assert spoof_resp.status_code == 401


def test_wrong_password_and_tampered_jwt_rejected():
    """Wrong passwords and modified or alg=none JWTs must return 401."""
    bad_login = _login("dondg01", "WrongPassword!999")
    assert bad_login.status_code == 401

    good_login = _login("dondg01", "DoctorCardio@2026!")
    assert good_login.status_code == 200
    token = good_login.json()["access_token"]
    header_b64, payload_b64, sig_b64 = token.split(".")

    # Tamper payload claims (attempting privilege escalation)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4)))
    payload["role"] = "ADMIN"
    tampered_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    assert client.get("/api/v1/auth/me", headers=_bearer(f"{header_b64}.{tampered_payload}.{sig_b64}")).status_code == 401

    # Reject alg: none tokens
    none_header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode()
    assert client.get("/api/v1/auth/me", headers=_bearer(f"{none_header}.{payload_b64}.")).status_code == 401


# -----------------------------------------------------------------------------
# 2. Stakeholder Role Enforcement via Authenticated Login
# -----------------------------------------------------------------------------

def test_doctor_abac_and_attachments():
    """dondg01 (Dr. Nguyễn Đạo Ga Đô) sees Cardiology records decrypted, Oncology/Pediatrics denied (TC-03), and MinIO attachments."""
    token = _login("dondg01", "DoctorCardio@2026!").json()["access_token"]
    headers = _bearer(token)

    resp = client.get("/api/v1/patients", headers=headers)
    assert resp.status_code == 200
    records = {r["record_id"]: r for r in resp.json()["records"]}

    # rec-pat-002 is Cardiology (Ly Bao Binh) -> Permitted
    assert "rec-pat-002" in records
    assert records["rec-pat-002"]["access_status"] == "PERMITTED"
    assert records["rec-pat-002"]["fields"]["name"] == "Ly Bao Binh"
    assert "F41.1" in records["rec-pat-002"]["fields"]["diagnosis"]

    # rec-pat-001 is Pediatrics (Luong Thanh Hai) -> Denied TC-03
    assert "rec-pat-001" in records
    assert records["rec-pat-001"]["access_status"] == "DENIED"

    # rec-pat-005 is Oncology (Hoang Duc Khang) -> Denied TC-03
    assert "rec-pat-005" in records
    assert records["rec-pat-005"]["access_status"] == "DENIED"

    att_resp = client.get("/api/v1/attachments/rec-pat-002", headers=headers)
    assert att_resp.status_code == 200
    filenames = {a["filename"] for a in att_resp.json()["attachments"]}
    assert "chest_xray_pa.png" in filenames


def test_nurse_field_redaction():
    """mailt01 (ĐD. Lê Thị Mai) sees demographics only; diagnosis & notes remain redacted."""
    token = _login("mailt01", "NurseCardio@2026!").json()["access_token"]
    resp = client.get("/api/v1/patients", headers=_bearer(token))
    assert resp.status_code == 200

    records = {r["record_id"]: r for r in resp.json()["records"]}
    pat2 = records["rec-pat-002"]
    assert pat2["access_status"] == "PERMITTED"
    assert pat2["fields"]["name"] == "Ly Bao Binh"
    assert pat2["fields"]["diagnosis"] == "[REDACTED_BY_POLICY]"
    assert pat2["fields"]["notes"] == "[REDACTED_BY_POLICY]"


def test_patient_and_family_isolation():
    """Patients and Patient Family only view their bound patient_id and are blocked from others."""
    hai_token = _login("hailt001", "Patient@2026!").json()["access_token"]
    hai_recs = client.get("/api/v1/patients", headers=_bearer(hai_token)).json()["records"]
    assert [r["record_id"] for r in hai_recs] == ["rec-pat-001"]
    assert hai_recs[0]["fields"]["name"] == "Luong Thanh Hai"

    binh_token = _login("binhlb002", "Patient@2026!").json()["access_token"]
    binh_recs = client.get("/api/v1/patients", headers=_bearer(binh_token)).json()["records"]
    assert [r["record_id"] for r in binh_recs] == ["rec-pat-002"]
    assert binh_recs[0]["fields"]["name"] == "Ly Bao Binh"

    fam_token = _login("ngoclb002", "Patient@2026!").json()["access_token"]
    fam_recs = client.get("/api/v1/patients", headers=_bearer(fam_token)).json()["records"]
    assert [r["record_id"] for r in fam_recs] == ["rec-pat-002"]

    # hailt001 must not access rec-pat-002 attachments
    assert client.get("/api/v1/attachments/rec-pat-002", headers=_bearer(hai_token)).status_code == 403


def test_dba_and_analyst_privilege_boundaries():
    """Cloud DBA (tuanpm01) views ciphertext only (TC-27); Analyst (tamtm01) runs BFV SUM but cannot read raw DB or accounts."""
    dba_token = _login("tuanpm01", "CloudDba@2026!").json()["access_token"]
    dba_headers = _bearer(dba_token)

    pat_resp = client.get("/api/v1/patients", headers=dba_headers)
    assert pat_resp.status_code == 200
    assert pat_resp.json()["status"] == "DENIED"
    assert pat_resp.json()["records"] == []

    raw_resp = client.get("/api/v1/dba/raw-records", headers=dba_headers)
    assert raw_resp.status_code == 200
    assert raw_resp.json()["total_records"] >= 1000
    assert client.post("/api/v1/crypto/he/sum", json={"items": [100, 200]}, headers=dba_headers).status_code == 403
    assert client.get("/api/v1/auth/accounts", headers=dba_headers).status_code == 403
    assert client.get("/api/v1/audit/logs", headers=dba_headers).status_code == 403

    analyst_token = _login("tamtm01", "Analyst@2026!").json()["access_token"]
    analyst_headers = _bearer(analyst_token)
    he_resp = client.post("/api/v1/crypto/he/sum", json={"items": [1500000, 3200000]}, headers=analyst_headers)
    assert he_resp.status_code == 200
    assert he_resp.json()["homomorphic_sum"] == 4700000
    assert client.get("/api/v1/dba/raw-records", headers=analyst_headers).status_code == 403
    assert client.get("/api/v1/auth/accounts", headers=analyst_headers).status_code == 403


def test_blind_search_and_cpabe_flow():
    """Authenticated Doctor performs blind index search and CP-ABE policy export + decrypt check."""
    doc_token = _login("dondg01", "DoctorCardio@2026!").json()["access_token"]
    headers = _bearer(doc_token)

    # Search for diagnosis of rec-pat-002
    search_resp = client.post(
        "/api/v1/patients/blind-search",
        json={"field_name": "diagnosis", "query_value": "F41.1 - Roi loan lo au lan toa (Generalized anxiety disorder)"},
        headers=headers,
    )
    assert search_resp.status_code == 200
    assert any(r["record_id"] == "rec-pat-002" for r in search_resp.json()["records"])

    exp_resp = client.post(
        "/api/v1/crypto/abe/export",
        json={"record_id": "rec-pat-002", "policy": "(CARDIOLOGY AND DOCTOR)"},
        headers=headers,
    )
    assert exp_resp.status_code == 200
    pkg = exp_resp.json()["export_package"]

    ok_dec = client.post(
        "/api/v1/crypto/abe/decrypt-test",
        json={"export_package": pkg, "user_attributes": ["CARDIOLOGY", "DOCTOR"]},
        headers=headers,
    )
    assert ok_dec.status_code == 200
    assert ok_dec.json()["status"] == "SUCCESS"

    fail_dec = client.post(
        "/api/v1/crypto/abe/decrypt-test",
        json={"export_package": pkg, "user_attributes": ["ONCOLOGY", "NURSE"]},
        headers=headers,
    )
    assert fail_dec.status_code == 200
    assert fail_dec.json()["status"] == "POLICY_NOT_SATISFIED"


# -----------------------------------------------------------------------------
# 3. Admin Account Provisioning, Revocation (TC-07) & Z1 Integrity Protection
# -----------------------------------------------------------------------------

def test_admin_provisioning_revocation_logout_and_separation(ephemeral_users):
    """
    Tests:
    - Non-admin cannot create/list/revoke accounts (403)
    - ADMIN cannot read clinical EHR or decrypt CP-ABE (TC-27), but manages accounts & Z3 audit logs
    - Provisioned user authenticates cleanly and assumes exact issued role
    - Password change bumps attr_epoch and invalidates old JWT
    - Revoke (TC-07) immediately invalidates active Bearer JWT; restore allows fresh login
    - Logout revokes JWT JTI
    """
    doc_token = _login("dondg01", "DoctorCardio@2026!").json()["access_token"]
    assert client.post(
        "/api/v1/auth/accounts",
        json={
            "username": "unauth_try",
            "password": "Password@1234!",
            "full_name": "Should Fail",
            "role": "DOCTOR",
            "department": "CARDIOLOGY",
        },
        headers=_bearer(doc_token),
    ).status_code == 403

    admin_token = _login("anvb01", "Admin@MedShare2026!").json()["access_token"]
    admin_headers = _bearer(admin_token)

    # TC-27: ADMIN blocked from reading clinical records
    admin_pats = client.get("/api/v1/patients", headers=admin_headers)
    assert admin_pats.status_code == 200
    assert admin_pats.json()["status"] == "DENIED"

    # Admin reads Z3 audit log
    audit_resp = client.get("/api/v1/audit/logs", headers=admin_headers)
    assert audit_resp.status_code == 200
    assert "events" in audit_resp.json()

    # Provision an ephemeral Oncology Doctor account
    uname = f"prov_onco_{uuid.uuid4().hex[:6]}"
    ephemeral_users.append(uname)
    create_resp = client.post(
        "/api/v1/auth/accounts",
        json={
            "username": uname,
            "password": "TempOnco@2026!",
            "full_name": "Dr. Temp Oncology",
            "role": "DOCTOR",
            "department": "ONCOLOGY",
        },
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["account"]["integrity_ok"] is True

    # New user logs in -> determines ONCOLOGY DOCTOR role (permits rec-pat-005, denies rec-pat-002)
    u_login = _login(uname, "TempOnco@2026!")
    assert u_login.status_code == 200
    u_token = u_login.json()["access_token"]
    u_recs = {r["record_id"]: r for r in client.get("/api/v1/patients", headers=_bearer(u_token)).json()["records"]}
    assert u_recs["rec-pat-005"]["access_status"] == "PERMITTED"
    assert u_recs["rec-pat-002"]["access_status"] == "DENIED"

    # Password rotation invalidates previous token (epoch bump)
    pw_resp = client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "TempOnco@2026!", "new_password": "RotatedOnco@2026!"},
        headers=_bearer(u_token),
    )
    assert pw_resp.status_code == 200
    assert client.get("/api/v1/auth/me", headers=_bearer(u_token)).status_code == 401

    # Log in with new password
    u_token_2 = _login(uname, "RotatedOnco@2026!").json()["access_token"]
    assert client.get("/api/v1/auth/me", headers=_bearer(u_token_2)).status_code == 200

    # Immediate revocation (TC-07) invalidates active Bearer token immediately
    rev_resp = client.post(f"/api/v1/auth/accounts/{uname}/revoke", headers=admin_headers)
    assert rev_resp.status_code == 200
    assert client.get("/api/v1/auth/me", headers=_bearer(u_token_2)).status_code == 401
    assert _login(uname, "RotatedOnco@2026!").status_code == 401

    # Restore allows fresh login, while pre-revocation token stays invalid
    res_resp = client.post(f"/api/v1/auth/accounts/{uname}/restore", headers=admin_headers)
    assert res_resp.status_code == 200
    assert client.get("/api/v1/auth/me", headers=_bearer(u_token_2)).status_code == 401

    u_token_3 = _login(uname, "RotatedOnco@2026!").json()["access_token"]
    assert client.post("/api/v1/auth/logout", headers=_bearer(u_token_3)).status_code == 200
    assert client.get("/api/v1/auth/me", headers=_bearer(u_token_3)).status_code == 401


def test_db_role_tampering_detected_by_z1_hmac(ephemeral_users):
    """Direct MongoDB role elevation without Z1 HMAC key must fail verification."""
    admin_token = _login("anvb01", "Admin@MedShare2026!").json()["access_token"]
    admin_headers = _bearer(admin_token)

    uname = f"tamper_pat_{uuid.uuid4().hex[:6]}"
    ephemeral_users.append(uname)
    resp = client.post(
        "/api/v1/auth/accounts",
        json={
            "username": uname,
            "password": "PatientTemp@2026!",
            "full_name": "Tamper Target",
            "role": "PATIENT",
            "department": "PATIENT_PORTAL",
            "patient_id": "rec-pat-001",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201

    token = _login(uname, "PatientTemp@2026!").json()["access_token"]
    assert client.get("/api/v1/auth/me", headers=_bearer(token)).status_code == 200

    # Attacker compromises Zone Z2 MongoDB and elevates role to ADMIN without Z1 mac_key
    mongo_storage.db["z1_identity_accounts"].update_one(
        {"username": uname},
        {"$set": {"role": "ADMIN", "department": "SECURITY"}},
    )

    # Active JWT must fail (401) and subsequent login must fail (403 HMAC violation)
    assert client.get("/api/v1/auth/me", headers=_bearer(token)).status_code == 401
    assert _login(uname, "PatientTemp@2026!").status_code == 403

    accounts = client.get("/api/v1/auth/accounts", headers=admin_headers).json()["accounts"]
    tampered_row = next(a for a in accounts if a["username"] == uname)
    assert tampered_row["integrity_ok"] is False
