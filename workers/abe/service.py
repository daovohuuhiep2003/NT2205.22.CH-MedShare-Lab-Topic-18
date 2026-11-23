"""
MedShare-Lab (Topic 18 — NT2205.11.CH)
FastAPI REST Microservice cho CP-ABE Worker (workers/abe/)
Cổng dịch vụ: 9002
"""

import base64
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from engine import CpAbeEngine

app = FastAPI(
    title="MedShare-Lab CP-ABE Worker Microservice",
    version="1.0.0",
    description="Microservice cung cấp năng lực mã hóa thuộc tính CP-ABE (Scheme AC17 + AEAD AES-256-GCM) cho Profile P2.",
)

# Cache các engine theo đường cong
_ENGINES: Dict[str, CpAbeEngine] = {}

def get_engine(curve: str = "BN254") -> CpAbeEngine:
    c = curve.upper()
    if c not in _ENGINES:
        _ENGINES[c] = CpAbeEngine(curve=c)
    return _ENGINES[c]


class SetupRequest(BaseModel):
    curve: Optional[str] = "BN254"

class KeygenRequest(BaseModel):
    curve: Optional[str] = "BN254"
    pk: str
    msk: str
    attributes: List[str]

class ExportPackageRequest(BaseModel):
    curve: Optional[str] = "BN254"
    pk: str
    payload_b64: str
    policy: str
    tenant_id: str
    epoch_id: str
    metadata: Optional[Dict[str, Any]] = None

class DecryptPackageRequest(BaseModel):
    curve: Optional[str] = "BN254"
    pk: str
    package: Dict[str, Any]
    sk: str

class CollusionTestRequest(BaseModel):
    curve: Optional[str] = "BN254"
    pk: str
    msk: str
    policy: str
    u1_attrs: List[str]
    u2_attrs: List[str]
    u3_authorized_attrs: List[str]


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "medshare-abe-worker",
        "supported_curves": ["BN254", "SS512", "MNT224"],
        "default_curve": "BN254",
        "scheme": "AC17-CPABE",
        "time": time.time(),
    }


@app.post("/api/v1/setup")
def setup_authority(req: SetupRequest):
    try:
        engine = get_engine(req.curve or "BN254")
        pk_b64, msk_b64, desc = engine.setup()
        return {
            "status": "success",
            "pk": pk_b64,
            "msk": msk_b64,
            "descriptor": desc,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/keygen")
def generate_user_key(req: KeygenRequest):
    try:
        engine = get_engine(req.curve or "BN254")
        sk_b64 = engine.keygen(req.pk, req.msk, req.attributes)
        return {
            "status": "success",
            "sk": sk_b64,
            "attributes": [a.strip().upper() for a in req.attributes],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/export/package")
def create_export_package(req: ExportPackageRequest):
    try:
        engine = get_engine(req.curve or "BN254")
        payload = base64.b64decode(req.payload_b64.encode("ascii"))
        package = engine.create_export_package(
            pk_b64=req.pk,
            payload=payload,
            policy=req.policy,
            tenant_id=req.tenant_id,
            epoch_id=req.epoch_id,
            metadata=req.metadata,
        )
        return {
            "status": "success",
            "package": package,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/export/decrypt")
def decrypt_export_package(req: DecryptPackageRequest):
    try:
        engine = get_engine(req.curve or "BN254")
        payload = engine.decrypt_export_package(
            pk_b64=req.pk,
            package=req.package,
            sk_b64=req.sk,
        )
        return {
            "status": "success",
            "payload_b64": base64.b64encode(payload).decode("ascii"),
        }
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/collusion/test")
def test_collusion(req: CollusionTestRequest):
    try:
        engine = get_engine(req.curve or "BN254")
        result = engine.test_collusion(
            pk_b64=req.pk,
            msk_b64=req.msk,
            policy=req.policy,
            u1_attrs=req.u1_attrs,
            u2_attrs=req.u2_attrs,
            u3_authorized_attrs=req.u3_authorized_attrs,
        )
        return {
            "status": "success",
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9002)

