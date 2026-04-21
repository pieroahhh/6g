"""
Phase 1: SYSTEM SETUP (Device-side parameter loading/initialization)

Compares: Our scheme vs Ref [19], [20], [22], [33]

Device-side setup means: receiving/loading public parameters and
performing any local initialization needed before key generation.

All 5 schemes participate here — every scheme requires some setup
work on the device to be ready for subsequent operations.
"""

import os
import hashlib
from bench_common import (
    measure, print_system_info, save_results,
    ATTRIBUTE_COUNTS, ITERATIONS,
    simulate_rlwe_operation, simulate_pairing_operation,
    simulate_ecc_point_mult,
)


# ============================================================
# OUR SCHEME — Device only receives PP from AC, minimal local init
# ============================================================
class OurScheme_Setup:
    def run(self, num_attrs):
        # Load public parameters (symmetric + hash primitives only on device)
        # ABE public params handled in TEE, not on device
        pp = os.urandom(64)
        _ = hashlib.sha256(pp).digest()
        # TEE attestation handshake (constant)
        _ = hashlib.sha256(pp + b"tee_init").digest()


# ============================================================
# REF [19] CDSS-RLWE — Device loads RLWE public params (per-attribute)
# ============================================================
class Ref19_Setup:
    def run(self, num_attrs):
        # PK = a*beta + p*e, and PK_i = a_i + p*e_i for each attribute i in U
        # Device needs to store/process all system attribute public keys
        _ = simulate_rlwe_operation()  # PK
        for _ in range(num_attrs):
            simulate_rlwe_operation()  # PK_i per attribute


# ============================================================
# REF [20] SSL-XIoMT — ECC setup + attribute hash map
# ============================================================
class Ref20_Setup:
    def run(self, num_attrs):
        # initializeTrustedAuthority + keyGetFuncGenerator
        # Device receives PK_AA, caches attribute hash map H(attr) for each attribute
        _ = simulate_ecc_point_mult()  # base params
        for _ in range(num_attrs):
            # H(attr) -> G1 mapping precomputation
            simulate_ecc_point_mult()


# ============================================================
# REF [22] TS-MABE — Pairing setup, device loads PK_j for each AA
# ============================================================
"""class Ref22_Setup:
    def run(self, num_attrs):
        # SetupGlobal + SetupAA_j: PK = <e(g,g)^alpha_j, g^beta_j>
        # Multiple AAs (one per attribute group in worst case)
        _ = simulate_pairing_operation()  # e(g,g) base
        # AA public keys — assumed ~1 AA per ~10 attrs (typical IIoT)
        num_aas = max(1, num_attrs // 10)
        for _ in range(num_aas):
            simulate_pairing_operation()
"""

# ============================================================
# REF [33] BCCG — ECC curve setup + domain public-key load
# ============================================================
class Ref33_Setup:
    def run(self, num_attrs):
        # KGC_A generates system parameters, device loads PK_a = sk_a * P_a
        # param_a = {G_A, q, P_a, H1, H2, PK_a}
        _ = simulate_ecc_point_mult()  # domain public key
        # Hash function initialization
        _ = hashlib.sha256(os.urandom(64)).digest()


# ============================================================
# RUN
# ============================================================
def main():
    print_system_info("PHASE 1: SYSTEM SETUP BENCHMARK")
    print(f"{'Attrs':>6} | {'Ours':>10} | {'Ref [19]':>10} | {'Ref [20]':>10} | {'Ref [33]':>10}")
    print(f"{'':>6} | {'(ms)':>10} | {'(ms)':>10} | {'(ms)':>10} | {'(ms)':>10}")
    print("-" * 65)

    ours = OurScheme_Setup()
    r19  = Ref19_Setup()
    r20  = Ref20_Setup()
    r33  = Ref33_Setup()

    results = []
    for n in ATTRIBUTE_COUNTS:
        t_ours = measure(lambda: ours.run(n))
        t_r19  = measure(lambda: r19.run(n))
        t_r20  = measure(lambda: r20.run(n))
        t_r33  = measure(lambda: r33.run(n))

        row = {
            "num_attributes": n,
            "our_scheme":   t_ours,
            "ref19_rlwe":   t_r19,
            "ref20_ssl":    t_r20,
            "ref33_bccg":   t_r33,
        }
        results.append(row)
        print(f"{n:>6} | {t_ours:>10.4f} | {t_r19:>10.4f} | "
              f"{t_r20:>10.4f} | {t_r33:>10.4f}")

    print("-" * 65)
    save_results(results, "setup")

if __name__ == "__main__":
    main()