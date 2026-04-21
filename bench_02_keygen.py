"""
Phase 2: KEY GENERATION (Device-side)

Compares: Our scheme vs Ref [19], [20], [22], [33]

Device-side key generation means: the device's share of cryptographic
work to establish or receive its attribute private key.

All 5 schemes participate here — every scheme must provision the
device with a key that binds it to its attributes/identity.
"""

import os
import hashlib
import hmac
from bench_common import (
    measure, print_system_info, save_results,
    ATTRIBUTE_COUNTS,
    simulate_rlwe_operation, simulate_pairing_operation,
    simulate_ecc_point_mult,
)


# ============================================================
# OUR SCHEME — HKDF-derived device key, ABE key sealed in TEE
# ============================================================
"""
class OurScheme_KeyGen:
    def run(self, num_attrs):
        # Device receives a symmetric master key from AC
        # Derives device-specific subkey via HKDF (RFC 5869)
        master = os.urandom(32)
        salt = os.urandom(16)
        prk = hmac.new(salt, master, hashlib.sha256).digest()
        _ = hmac.new(prk, b"\x01", hashlib.sha256).digest()
        # DID/VC binding (one hash)
        _ = hashlib.sha256(master + b"did_bind").digest()
"""

# ============================================================
# REF [19] CDSS-RLWE — Per-attribute RLWE key share
# ============================================================
class Ref19_KeyGen:
    def run(self, num_attrs):
        # SK = {K, K_i} where K_i = (a_i)^-1 * b * s_att_i^-1 + p*e''_i
        # One RLWE-level operation per user attribute
        for _ in range(num_attrs):
            simulate_rlwe_operation()


# ============================================================
# REF [20] SSL-XIoMT — ECC-based SK per attribute
# ============================================================
class Ref20_KeyGen:
    def run(self, num_attrs):
        # SK_E generation with random r in Z_p and r_j per attribute
        # Device receives and stores per-attribute key material
        _ = simulate_ecc_point_mult()  # base key r
        for _ in range(num_attrs):
            simulate_ecc_point_mult()  # per-attribute r_j


# ============================================================
# REF [22] TS-MABE — Receiver key per attribute
# ============================================================
class Ref22_KeyGen:
    def run(self, num_attrs):
        # RK_{1,i} = g^alpha_j * H(GID)^beta_j * f(R_i)^k for each attribute
        # Each attribute requires a pairing-related exponentiation
        _ = simulate_pairing_operation()  # RK_2 = g^k (base)
        for _ in range(num_attrs):
            simulate_pairing_operation()  # RK_{1,i} per attribute


# ============================================================
# REF [33] BCCG — Identity private key + PUF response
# ============================================================
"""class Ref33_KeyGen:
    def run(self, num_attrs):
        # vsk_i = H1(VID || rs || s || sk_a || T_reg) ; vpk_i = vsk_i * P_a
        # PUF challenge/response + fuzzy extractor Gen
        # Plus threshold share (x_i, y_i) from polynomial
        _ = hashlib.sha256(os.urandom(64)).digest()  # vsk_i
        _ = simulate_ecc_point_mult()                # vpk_i = vsk_i * P_a
        # Fuzzy extractor (PUF.Gen) — one HMAC-like operation
        _ = hmac.new(os.urandom(32), os.urandom(64), hashlib.sha256).digest()
        # Polynomial share evaluation f(x_i) — constant per device
        _ = hashlib.sha256(os.urandom(32)).digest()
        
"""

# ============================================================
# RUN
# ============================================================
def main():
    print_system_info("PHASE 2: KEY GENERATION BENCHMARK")
    print(f"{'Attrs':>6} | {'Ref [19]':>10} | {'Ref [20]':>10} | {'Ref [22]':>10}")
    print(f"{'':>6} | {'(ms)':>10} | {'(ms)':>10} | {'(ms)':>10}")
    print("-" * 45)

    r19  = Ref19_KeyGen()
    r20  = Ref20_KeyGen()
    r22  = Ref22_KeyGen()

    results = []
    for n in ATTRIBUTE_COUNTS:
        t_r19  = measure(lambda: r19.run(n))
        t_r20  = measure(lambda: r20.run(n))
        t_r22  = measure(lambda: r22.run(n))

        row = {
            "num_attributes": n,
            "ref19_rlwe":   t_r19,
            "ref20_ssl":    t_r20,
            "ref22_tsmabe": t_r22,
        }
        results.append(row)
        print(f"{n:>6} | {t_r19:>10.4f} | {t_r20:>10.4f} | {t_r22:>10.4f}")

    print("-" * 45)
    save_results(results, "keygen")

if __name__ == "__main__":
    main()