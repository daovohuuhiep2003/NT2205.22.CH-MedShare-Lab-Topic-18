#include <iostream>
#include <vector>
#include <cassert>
#include "seal/seal.h"

using namespace std;
using namespace seal;

int main() {
    cout << "=================================================================" << endl;
    cout << "   MEDSHARE-LAB: HOMOMORPHIC ENCRYPTION WORKER (SEAL BFV)" << endl;
    cout << "=================================================================" << endl;

    // 1. Cấu hình tham số mã hóa BFV theo thiết kế đề tài
    EncryptionParameters parms(scheme_type::bfv);
    size_t poly_modulus_degree = 8192;
    parms.set_poly_modulus_degree(poly_modulus_degree);
    parms.set_coeff_modulus(CoeffModulus::BFVDefault(poly_modulus_degree));
    parms.set_plain_modulus(PlainModulus::Batching(poly_modulus_degree, 20));

    SEALContext context(parms);
    if (!context.parameters_set()) {
        cerr << "[LỖI] Tham số BFV không hợp lệ!" << endl;
        return 1;
    }
    cout << "[+] SEALContext khởi tạo thành công với BFV (N=8192, 128-bit security)." << endl;

    // 2. Sinh khóa cho Data Owner
    KeyGenerator keygen(context);
    SecretKey secret_key = keygen.secret_key();
    PublicKey public_key;
    keygen.create_public_key(public_key);
    RelinKeys relin_keys;
    keygen.create_relin_keys(relin_keys);

    Encryptor encryptor(context, public_key);
    Evaluator evaluator(context);
    Decryptor decryptor(context, secret_key);
    BatchEncoder batch_encoder(context);

    // 3. Chuẩn bị mảng dữ liệu y tế (amount_units: chi phí điều trị)
    // Giả lập 4 khoản thanh toán của bệnh nhân
    int64_t val1 = 150;
    int64_t val2 = 350;
    int64_t val3 = 500;
    int64_t val4 = 1000;
    int64_t expected_sum = val1 + val2 + val3 + val4; // 2000

    Plaintext plain1, plain2, plain3, plain4;
    vector<int64_t> pod1(batch_encoder.slot_count(), 0);
    vector<int64_t> pod2(batch_encoder.slot_count(), 0);
    vector<int64_t> pod3(batch_encoder.slot_count(), 0);
    vector<int64_t> pod4(batch_encoder.slot_count(), 0);
    pod1[0] = val1; pod2[0] = val2; pod3[0] = val3; pod4[0] = val4;

    batch_encoder.encode(pod1, plain1);
    batch_encoder.encode(pod2, plain2);
    batch_encoder.encode(pod3, plain3);
    batch_encoder.encode(pod4, plain4);

    Ciphertext ct1, ct2, ct3, ct4;
    encryptor.encrypt(plain1, ct1);
    encryptor.encrypt(plain2, ct2);
    encryptor.encrypt(plain3, ct3);
    encryptor.encrypt(plain4, ct4);

    cout << "\n[+] Data Owner đã mã hóa 4 giá trị thành BFV ciphertexts:" << endl;
    cout << "    Val1=" << val1 << ", Val2=" << val2 << ", Val3=" << val3 << ", Val4=" << val4 << endl;

    // 4. Máy chủ Cloud (Untrusted Z2) thực hiện tính toán trên Ciphertext
    cout << "\n[+] Untrusted Cloud Worker thực thi phép cộng đồng cấu (SUM) trên Ciphertext..." << endl;
    Ciphertext ct_sum;
    evaluator.add(ct1, ct2, ct_sum);
    evaluator.add_inplace(ct_sum, ct3);
    evaluator.add_inplace(ct_sum, ct4);

    int noise_budget = decryptor.invariant_noise_budget(ct_sum);
    cout << "    - Noise budget còn lại sau phép cộng SUM: " << noise_budget << " bits" << endl;

    // 5. TEST 1 (POSITIVE): Data Owner giải mã kết quả trả về từ Cloud
    Plaintext plain_sum;
    decryptor.decrypt(ct_sum, plain_sum);
    vector<int64_t> result_pod;
    batch_encoder.decode(plain_sum, result_pod);
    int64_t actual_sum = result_pod[0];

    cout << "\n[*] [TEST 1 - POSITIVE] Data Owner giải mã kết quả tính toán SUM từ Cloud:" << endl;
    cout << "    Kỳ vọng: " << expected_sum << " | Thực tế: " << actual_sum << endl;
    if (actual_sum == expected_sum) {
        cout << "    --> [PASS] Positive Test: Phép cộng đồng cấu BFV chính xác 100% (Integer Exactness)!" << endl;
    } else {
        cerr << "    --> [FAIL] Positive Test: Kết quả giải mã sai lệch!" << endl;
        return 1;
    }

    // 6. TEST 2 (NEGATIVE - Confidentiality): Kẻ tấn công dùng sai Secret Key
    cout << "\n[*] [TEST 2 - NEGATIVE] Đối thủ (sai Secret Key) cố gắng giải mã Ciphertext kết quả:" << endl;
    KeyGenerator attacker_keygen(context);
    SecretKey attacker_sk = attacker_keygen.secret_key();
    Decryptor attacker_decryptor(context, attacker_sk);

    Plaintext attacker_plain;
    attacker_decryptor.decrypt(ct_sum, attacker_plain);
    vector<int64_t> attacker_pod;
    batch_encoder.decode(attacker_plain, attacker_pod);
    int64_t attacker_res = attacker_pod[0];

    cout << "    Kết quả giải mã của đối thủ: " << attacker_res << " (Khác expected: " << expected_sum << ")" << endl;
    if (attacker_res != expected_sum) {
        cout << "    --> [PASS] Negative Test: Kẻ tấn công không có Secret Key không thể đọc được plaintext!" << endl;
    } else {
        cerr << "    --> [FAIL] Negative Test: Kẻ tấn công giải mã thành công dù không có khóa hợp lệ!" << endl;
        return 1;
    }

    cout << "\n=================================================================" << endl;
    cout << "   [OK] HE (SEAL BFV) WORKER SMOKE TESTS: 100% PASSED!" << endl;
    cout << "=================================================================" << endl;
    return 0;
}
