#include <iostream>
#include <vector>
#include <chrono>
#include <numeric>
#include <random>
#include <sstream>
#include <iomanip>
#include <cstdint>
#include <cstring>
#include "seal/seal.h"

using namespace std;
using namespace seal;

// Helper to serialize SEAL objects and measure byte length
template <typename T>
size_t get_serialized_size(const T &obj) {
    stringstream ss;
    obj.save(ss);
    return ss.str().size();
}

struct BenchmarkResult {
    size_t cohort_size;
    int64_t expected_sum;
    int64_t actual_sum;
    bool exact_match;
    int noise_budget_remaining;
    double keygen_ms;
    double encode_ms;
    double encrypt_ms;
    double eval_add_ms;
    double decrypt_ms;
    double decode_ms;
    double total_e2e_ms;
    size_t public_key_bytes;
    size_t secret_key_bytes;
    size_t relin_keys_bytes;
    size_t ciphertext_bytes;
    size_t total_ciphertext_bytes;
    double expansion_ratio;
};

class BFVEngine {
public:
    size_t poly_modulus_degree;
    int plain_modulus_bits;
    SEALContext context;
    KeyGenerator keygen;
    SecretKey secret_key;
    PublicKey public_key;
    RelinKeys relin_keys;
    Encryptor encryptor;
    Evaluator evaluator;
    Decryptor decryptor;
    BatchEncoder batch_encoder;

    BFVEngine(size_t poly_degree = 8192, int plain_bits = 30)
        : poly_modulus_degree(poly_degree),
          plain_modulus_bits(plain_bits),
          context(create_context(poly_degree, plain_bits)),
          keygen(context),
          secret_key(keygen.secret_key()),
          encryptor(context, (keygen.create_public_key(public_key), public_key)),
          evaluator(context),
          decryptor(context, secret_key),
          batch_encoder(context) {
        keygen.create_relin_keys(relin_keys);
    }

    static SEALContext create_context(size_t poly_degree, int plain_bits) {
        EncryptionParameters parms(scheme_type::bfv);
        parms.set_poly_modulus_degree(poly_degree);
        parms.set_coeff_modulus(CoeffModulus::BFVDefault(poly_degree));
        parms.set_plain_modulus(PlainModulus::Batching(poly_degree, plain_bits));
        SEALContext ctx(parms);
        if (!ctx.parameters_set()) {
            throw runtime_error("Invalid BFV encryption parameters!");
        }
        return ctx;
    }

    // Benchmark multi-record summation
    BenchmarkResult run_aggregation_benchmark(const vector<int64_t> &costs) {
        BenchmarkResult res;
        res.cohort_size = costs.size();
        res.expected_sum = accumulate(costs.begin(), costs.end(), (int64_t)0);

        // Measure Keygen sizes
        res.public_key_bytes = get_serialized_size(public_key);
        res.secret_key_bytes = get_serialized_size(secret_key);
        res.relin_keys_bytes = get_serialized_size(relin_keys);

        // 1. Encoding
        auto t0 = chrono::high_resolution_clock::now();
        vector<Plaintext> plaintexts(costs.size());
        for (size_t i = 0; i < costs.size(); ++i) {
            vector<int64_t> pod(batch_encoder.slot_count(), 0);
            pod[0] = costs[i];
            batch_encoder.encode(pod, plaintexts[i]);
        }
        auto t1 = chrono::high_resolution_clock::now();

        // 2. Encryption
        vector<Ciphertext> ciphertexts(costs.size());
        for (size_t i = 0; i < costs.size(); ++i) {
            encryptor.encrypt(plaintexts[i], ciphertexts[i]);
        }
        auto t2 = chrono::high_resolution_clock::now();

        if (!ciphertexts.empty()) {
            res.ciphertext_bytes = get_serialized_size(ciphertexts[0]);
            res.total_ciphertext_bytes = res.ciphertext_bytes * costs.size();
            size_t raw_plaintext_bytes = costs.size() * sizeof(int64_t);
            res.expansion_ratio = (double)res.total_ciphertext_bytes / (double)raw_plaintext_bytes;
        } else {
            res.ciphertext_bytes = 0;
            res.total_ciphertext_bytes = 0;
            res.expansion_ratio = 1.0;
        }

        // 3. Cloud Evaluation (Homomorphic SUM)
        auto t3 = chrono::high_resolution_clock::now();
        Ciphertext ct_sum;
        if (!ciphertexts.empty()) {
            ct_sum = ciphertexts[0];
            for (size_t i = 1; i < ciphertexts.size(); ++i) {
                evaluator.add_inplace(ct_sum, ciphertexts[i]);
            }
        } else {
            Plaintext p_zero;
            vector<int64_t> pod(batch_encoder.slot_count(), 0);
            batch_encoder.encode(pod, p_zero);
            encryptor.encrypt(p_zero, ct_sum);
        }
        auto t4 = chrono::high_resolution_clock::now();

        res.noise_budget_remaining = decryptor.invariant_noise_budget(ct_sum);

        // 4. Decryption
        Plaintext plain_sum;
        decryptor.decrypt(ct_sum, plain_sum);
        auto t5 = chrono::high_resolution_clock::now();

        // 5. Decoding
        vector<int64_t> result_pod;
        batch_encoder.decode(plain_sum, result_pod);
        auto t6 = chrono::high_resolution_clock::now();

        res.actual_sum = result_pod[0];
        res.exact_match = (res.actual_sum == res.expected_sum);

        res.encode_ms = chrono::duration<double, milli>(t1 - t0).count();
        res.encrypt_ms = chrono::duration<double, milli>(t2 - t1).count();
        res.eval_add_ms = chrono::duration<double, milli>(t4 - t3).count();
        res.decrypt_ms = chrono::duration<double, milli>(t5 - t4).count();
        res.decode_ms = chrono::duration<double, milli>(t6 - t5).count();
        res.total_e2e_ms = chrono::duration<double, milli>(t6 - t0).count();
        res.keygen_ms = 0.0; // Keygen amortized

        return res;
    }

    // TC-19: Malicious worker test (Integrity-gap scenario)
    // Demonstrates that an untrusted cloud server can add a forged offset into the ciphertext
    // and the data owner will decrypt the forged sum successfully without cryptographic error.
    pair<int64_t, int64_t> run_tamper_test(const vector<int64_t> &costs, int64_t tamper_offset) {
        int64_t expected_honest = accumulate(costs.begin(), costs.end(), (int64_t)0);

        vector<Plaintext> plaintexts(costs.size());
        vector<Ciphertext> ciphertexts(costs.size());
        for (size_t i = 0; i < costs.size(); ++i) {
            vector<int64_t> pod(batch_encoder.slot_count(), 0);
            pod[0] = costs[i];
            batch_encoder.encode(pod, plaintexts[i]);
            encryptor.encrypt(plaintexts[i], ciphertexts[i]);
        }

        Ciphertext ct_sum = ciphertexts[0];
        for (size_t i = 1; i < ciphertexts.size(); ++i) {
            evaluator.add_inplace(ct_sum, ciphertexts[i]);
        }

        // Malicious cloud worker injects an unauthorized value into the homomorphic sum
        Plaintext plain_offset;
        vector<int64_t> offset_pod(batch_encoder.slot_count(), 0);
        offset_pod[0] = tamper_offset;
        batch_encoder.encode(offset_pod, plain_offset);

        // Worker adds forged offset using evaluator.add_plain
        evaluator.add_plain_inplace(ct_sum, plain_offset);

        // Owner decrypts the forged ciphertext
        Plaintext plain_res;
        decryptor.decrypt(ct_sum, plain_res);
        vector<int64_t> res_pod;
        batch_encoder.decode(plain_res, res_pod);
        int64_t tampered_sum = res_pod[0];

        return {expected_honest, tampered_sum};
    }
};

void print_json_benchmark(const vector<BenchmarkResult> &results) {
    cout << "{\n";
    cout << "  \"scheme\": \"SEAL-BFV\",\n";
    cout << "  \"poly_modulus_degree\": 8192,\n";
    cout << "  \"security_level_bits\": 128,\n";
    cout << "  \"plain_modulus_bits\": 30,\n";
    cout << "  \"public_key_bytes\": " << results[0].public_key_bytes << ",\n";
    cout << "  \"secret_key_bytes\": " << results[0].secret_key_bytes << ",\n";
    cout << "  \"ciphertext_item_bytes\": " << results[0].ciphertext_bytes << ",\n";
    cout << "  \"runs\": [\n";
    for (size_t i = 0; i < results.size(); ++i) {
        const auto &r = results[i];
        cout << "    {\n";
        cout << "      \"cohort_size\": " << r.cohort_size << ",\n";
        cout << "      \"expected_sum\": " << r.expected_sum << ",\n";
        cout << "      \"actual_sum\": " << r.actual_sum << ",\n";
        cout << "      \"exact_match\": " << (r.exact_match ? "true" : "false") << ",\n";
        cout << "      \"noise_budget_remaining\": " << r.noise_budget_remaining << ",\n";
        cout << "      \"total_ciphertext_bytes\": " << r.total_ciphertext_bytes << ",\n";
        cout << "      \"expansion_ratio\": " << fixed << setprecision(2) << r.expansion_ratio << ",\n";
        cout << "      \"timings_ms\": {\n";
        cout << "        \"encode\": " << setprecision(3) << r.encode_ms << ",\n";
        cout << "        \"encrypt\": " << r.encrypt_ms << ",\n";
        cout << "        \"eval_add\": " << r.eval_add_ms << ",\n";
        cout << "        \"decrypt\": " << r.decrypt_ms << ",\n";
        cout << "        \"decode\": " << r.decode_ms << ",\n";
        cout << "        \"total_e2e\": " << r.total_e2e_ms << "\n";
        cout << "      }\n";
        cout << "    }" << (i + 1 < results.size() ? "," : "") << "\n";
    }
    cout << "  ]\n";
    cout << "}\n";
}

int main(int argc, char* argv[]) {
    try {
        string mode = (argc > 1) ? argv[1] : "benchmark";

        if (mode == "benchmark") {
            vector<size_t> cohort_sizes = {10, 50, 100, 250, 500, 1000};
            if (argc > 2) {
                cohort_sizes.clear();
                for (int i = 2; i < argc; ++i) {
                    cohort_sizes.push_back(stoul(argv[i]));
                }
            }

            BFVEngine engine(8192, 30);
            mt19937_64 rng(1801); // Deterministic seed
            uniform_int_distribution<int64_t> dist(50, 2500); // Treatment costs $50 - $2500

            vector<BenchmarkResult> results;
            for (size_t sz : cohort_sizes) {
                vector<int64_t> costs(sz);
                for (size_t i = 0; i < sz; ++i) {
                    costs[i] = dist(rng);
                }
                BenchmarkResult res = engine.run_aggregation_benchmark(costs);
                results.push_back(res);
            }

            print_json_benchmark(results);
            return 0;
        }

        if (mode == "tamper_test") {
            // TC-19: Malicious worker tamper scenario
            int64_t tamper_offset = (argc > 2) ? stoll(argv[2]) : 500;
            vector<int64_t> costs = {150, 350, 500, 1000}; // sum = 2000

            BFVEngine engine(8192, 30);
            auto [expected_honest, tampered_sum] = engine.run_tamper_test(costs, tamper_offset);

            cout << "{\n";
            cout << "  \"test\": \"TC-19_MALICIOUS_WORKER_TAMPER\",\n";
            cout << "  \"expected_honest_sum\": " << expected_honest << ",\n";
            cout << "  \"tamper_offset\": " << tamper_offset << ",\n";
            cout << "  \"decrypted_tampered_sum\": " << tampered_sum << ",\n";
            cout << "  \"integrity_gap_demonstrated\": " << (tampered_sum != expected_honest ? "true" : "false") << ",\n";
            cout << "  \"conclusion\": \"BFV guarantees confidentiality but does NOT protect against active malicious worker tampering without separate verifiable proofs (LIMIT verified).\"\n";
            cout << "}\n";
            return 0;
        }

        if (mode == "aggregate") {
            // Aggregate arbitrary list of integers from CLI
            if (argc < 3) {
                cerr << "Usage: " << argv[0] << " aggregate <v1> <v2> ...\n";
                return 1;
            }
            vector<int64_t> costs;
            for (int i = 2; i < argc; ++i) {
                costs.push_back(stoll(argv[i]));
            }
            BFVEngine engine(8192, 30);
            BenchmarkResult res = engine.run_aggregation_benchmark(costs);
            vector<BenchmarkResult> results = {res};
            print_json_benchmark(results);
            return 0;
        }

        cerr << "Unknown mode: " << mode << "\n";
        return 1;
    } catch (const exception &e) {
        cerr << "Error: " << e.what() << "\n";
        return 1;
    }
}
