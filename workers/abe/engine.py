"""
MedShare-Lab (Topic 18 — NT2205.11.CH)
Lõi Mật mã CP-ABE (Ciphertext-Policy Attribute-Based Encryption)
Hiện thực hóa Scheme AC17 (Pairing-Based Cryptography) kết hợp AEAD (AES-256-GCM + HKDF)
Hỗ trợ Profile P2 (Fine-Grained Sharing Capsule & Inter-Hospital Export Package).
"""

import base64
import hashlib
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from charm.core.engine.util import bytesToObject, objectToBytes
from charm.schemes.abenc.ac17 import AC17CPABE
from charm.toolbox.pairinggroup import GT, PairingGroup
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class CpAbeEngine:
    """
    Lõi thực thi mật mã CP-ABE trên nền Charm-Crypto.
    Hỗ trợ cả đường cong BN254 (128-bit security) và SS512 (Research Prototype ~80-bit).
    """

    def __init__(self, curve: str = "BN254"):
        self.curve_name = curve
        self.group = PairingGroup(curve)
        # AC17CPABE với secLevel=2
        self.cpabe = AC17CPABE(self.group, 2)

    @property
    def security_level_notes(self) -> str:
        if self.curve_name.upper() == "SS512":
            return "SS512 curve provides ~80-bit security (Research Demonstration Only; NIST deprecation notice)"
        elif self.curve_name.upper() == "BN254":
            return "BN254 curve provides 128-bit security (Type-3 Asymmetric Pairing; Recommended for production)"
        else:
            return f"Custom pairing curve {self.curve_name}"

    # -------------------------------------------------------------------------
    # 1. Authority Setup & Key Issuance
    # -------------------------------------------------------------------------

    def setup(self) -> Tuple[str, str, Dict[str, Any]]:
        """
        Sinh cặp khóa thẩm quyền Master (MPK, MSK).
        Trả về: (pk_b64, msk_b64, public_descriptor)
        """
        pk, msk = self.cpabe.setup()
        pk_b64 = base64.b64encode(objectToBytes(pk, self.group)).decode("ascii")
        msk_b64 = base64.b64encode(objectToBytes(msk, self.group)).decode("ascii")

        descriptor = {
            "curve": self.curve_name,
            "scheme": "AC17-CPABE",
            "security_notes": self.security_level_notes,
            "created_at": time.time(),
        }
        return pk_b64, msk_b64, descriptor

    def keygen(self, pk_b64: str, msk_b64: str, attributes: List[str]) -> str:
        """
        Cấp phát khóa bí mật thuộc tính SK cho một người dùng cụ thể.
        Mỗi khóa được gắn một số ngẫu nhiên bí mật riêng của người dùng để chống thông đồng.
        """
        pk = bytesToObject(base64.b64decode(pk_b64.encode("ascii")), self.group)
        msk = bytesToObject(base64.b64decode(msk_b64.encode("ascii")), self.group)
        # Chuẩn hóa thuộc tính: chữ in hoa, bỏ khoảng trắng thừa
        norm_attrs = [attr.strip().upper() for attr in attributes]
        sk = self.cpabe.keygen(pk, msk, norm_attrs)
        sk_b64 = base64.b64encode(objectToBytes(sk, self.group)).decode("ascii")
        return sk_b64

    # -------------------------------------------------------------------------
    # 2. Key Encapsulation Mechanism (KEM)
    # -------------------------------------------------------------------------

    def kem_encapsulate(
        self,
        pk_b64: str,
        policy: str,
        tenant_id: str,
        epoch_id: str,
    ) -> Tuple[bytes, str]:
        """
        Đóng gói khóa chia sẻ:
        1. Sinh ngẫu nhiên phần tử Z in GT
        2. Mã hóa Z bằng CP-ABE dưới chính sách policy
        3. Dẫn xuất wrap_key 256-bit từ Z qua HKDF-SHA-256 gắn ngữ cảnh (tenant, epoch, policy_hash)
        Trả về: (wrap_key_32bytes, kem_ciphertext_b64)
        """
        pk = bytesToObject(base64.b64decode(pk_b64.encode("ascii")), self.group)
        # Chọn bí mật ngẫu nhiên trong nhóm GT
        secret_z = self.group.random(GT)
        kem_ct = self.cpabe.encrypt(pk, secret_z, policy)
        kem_ct_b64 = base64.b64encode(objectToBytes(kem_ct, self.group)).decode("ascii")

        # Chuẩn hóa canonical serialization của secret_z
        z_bytes = objectToBytes(secret_z, self.group)
        policy_hash = hashlib.sha256(policy.encode("utf-8")).hexdigest()

        # Dẫn xuất khóa bao gói bằng HKDF-SHA-256
        hkdf_info = f"medshare-p2-kem|{tenant_id}|{epoch_id}|{policy_hash}".encode("utf-8")
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=hkdf_info,
        )
        wrap_key = hkdf.derive(z_bytes)
        return wrap_key, kem_ct_b64

    def kem_decapsulate(
        self,
        pk_b64: str,
        kem_ct_b64: str,
        sk_b64: str,
        tenant_id: str,
        epoch_id: str,
        policy: str,
    ) -> bytes:
        """
        Mở gói khóa chia sẻ:
        1. Giải mã CP-ABE ciphertext bằng khóa thuộc tính của người nhận
        2. Khôi phục phần tử nhóm Z in GT
        3. Dẫn xuất lại wrap_key bằng HKDF-SHA-256
        Nếu người nhận không thỏa chính sách hoặc khóa không hợp lệ, tung ngoại lệ từ chối.
        """
        pk = bytesToObject(base64.b64decode(pk_b64.encode("ascii")), self.group)
        kem_ct = bytesToObject(base64.b64decode(kem_ct_b64.encode("ascii")), self.group)
        sk = bytesToObject(base64.b64decode(sk_b64.encode("ascii")), self.group)

        try:
            recovered_z = self.cpabe.decrypt(pk, kem_ct, sk)
        except Exception as e:
            raise ValueError(f"CP-ABE decryption failed: {e}")

        if not recovered_z:
            raise PermissionError("Policy not satisfied: user attributes do not satisfy the access policy.")

        z_bytes = objectToBytes(recovered_z, self.group)
        policy_hash = hashlib.sha256(policy.encode("utf-8")).hexdigest()

        hkdf_info = f"medshare-p2-kem|{tenant_id}|{epoch_id}|{policy_hash}".encode("utf-8")
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=hkdf_info,
        )
        wrap_key = hkdf.derive(z_bytes)
        return wrap_key

    # -------------------------------------------------------------------------
    # 3. Full Profile P2 Export Package (KEM/DEM Hybrid Encryption)
    # -------------------------------------------------------------------------

    def create_export_package(
        self,
        pk_b64: str,
        payload: bytes,
        policy: str,
        tenant_id: str,
        epoch_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Tạo gói xuất chia sẻ dữ liệu liên viện (Profile P2):
        1. Sinh fresh share_DEK 32 bytes ngẫu nhiên qua CSPRNG.
        2. Mã hóa payload dữ liệu lớn bằng share_DEK (AES-256-GCM + AAD).
        3. Dùng KEM đóng gói share_DEK bằng wrap_key (AES-256-GCM).
        4. Gói ghém manifest chứa mã băm, chính sách, epoch, tenant context.
        """
        export_id = f"EXP-{int(time.time()*1000)}-{os.urandom(4).hex()}"
        meta = metadata or {}
        policy_hash = hashlib.sha256(policy.encode("utf-8")).hexdigest()
        payload_hash = hashlib.sha256(payload).hexdigest()

        # 1. KEM: Sinh wrap_key và kem_ciphertext
        wrap_key, kem_ct_b64 = self.kem_encapsulate(
            pk_b64=pk_b64,
            policy=policy,
            tenant_id=tenant_id,
            epoch_id=epoch_id,
        )

        # 2. DEM Part 1: Bọc share_DEK bằng wrap_key
        share_dek = os.urandom(32)
        wrap_nonce = os.urandom(12)
        wrap_aad = json.dumps({
            "export_id": export_id,
            "tenant_id": tenant_id,
            "epoch_id": epoch_id,
            "policy_hash": policy_hash,
            "type": "share_dek_capsule",
        }, sort_keys=True).encode("utf-8")

        aesgcm_wrap = AESGCM(wrap_key)
        wrapped_dek_bytes = aesgcm_wrap.encrypt(wrap_nonce, share_dek, wrap_aad)
        wrapped_dek_b64 = base64.b64encode(wrap_nonce + wrapped_dek_bytes).decode("ascii")

        # 3. DEM Part 2: Mã hóa bulk payload bằng share_DEK
        payload_nonce = os.urandom(12)
        payload_aad = json.dumps({
            "export_id": export_id,
            "tenant_id": tenant_id,
            "epoch_id": epoch_id,
            "payload_hash": payload_hash,
            "type": "medical_export_payload",
        }, sort_keys=True).encode("utf-8")

        aesgcm_payload = AESGCM(share_dek)
        encrypted_payload_bytes = aesgcm_payload.encrypt(payload_nonce, payload, payload_aad)
        encrypted_payload_b64 = base64.b64encode(payload_nonce + encrypted_payload_bytes).decode("ascii")

        package = {
            "format_version": "P2-CPABE-1.0",
            "export_id": export_id,
            "tenant_id": tenant_id,
            "epoch_id": epoch_id,
            "policy": policy,
            "policy_hash": policy_hash,
            "payload_hash": payload_hash,
            "kem_ciphertext": kem_ct_b64,
            "wrapped_share_dek": wrapped_dek_b64,
            "encrypted_payload": encrypted_payload_b64,
            "metadata": meta,
            "crypto_profile": f"AC17-{self.curve_name}-AES256GCM",
            "created_at": time.time(),
        }
        return package

    def decrypt_export_package(
        self,
        pk_b64: str,
        package: Dict[str, Any],
        sk_b64: str,
    ) -> bytes:
        """
        Giải mã gói xuất chia sẻ dữ liệu liên viện (Profile P2):
        1. Giải mã KEM ciphertext -> wrap_key
        2. Mở bọc share_DEK qua AES-256-GCM (kiểm tra toàn vẹn wrap_aad)
        3. Giải mã bulk payload qua share_DEK (kiểm tra toàn vẹn payload_aad và payload_hash)
        """
        export_id = package["export_id"]
        tenant_id = package["tenant_id"]
        epoch_id = package["epoch_id"]
        policy = package["policy"]
        policy_hash = package["policy_hash"]
        kem_ct_b64 = package["kem_ciphertext"]
        wrapped_dek_b64 = package["wrapped_share_dek"]
        encrypted_payload_b64 = package["encrypted_payload"]

        # 1. Thu hồi wrap_key qua KEM
        wrap_key = self.kem_decapsulate(
            pk_b64=pk_b64,
            kem_ct_b64=kem_ct_b64,
            sk_b64=sk_b64,
            tenant_id=tenant_id,
            epoch_id=epoch_id,
            policy=policy,
        )

        # 2. Giải mã share_DEK
        wrapped_dek_raw = base64.b64decode(wrapped_dek_b64.encode("ascii"))
        wrap_nonce = wrapped_dek_raw[:12]
        wrapped_dek_bytes = wrapped_dek_raw[12:]
        wrap_aad = json.dumps({
            "export_id": export_id,
            "tenant_id": tenant_id,
            "epoch_id": epoch_id,
            "policy_hash": policy_hash,
            "type": "share_dek_capsule",
        }, sort_keys=True).encode("utf-8")

        aesgcm_wrap = AESGCM(wrap_key)
        try:
            share_dek = aesgcm_wrap.decrypt(wrap_nonce, wrapped_dek_bytes, wrap_aad)
        except Exception as e:
            raise ValueError(f"Share DEK AEAD decryption / integrity verification failed: {e}")

        # 3. Giải mã Payload
        encrypted_payload_raw = base64.b64decode(encrypted_payload_b64.encode("ascii"))
        payload_nonce = encrypted_payload_raw[:12]
        payload_ciphertext = encrypted_payload_raw[12:]
        payload_aad = json.dumps({
            "export_id": export_id,
            "tenant_id": tenant_id,
            "epoch_id": epoch_id,
            "payload_hash": package["payload_hash"],
            "type": "medical_export_payload",
        }, sort_keys=True).encode("utf-8")

        aesgcm_payload = AESGCM(share_dek)
        try:
            payload = aesgcm_payload.decrypt(payload_nonce, payload_ciphertext, payload_aad)
        except Exception as e:
            raise ValueError(f"Payload AEAD decryption / integrity verification failed: {e}")

        # Kiểm tra tính khớp của digest
        computed_hash = hashlib.sha256(payload).hexdigest()
        if computed_hash != package["payload_hash"]:
            raise ValueError("Payload hash mismatch: decrypted content does not match manifest digest.")

        return payload

    # -------------------------------------------------------------------------
    # 4. Collusion Resistance Testing (TC-12)
    # -------------------------------------------------------------------------

    def test_collusion(
        self,
        pk_b64: str,
        msk_b64: str,
        policy: str,
        u1_attrs: List[str],
        u2_attrs: List[str],
        u3_authorized_attrs: List[str],
    ) -> Dict[str, Any]:
        """
        Thực hiện kiểm thử đối kháng chống thông đồng (Collusion Resistance Test - TC-12).
        Kịch bản:
        - Chính sách đòi hỏi thuộc tính giao nhau (ví dụ: DOCTOR and CARDIOLOGY)
        - U1 chỉ có DOCTOR (thiếu CARDIOLOGY)
        - U2 chỉ có CARDIOLOGY (thiếu DOCTOR)
        - U3 có cả DOCTOR and CARDIOLOGY (Positive Control)
        - Đối thủ cố gắng trộn thành phần khóa của U1 và U2 để tạo thành forged key có đủ thuộc tính.
        Kiểm chứng:
        - Thuật toán giải mã bắt buộc phải từ chối (hoặc tung lỗi authentication tag/invalid ciphertext).
        - U1 đơn lẻ: Thất bại.
        - U2 đơn lẻ: Thất bại.
        - Forged colluded key: Thất bại.
        - U3 (hợp lệ): Thành công 100%.
        """
        pk = bytesToObject(base64.b64decode(pk_b64.encode("ascii")), self.group)
        msk = bytesToObject(base64.b64decode(msk_b64.encode("ascii")), self.group)

        # Sinh bí mật ngẫu nhiên để mã hóa
        test_msg = self.group.random(GT)
        ct = self.cpabe.encrypt(pk, test_msg, policy)

        # Cấp khóa cho U1, U2, U3
        key_u1 = self.cpabe.keygen(pk, msk, [a.strip().upper() for a in u1_attrs])
        key_u2 = self.cpabe.keygen(pk, msk, [a.strip().upper() for a in u2_attrs])
        key_u3 = self.cpabe.keygen(pk, msk, [a.strip().upper() for a in u3_authorized_attrs])

        # 1. Test U1 độc lập
        dec_u1 = self.cpabe.decrypt(pk, ct, key_u1)
        u1_pass = (dec_u1 == test_msg)

        # 2. Test U2 độc lập
        dec_u2 = self.cpabe.decrypt(pk, ct, key_u2)
        u2_pass = (dec_u2 == test_msg)

        # 3. Test U3 hợp lệ (Positive Control)
        dec_u3 = self.cpabe.decrypt(pk, ct, key_u3)
        u3_pass = (dec_u3 == test_msg)

        # 4. Thử nghiệm trộn thành phần khóa (Collusion Attack)
        def clone(obj):
            return bytesToObject(objectToBytes(obj, self.group), self.group)

        # Strategy 1: Nền U1, mượn thành phần thuộc tính từ U2
        colluded_key_1 = clone(key_u1)
        union_attrs = list(set([a.strip().upper() for a in u1_attrs] + [a.strip().upper() for a in u2_attrs]))
        colluded_key_1["attr_list"] = union_attrs
        for attr, comp in key_u2.get("K", {}).items():
            if attr not in colluded_key_1.get("K", {}):
                colluded_key_1["K"][attr] = clone(comp)

        collusion_1_success = False
        collusion_1_error = None
        try:
            res_c1 = self.cpabe.decrypt(pk, ct, colluded_key_1)
            collusion_1_success = (res_c1 == test_msg)
        except Exception as e:
            collusion_1_error = str(e)

        # Strategy 2: Nền U2, mượn thành phần thuộc tính từ U1
        colluded_key_2 = clone(key_u2)
        colluded_key_2["attr_list"] = union_attrs
        for attr, comp in key_u1.get("K", {}).items():
            if attr not in colluded_key_2.get("K", {}):
                colluded_key_2["K"][attr] = clone(comp)

        collusion_2_success = False
        collusion_2_error = None
        try:
            res_c2 = self.cpabe.decrypt(pk, ct, colluded_key_2)
            collusion_2_success = (res_c2 == test_msg)
        except Exception as e:
            collusion_2_error = str(e)

        collusion_resisted = (not collusion_1_success) and (not collusion_2_success)

        return {
            "policy": policy,
            "curve": self.curve_name,
            "u1_alone_decrypt": u1_pass,
            "u2_alone_decrypt": u2_pass,
            "u3_authorized_decrypt": u3_pass,
            "collusion_strategy_1_success": collusion_1_success,
            "collusion_strategy_1_error": collusion_1_error,
            "collusion_strategy_2_success": collusion_2_success,
            "collusion_strategy_2_error": collusion_2_error,
            "collusion_resistance_verified": collusion_resisted and u3_pass and (not u1_pass) and (not u2_pass),
        }

