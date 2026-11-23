"""
MedShare-Lab (Topic 18 — NT2205.11.CH)
Giao diện CLI cho CP-ABE Worker (workers/abe/cli.py)
Cho phép gọi trực tiếp qua docker run / subprocess mà không phụ thuộc HTTP daemon.
"""

import argparse
import base64
import json
import sys
import time

from engine import CpAbeEngine


def main():
    parser = argparse.ArgumentParser(description="MedShare-Lab CP-ABE Worker CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: setup
    p_setup = subparsers.add_parser("setup")
    p_setup.add_argument("--curve", default="BN254", choices=["BN254", "SS512", "MNT224"])

    # Subcommand: keygen
    p_keygen = subparsers.add_parser("keygen")
    p_keygen.add_argument("--curve", default="BN254")
    p_keygen.add_argument("--pk", required=True)
    p_keygen.add_argument("--msk", required=True)
    p_keygen.add_argument("--attributes", required=True, help="Comma-separated attribute list")

    # Subcommand: package
    p_pkg = subparsers.add_parser("package")
    p_pkg.add_argument("--curve", default="BN254")
    p_pkg.add_argument("--pk", required=True)
    p_pkg.add_argument("--payload-b64", required=True)
    p_pkg.add_argument("--policy", required=True)
    p_pkg.add_argument("--tenant-id", required=True)
    p_pkg.add_argument("--epoch-id", required=True)

    # Subcommand: decrypt
    p_dec = subparsers.add_parser("decrypt")
    p_dec.add_argument("--curve", default="BN254")
    p_dec.add_argument("--pk", required=True)
    p_dec.add_argument("--package-json", required=True)
    p_dec.add_argument("--sk", required=True)

    # Subcommand: collusion
    p_coll = subparsers.add_parser("collusion")
    p_coll.add_argument("--curve", default="BN254")
    p_coll.add_argument("--pk", required=True)
    p_coll.add_argument("--msk", required=True)
    p_coll.add_argument("--policy", required=True)
    p_coll.add_argument("--u1", required=True, help="Comma-separated attributes for U1")
    p_coll.add_argument("--u2", required=True, help="Comma-separated attributes for U2")
    p_coll.add_argument("--u3", required=True, help="Comma-separated attributes for U3 (authorized)")

    # Subcommand: benchmark
    p_bench = subparsers.add_parser("benchmark")
    p_bench.add_argument("--curves", default="BN254,SS512")
    p_bench.add_argument("--leaves", default="2,4,8,16")
    p_bench.add_argument("--iterations", type=int, default=3)

    args = parser.parse_args()

    if args.command == "setup":
        engine = CpAbeEngine(curve=args.curve)
        pk_b64, msk_b64, desc = engine.setup()
        print(json.dumps({
            "status": "success",
            "pk": pk_b64,
            "msk": msk_b64,
            "descriptor": desc,
        }))

    elif args.command == "keygen":
        engine = CpAbeEngine(curve=args.curve)
        attrs = [a.strip() for a in args.attributes.split(",") if a.strip()]
        sk_b64 = engine.keygen(args.pk, args.msk, attrs)
        print(json.dumps({
            "status": "success",
            "sk": sk_b64,
            "attributes": attrs,
        }))

    elif args.command == "package":
        engine = CpAbeEngine(curve=args.curve)
        payload = base64.b64decode(args.payload_b64.encode("ascii"))
        package = engine.create_export_package(
            pk_b64=args.pk,
            payload=payload,
            policy=args.policy,
            tenant_id=args.tenant_id,
            epoch_id=args.epoch_id,
        )
        print(json.dumps({
            "status": "success",
            "package": package,
        }))

    elif args.command == "decrypt":
        engine = CpAbeEngine(curve=args.curve)
        pkg = json.loads(args.package_json)
        try:
            payload = engine.decrypt_export_package(args.pk, pkg, args.sk)
            print(json.dumps({
                "status": "success",
                "payload_b64": base64.b64encode(payload).decode("ascii"),
            }))
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "error": str(e),
            }))
            sys.exit(1)

    elif args.command == "collusion":
        engine = CpAbeEngine(curve=args.curve)
        u1_attrs = [a.strip() for a in args.u1.split(",") if a.strip()]
        u2_attrs = [a.strip() for a in args.u2.split(",") if a.strip()]
        u3_attrs = [a.strip() for a in args.u3.split(",") if a.strip()]
        result = engine.test_collusion(
            pk_b64=args.pk,
            msk_b64=args.msk,
            policy=args.policy,
            u1_attrs=u1_attrs,
            u2_attrs=u2_attrs,
            u3_authorized_attrs=u3_attrs,
        )
        print(json.dumps({
            "status": "success",
            "result": result,
        }))

    elif args.command == "benchmark":
        curves = [c.strip() for c in args.curves.split(",") if c.strip()]
        leaves_list = [int(k.strip()) for k in args.leaves.split(",") if k.strip()]
        iterations = args.iterations

        bench_results = []
        for curve in curves:
            engine = CpAbeEngine(curve=curve)
            # 1. Setup timing
            setup_times = []
            for _ in range(iterations):
                t0 = time.perf_counter()
                pk, msk, desc = engine.setup()
                t1 = time.perf_counter()
                setup_times.append((t1 - t0) * 1000)
            avg_setup_ms = sum(setup_times) / len(setup_times)
            pk_size_bytes = len(base64.b64decode(pk.encode("ascii")))
            msk_size_bytes = len(base64.b64decode(msk.encode("ascii")))

            # Benchmark across policy complexities
            for k in leaves_list:
                # Tạo policy cân bằng gồm k lá: (ATTR0 and ATTR1 and ... and ATTRk-1)
                attrs_all = [f"ATTR{i}" for i in range(k)]
                policy_str = " and ".join(attrs_all)
                if k > 1:
                    policy_str = f"({policy_str})"

                # KeyGen timing
                keygen_times = []
                for _ in range(iterations):
                    t0 = time.perf_counter()
                    sk = engine.keygen(pk, msk, attrs_all)
                    t1 = time.perf_counter()
                    keygen_times.append((t1 - t0) * 1000)
                avg_keygen_ms = sum(keygen_times) / len(keygen_times)
                sk_size_bytes = len(base64.b64decode(sk.encode("ascii")))

                # Export package (Encrypt) timing
                payload = b"PATIENT_EHR_EXPORT_RECORD_" + (b"X" * 1024)  # 1 KB payload
                enc_times = []
                pkg = None
                for _ in range(iterations):
                    t0 = time.perf_counter()
                    pkg = engine.create_export_package(
                        pk_b64=pk,
                        payload=payload,
                        policy=policy_str,
                        tenant_id="hospital_a",
                        epoch_id="EPOCH_2026_Q3",
                    )
                    t1 = time.perf_counter()
                    enc_times.append((t1 - t0) * 1000)
                avg_enc_ms = sum(enc_times) / len(enc_times)
                kem_size_bytes = len(base64.b64decode(pkg["kem_ciphertext"].encode("ascii")))
                total_pkg_bytes = len(json.dumps(pkg).encode("utf-8"))

                # Decrypt timing
                dec_times = []
                for _ in range(iterations):
                    t0 = time.perf_counter()
                    recovered = engine.decrypt_export_package(pk, pkg, sk)
                    t1 = time.perf_counter()
                    assert recovered == payload
                    dec_times.append((t1 - t0) * 1000)
                avg_dec_ms = sum(dec_times) / len(dec_times)

                bench_results.append({
                    "curve": curve,
                    "security_level": desc["security_notes"],
                    "policy_leaves": k,
                    "policy": policy_str,
                    "setup_time_ms": round(avg_setup_ms, 2),
                    "pk_size_bytes": pk_size_bytes,
                    "msk_size_bytes": msk_size_bytes,
                    "keygen_time_ms": round(avg_keygen_ms, 2),
                    "user_key_size_bytes": sk_size_bytes,
                    "encrypt_time_ms": round(avg_enc_ms, 2),
                    "kem_ciphertext_bytes": kem_size_bytes,
                    "total_package_bytes": total_pkg_bytes,
                    "decrypt_time_ms": round(avg_dec_ms, 2),
                })

        print(json.dumps({
            "status": "success",
            "benchmark_results": bench_results,
        }, indent=2))


if __name__ == "__main__":
    main()
