"""
MedShare-Lab (Topic 18 — NT2205.11.CH)
Python Adapter Client cho CP-ABE Worker (Scheme AC17 + AEAD AES-256-GCM)
Cung cấp giao diện kết nối giữa Trusted Gateway / Client với microservice medshare-abe-worker (:9002).
"""

import base64
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from medshare.crypto.errors import CryptoError


class CpAbeError(CryptoError):
    """Lỗi cơ bản trong các thao tác CP-ABE."""
    pass


class PolicyNotSatisfiedError(CpAbeError):
    """Ngoại lệ khi thuộc tính của người dùng không thỏa mãn Access Policy."""
    pass


class CollusionVulnerabilityError(CpAbeError):
    """Ngoại lệ an ninh khi phát hiện lỗ hổng thông đồng khóa (Collusion Attack)."""
    pass


class AbeClient:
    """
    Adapter giao tiếp với CP-ABE Worker microservice (hoặc CLI container fallback).
    Đóng vai trò là client SDK ở vùng Z0/Z1 để:
    - Quản lý Master Authority (setup, key issuance)
    - Đóng gói dữ liệu chia sẻ liên viện (Profile P2 KEM/DEM Export Package)
    - Giải mã và xác thực tính toàn vẹn gói chia sẻ
    - Thực hiện các thí nghiệm kiểm thử đối kháng (Collusion resistance, Epoch revocation).
    """

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        default_curve: str = "BN254",
        timeout: int = 30,
    ):
        self.endpoint_url = endpoint_url or os.getenv("MEDSHARE_ABE_URL", "http://127.0.0.1:9002")
        self.default_curve = default_curve
        self.timeout = timeout

    def _http_request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Gửi HTTP request đến worker qua REST API."""
        url = urllib.parse.urljoin(self.endpoint_url, path)
        data = None
        headers = {"Content-Type": "application/json"} if payload else {}

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                resp_bytes = response.read()
                return json.loads(resp_bytes.decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            if e.code == 403:
                raise PolicyNotSatisfiedError(f"HTTP 403: {err_body}")
            raise CpAbeError(f"HTTP {e.code}: {err_body}")
        except urllib.error.URLError as e:
            # Nếu daemon REST chưa chạy hoặc không kết nối được, thử fallback qua Docker CLI
            return self._docker_cli_fallback(path, payload)

    def _docker_cli_fallback(self, path: str, payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Phương án dự phòng gọi qua Docker container nếu HTTP endpoint không truy cập được."""
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        abe_dir = os.path.join(repo_root, "workers/abe")

        if path == "/health":
            return {"status": "ok", "service": "medshare-abe-worker-fallback"}

        if path == "/api/v1/setup":
            curve = (payload or {}).get("curve", self.default_curve)
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{abe_dir}:/app",
                "medshare-abe-worker:latest",
                "python3", "/app/cli.py", "setup", "--curve", curve
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(res.stdout)

        elif path == "/api/v1/keygen":
            p = payload or {}
            curve = p.get("curve", self.default_curve)
            attrs_str = ",".join(p.get("attributes", []))
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{abe_dir}:/app",
                "medshare-abe-worker:latest",
                "python3", "/app/cli.py", "keygen",
                "--curve", curve,
                "--pk", p["pk"],
                "--msk", p["msk"],
                "--attributes", attrs_str
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(res.stdout)

        elif path == "/api/v1/export/package":
            p = payload or {}
            curve = p.get("curve", self.default_curve)
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{abe_dir}:/app",
                "medshare-abe-worker:latest",
                "python3", "/app/cli.py", "package",
                "--curve", curve,
                "--pk", p["pk"],
                "--payload-b64", p["payload_b64"],
                "--policy", p["policy"],
                "--tenant-id", p["tenant_id"],
                "--epoch-id", p["epoch_id"]
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(res.stdout)

        elif path == "/api/v1/export/decrypt":
            p = payload or {}
            curve = p.get("curve", self.default_curve)
            pkg_json = json.dumps(p["package"])
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{abe_dir}:/app",
                "medshare-abe-worker:latest",
                "python3", "/app/cli.py", "decrypt",
                "--curve", curve,
                "--pk", p["pk"],
                "--package-json", pkg_json,
                "--sk", p["sk"]
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                raise PolicyNotSatisfiedError(f"Decryption failed in container: {res.stderr or res.stdout}")
            return json.loads(res.stdout)

        elif path == "/api/v1/collusion/test":
            p = payload or {}
            curve = p.get("curve", self.default_curve)
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{abe_dir}:/app",
                "medshare-abe-worker:latest",
                "python3", "/app/cli.py", "collusion",
                "--curve", curve,
                "--pk", p["pk"],
                "--msk", p["msk"],
                "--policy", p["policy"],
                "--u1", ",".join(p["u1_attrs"]),
                "--u2", ",".join(p["u2_attrs"]),
                "--u3", ",".join(p["u3_authorized_attrs"])
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(res.stdout)

        raise CpAbeError(f"Unsupported path for fallback: {path}")

    # -------------------------------------------------------------------------
    # Public SDK API
    # -------------------------------------------------------------------------

    def is_service_healthy(self) -> bool:
        """Kiểm tra worker service có hoạt động bình thường hay không."""
        try:
            res = self._http_request("GET", "/health")
            return res.get("status") == "ok"
        except Exception:
            return False

    def setup_authority(self, curve: Optional[str] = None) -> Tuple[str, str, Dict[str, Any]]:
        """
        Khởi tạo Master Authority của miền chia sẻ ABE.
        Trả về: (pk, msk, descriptor)
        """
        c = curve or self.default_curve
        resp = self._http_request("POST", "/api/v1/setup", {"curve": c})
        return resp["pk"], resp["msk"], resp["descriptor"]

    def issue_user_key(
        self,
        pk: str,
        msk: str,
        attributes: List[str],
        curve: Optional[str] = None,
    ) -> str:
        """Cấp phát khóa bí mật thuộc tính (SK) cho một người dùng định danh."""
        c = curve or self.default_curve
        resp = self._http_request("POST", "/api/v1/keygen", {
            "curve": c,
            "pk": pk,
            "msk": msk,
            "attributes": attributes,
        })
        return resp["sk"]

    def create_export_package(
        self,
        pk: str,
        payload: bytes,
        policy: str,
        tenant_id: str,
        epoch_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        curve: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Đóng gói hồ sơ y tế / tệp chia sẻ liên viện thành gói xuất chuẩn Profile P2.
        Sử dụng cơ chế KEM (CP-ABE đóng gói wrap_key) + DEM (AES-256-GCM bọc share_DEK và payload).
        """
        c = curve or self.default_curve
        payload_b64 = base64.b64encode(payload).decode("ascii")
        resp = self._http_request("POST", "/api/v1/export/package", {
            "curve": c,
            "pk": pk,
            "payload_b64": payload_b64,
            "policy": policy,
            "tenant_id": tenant_id,
            "epoch_id": epoch_id,
            "metadata": metadata or {},
        })
        return resp["package"]

    def decrypt_export_package(
        self,
        pk: str,
        package: Dict[str, Any],
        user_key: str,
        curve: Optional[str] = None,
    ) -> bytes:
        """
        Giải mã gói chia sẻ Profile P2 bằng khóa thuộc tính của người nhận.
        Trả về plaintext bytes nếu thỏa mãn chính sách và toàn vẹn dữ liệu.
        Tung lỗi PolicyNotSatisfiedError nếu thiếu thuộc tính.
        """
        c = curve or self.default_curve
        resp = self._http_request("POST", "/api/v1/export/decrypt", {
            "curve": c,
            "pk": pk,
            "package": package,
            "sk": user_key,
        })
        return base64.b64decode(resp["payload_b64"].encode("ascii"))

    def test_collusion_resistance(
        self,
        pk: str,
        msk: str,
        policy: str,
        u1_attrs: List[str],
        u2_attrs: List[str],
        u3_authorized_attrs: List[str],
        curve: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Thực hiện kiểm thử đối kháng chống thông đồng (Collusion Resistance - TC-12).
        Chứng minh rằng việc ghép các thành phần khóa của U1 và U2 không thể giải mã được bản mã.
        """
        c = curve or self.default_curve
        resp = self._http_request("POST", "/api/v1/collusion/test", {
            "curve": c,
            "pk": pk,
            "msk": msk,
            "policy": policy,
            "u1_attrs": u1_attrs,
            "u2_attrs": u2_attrs,
            "u3_authorized_attrs": u3_authorized_attrs,
        })
        res = resp["result"]
        if not res["collusion_resistance_verified"]:
            raise CollusionVulnerabilityError("CP-ABE Collusion Resistance check failed: forged key was able to decrypt!")
        return res

    def run_benchmark(
        self,
        curves: List[str] = ("BN254", "SS512"),
        leaves: List[int] = (2, 4, 8, 16),
        iterations: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Chạy benchmark E4 toàn diện qua container CLI.
        """
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        abe_dir = os.path.join(repo_root, "workers/abe")
        curves_str = ",".join(curves)
        leaves_str = ",".join(str(k) for k in leaves)

        cmd = [
            "docker", "run", "--rm",
            "-v", f"{abe_dir}:/app",
            "medshare-abe-worker:latest",
            "python3", "/app/cli.py", "benchmark",
            "--curves", curves_str,
            "--leaves", leaves_str,
            "--iterations", str(iterations)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        return data["benchmark_results"]
