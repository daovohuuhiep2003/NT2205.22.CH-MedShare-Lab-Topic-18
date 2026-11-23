#!/usr/bin/env python3
"""
Smoke test for Post-Quantum Cryptography (PQC) Worker
Topic 18 - NT2205.11.CH (MedShare-Lab)
Gate Tuần 2 Requirement:
1. FIPS 203: ML-KEM-768 (Profile P4 - Long-term key archive / KEM-DEM)
   - Positive Test: Encapsulation & Decapsulation khớp 100% Shared Secret.
   - Negative Test: Tampered Ciphertext / Wrong Secret Key bị từ chối (Shared Secret không khớp).
2. FIPS 204: ML-DSA-65 (Audit Log Integrity / Policy Manifest Signature)
   - Positive Test: Ký số Policy bundle & Xác thực hợp lệ (True).
   - Negative Test: Payload hoặc chữ ký bị tamper bị từ chối dứt khoát (False).
"""
import sys

def run_pqc_smoke_test():
    print("=================================================================")
    print("   MEDSHARE-LAB: PQC WORKER SMOKE TEST (FIPS 203 & FIPS 204)")
    print("=================================================================")

    try:
        import oqs
    except ImportError as e:
        print(f"[LỖI] Không thể import thư viện oqs (liboqs-python): {e}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # 1. KIỂM THỬ FIPS 203: ML-KEM-768 (Đóng gói khóa / KEM)
    # --------------------------------------------------------------------------
    kem_alg = "ML-KEM-768"
    enabled_kems = oqs.get_enabled_kem_mechanisms()
    if kem_alg not in enabled_kems:
        if "Kyber768" in enabled_kems:
            kem_alg = "Kyber768"
        else:
            print(f"[LỖI] Không tìm thấy cơ chế {kem_alg} trong liboqs!")
            sys.exit(1)

    print(f"\n[+] Khởi tạo KEM Worker: {kem_alg} (FIPS 203)...")
    with oqs.KeyEncapsulation(kem_alg) as receiver:
        receiver_pubkey = receiver.generate_keypair()
        print(f"    - Public Key size: {len(receiver_pubkey)} bytes")

        # Sender đóng gói shared secret (dùng làm DEK trong KEM/DEM)
        with oqs.KeyEncapsulation(kem_alg) as sender:
            ciphertext, shared_secret_sender = sender.encap_secret(receiver_pubkey)
            print(f"    - Ciphertext capsule size: {len(ciphertext)} bytes")
            print(f"    - Shared Secret (DEK) size: {len(shared_secret_sender)} bytes")

        # 1.1 Positive Test: Receiver giải bọc capsule
        shared_secret_receiver = receiver.decap_secret(ciphertext)
        if shared_secret_receiver == shared_secret_sender:
            print("    --> [PASS] Positive Test: ML-KEM-768 giải bọc thành công, shared secret khớp tuyệt đối!")
        else:
            print("    --> [FAIL] Positive Test: Shared secret không khớp!")
            sys.exit(1)

        # 1.2 Negative Test 1: Tamper ciphertext (đối thủ thay đổi 1 byte trên đường truyền)
        tampered_ciphertext = bytearray(ciphertext)
        tampered_ciphertext[0] ^= 0xFF
        tampered_secret = receiver.decap_secret(bytes(tampered_ciphertext))
        if tampered_secret != shared_secret_sender:
            print("    --> [PASS] Negative Test 1: Ciphertext bị sửa đổi sinh ra secret sai lệch (Kháng tấn công giả mạo)!")
        else:
            print("    --> [FAIL] Negative Test 1: Tampered ciphertext vẫn cho ra cùng secret!")
            sys.exit(1)

        # 1.3 Negative Test 2: Receiver khác (khóa khác) cố giải bọc
        with oqs.KeyEncapsulation(kem_alg) as attacker:
            attacker.generate_keypair()
            attacker_secret = attacker.decap_secret(ciphertext)
            if attacker_secret != shared_secret_sender:
                print("    --> [PASS] Negative Test 2: Kẻ tấn công dùng sai private key không thể giải mã secret!")
            else:
                print("    --> [FAIL] Negative Test 2: Sai private key nhưng vẫn giải được secret!")
                sys.exit(1)

    # --------------------------------------------------------------------------
    # 2. KIỂM THỬ FIPS 204: ML-DSA-65 (Chữ ký số toàn vẹn)
    # --------------------------------------------------------------------------
    sig_alg = "ML-DSA-65"
    enabled_sigs = oqs.get_enabled_sig_mechanisms()
    if sig_alg not in enabled_sigs:
        if "Dilithium3" in enabled_sigs:
            sig_alg = "Dilithium3"
        else:
            print(f"[LỖI] Không tìm thấy cơ chế {sig_alg} trong liboqs!")
            sys.exit(1)

    print(f"\n[+] Khởi tạo Signature Worker: {sig_alg} (FIPS 204)...")
    with oqs.Signature(sig_alg) as signer:
        signer_pubkey = signer.generate_keypair()
        print(f"    - Public Key size: {len(signer_pubkey)} bytes")

        manifest_payload = b"MEDSHARE_AUDIT_CHECKPOINT:epoch=42:tenant=hospital_a:merkle_root=3f8a9c2b"
        signature = signer.sign(manifest_payload)
        print(f"    - Signature size: {len(signature)} bytes")

        with oqs.Signature(sig_alg) as verifier:
            # 2.1 Positive Test: Xác thực chữ ký hợp lệ
            is_valid = verifier.verify(manifest_payload, signature, signer_pubkey)
            if is_valid:
                print("    --> [PASS] Positive Test: Chữ ký ML-DSA-65 xác thực thành công!")
            else:
                print("    --> [FAIL] Positive Test: Chữ ký hợp lệ bị từ chối!")
                sys.exit(1)

            # 2.2 Negative Test 1: Giả mạo dữ liệu kiểm toán (Tampered manifest)
            tampered_payload = b"MEDSHARE_AUDIT_CHECKPOINT:epoch=42:tenant=hospital_b:merkle_root=HACKED!!"
            is_valid_tampered = verifier.verify(tampered_payload, signature, signer_pubkey)
            if not is_valid_tampered:
                print("    --> [PASS] Negative Test 1: Phát hiện và từ chối dữ liệu bị giả mạo!")
            else:
                print("    --> [FAIL] Negative Test 1: Chấp nhận dữ liệu kiểm toán đã bị sửa đổi!")
                sys.exit(1)

            # 2.3 Negative Test 2: Giả mạo byte chữ ký
            tampered_signature = bytearray(signature)
            tampered_signature[0] ^= 0xFF
            is_valid_sig = verifier.verify(manifest_payload, bytes(tampered_signature), signer_pubkey)
            if not is_valid_sig:
                print("    --> [PASS] Negative Test 2: Phát hiện và từ chối chữ ký số bị sai lệch!")
            else:
                print("    --> [FAIL] Negative Test 2: Chấp nhận chữ ký số bị hỏng!")
                sys.exit(1)

    print("\n=================================================================")
    print("   [OK] PQC WORKER SMOKE TESTS: 100% PASSED (FIPS 203 & 204)!")
    print("=================================================================")

if __name__ == '__main__':
    run_pqc_smoke_test()
