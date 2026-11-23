#!/usr/bin/env python3
"""
Smoke test for CP-ABE Worker (AC17 scheme on SS512 curve)
Tuần 2 Feasibility Spike - Gate Tuần 2 Requirement:
- 1 Positive test: Thuộc tính thỏa mãn Policy -> Giải mã thành công và khớp chính xác.
- 1 Negative test: Thuộc tính KHÔNG thỏa mãn Policy -> Từ chối giải mã, trả về False / không khớp.
"""
import sys

def run_smoke_test():
    print("=================================================================")
    print("   MEDSHARE-LAB: CP-ABE WORKER SMOKE TEST (CHARM-CRYPTO)")
    print("=================================================================")
    
    try:
        from charm.toolbox.pairinggroup import PairingGroup, GT
        from charm.schemes.abenc.ac17 import AC17CPABE
    except ImportError as e:
        print(f"[LỖI] Không thể import thư viện Charm-Crypto: {e}")
        sys.exit(1)

    print("[+] Khởi tạo PairingGroup('SS512')...")
    group = PairingGroup('SS512')
    cpabe = AC17CPABE(group, 2)

    print("[+] Sinh cặp khóa thẩm quyền Master (MPK, MSK)...")
    (pk, msk) = cpabe.setup()

    # Chính sách kiểm soát truy cập hồ sơ bệnh án
    policy = "((DOCTOR and CARDIOLOGY) or CHIEF_OF_MEDICINE)"
    secret_key_msg = group.random(GT)

    print(f"[+] Mã hóa khóa bí mật với Policy: '{policy}'...")
    ciphertext = cpabe.encrypt(pk, secret_key_msg, policy)

    # --------------------------------------------------------------------------
    # 1. POSITIVE TEST: User 1 thỏa mãn chính sách (DOCTOR và CARDIOLOGY)
    # --------------------------------------------------------------------------
    user1_attrs = ['DOCTOR', 'CARDIOLOGY', 'TENANT_HOSPITAL_A']
    print(f"\n[*] [TEST 1 - POSITIVE] Cấp khóa cho Bác sĩ Tim mạch với attributes: {user1_attrs}")
    key_user1 = cpabe.keygen(pk, msk, user1_attrs)
    
    decrypted_msg1 = cpabe.decrypt(pk, ciphertext, key_user1)
    if decrypted_msg1 == secret_key_msg:
        print("    --> [PASS] Positive Test: Giải mã thành công, khóa bí mật khớp 100%!")
    else:
        print("    --> [FAIL] Positive Test: Giải mã thất bại dù thuộc tính hợp lệ!")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # 2. NEGATIVE TEST: User 2 thiếu thuộc tính (NURSE, CARDIOLOGY - thiếu DOCTOR)
    # --------------------------------------------------------------------------
    user2_attrs = ['NURSE', 'CARDIOLOGY', 'TENANT_HOSPITAL_A']
    print(f"\n[*] [TEST 2 - NEGATIVE] Cấp khóa cho Điều dưỡng với attributes: {user2_attrs}")
    key_user2 = cpabe.keygen(pk, msk, user2_attrs)
    
    decrypted_msg2 = cpabe.decrypt(pk, ciphertext, key_user2)
    if decrypted_msg2 != secret_key_msg:
        print("    --> [PASS] Negative Test: Từ chối giải mã thành công (không thỏa policy)!")
    else:
        print("    --> [FAIL] Negative Test: Người dùng không đủ quyền vẫn giải mã được!")
        sys.exit(1)

    print("\n=================================================================")
    print("   [OK] CP-ABE WORKER SMOKE TESTS: 100% PASSED!")
    print("=================================================================")

if __name__ == '__main__':
    run_smoke_test()
