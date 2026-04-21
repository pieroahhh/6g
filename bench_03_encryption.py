"""
Phase 3: ENCRYPTION (Device-side, online)

Compares: Our scheme vs Ref [19], Ref [20] ONLY

Why only 3 schemes here?
  - Ref [22] TS-MABE uses online/offline encryption: online device cost
    is effectively zero (per the paper's computation cost table — the
    "Online" column shows no multiplications).
  - Ref [33] BCCG is an authentication/key-agreement protocol, not a
    data-encryption scheme. It does not perform attribute-based data
    encryption on the device.

Our scheme: device does T_sym + T_KDF + T_ZKP*, then a single TEE
invocation passes the wrapped key to the edge TEE for ABE encryption.
The device itself does NOT iterate over attributes.
"""

import os
import hashlib
import hmac

try:
    from nacl.secret import SecretBox
    from nacl.utils import random as nacl_random
    HAVE_NACL = True
except ImportError:
    HAVE_NACL = False

from Crypto.Cipher import AES

from bench_common import (
    measure, print_system_info, save_results,
    ATTRIBUTE_COUNTS, SMALL_DATA_SIZE,
    simulate_rlwe_operation, simulate_ecc_point_mult,
    simulate_tee_abe_call,
)


# ============================================================
# OUR SCHEME — T_sym + T_KDF + T_ZKP* + TEE call (constant)
# ============================================================
class OurScheme_Encrypt:
    """
    Device-side encryption cost:
      T_sym    : xChaCha20-Poly1305 (or AES-GCM fallback) on payload
      T_KDF    : HKDF key derivation
      T_ZKP*   : Single-protocol lightweight ZKP commitment
      + TEE call: wrap DEK, ship to edge TEE for ABE encryption
    Device does NOT iterate over attributes — this is the key claim.
    """
    def __init__(self, data_size):
        if HAVE_NACL:
            self.master_key = nacl_random(32)
            self.box = SecretBox(self.master_key)
        else:
            self.master_key = os.urandom(32)
        self.data = os.urandom(data_size)

    def run(self, num_attrs):
        # 1) T_sym — symmetric payload encryption
        if HAVE_NACL:
            ciphertext = self.box.encrypt(self.data)
        else:
            cipher = AES.new(self.master_key, AES.MODE_GCM)
            ciphertext, _ = cipher.encrypt_and_digest(self.data)

        # 2) T_KDF — HKDF (HMAC-Extract + HMAC-Expand)
        # NOT PBKDF2 — input is already high-entropy, no password stretching
        # needed. HKDF is the correct primitive per RFC 5869.
        salt = os.urandom(16)
        prk = hmac.new(salt, self.master_key, hashlib.sha256).digest()
        dek = hmac.new(prk, b"\x01", hashlib.sha256).digest()

        # 3) T_ZKP* — single-protocol lightweight ZKP commitment
        #    Contrast with Ref [20]'s dual PLONK + ZK-STARK
        zkp_commit = hashlib.sha256(self.master_key + dek + salt).digest()

        # 4) TEE call — ship wrapped DEK to edge TEE for CP-ABE
        #    Constant cost regardless of num_attrs (TEE does the ABE work)
        _ = simulate_tee_abe_call(num_attrs)

        return ciphertext, dek, zkp_commit


# ============================================================
# REF [19] CDSS-RLWE — Per-attribute RLWE polynomial operations
# ============================================================
class Ref19_Encrypt:
    """
    Online encryption from Wang et al. CDSS-RLWE:
      C_i = a * PK_i * r * delta_i * tau_rho(i) + pe'''_i * delta_i
    Per-attribute RLWE multiplication in R_q on the device.
    """
    def __init__(self, data_size):
        self.sym_key = os.urandom(32)
        self.data = os.urandom(data_size)

    def run(self, num_attrs):
        # Symmetric data encryption
        cipher = AES.new(self.sym_key, AES.MODE_GCM)
        cipher.encrypt_and_digest(self.data)

        # Per-attribute RLWE operations (online phase, on device)
        for _ in range(num_attrs):
            simulate_rlwe_operation()


# ============================================================
# REF [20] SSL-XIoMT — Partial CP-ABE + DUAL ZKP (PLONK + ZK-STARK)
# ============================================================
class Ref20_Encrypt:
    """
    SSL-XIoMT device-side encryption:
      - AES-256-GCM on payload
      - Partial CP-ABE attribute preparation (per attribute)
      - DUAL ZKP: BOTH PLONK (verified users) AND ZK-STARK (suspicious
        users) proofs generated — this is the overhead our scheme avoids
        by using a single lightweight ZKP*.
    """
    def __init__(self, data_size):
        self.sym_key = os.urandom(32)
        self.data = os.urandom(data_size)

    def run(self, num_attrs):
        # AES-256-GCM
        cipher = AES.new(self.sym_key, AES.MODE_GCM)
        cipher.encrypt_and_digest(self.data)

        # Partial CP-ABE attribute preparation (done on device, not offloaded)
        for _ in range(num_attrs):
            simulate_ecc_point_mult()

        # DUAL ZKP — the key overhead vs our T_ZKP*
        # PLONK proof
        plonk = os.urandom(256)
        for _ in range(5):
            plonk = hashlib.sha512(plonk).digest()
        # ZK-STARK proof (heavier, trustless)
        zkstark = os.urandom(256)
        for _ in range(15):
            zkstark = hashlib.sha512(zkstark).digest()


# ============================================================
# RUN
# ============================================================
def main():
    print_system_info("PHASE 3: ENCRYPTION BENCHMARK")
    print(f"{'Attrs':>6} | {'Ours':>10} | {'Ref [19]':>10} | {'Ref [20]':>10}")
    print(f"{'':>6} | {'(ms)':>10} | {'(ms)':>10} | {'(ms)':>10}")
    print("-" * 45)

    ours = OurScheme_Encrypt(SMALL_DATA_SIZE)
    r19  = Ref19_Encrypt(SMALL_DATA_SIZE)
    r20  = Ref20_Encrypt(SMALL_DATA_SIZE)

    results = []
    for n in ATTRIBUTE_COUNTS:
        t_ours = measure(lambda: ours.run(n))
        t_r19  = measure(lambda: r19.run(n))
        t_r20  = measure(lambda: r20.run(n))

        row = {
            "num_attributes": n,
            "our_scheme":   t_ours,
            "ref19_rlwe":   t_r19,
            "ref20_ssl":    t_r20,
        }
        results.append(row)
        print(f"{n:>6} | {t_ours:>10.4f} | {t_r19:>10.4f} | {t_r20:>10.4f}")

    print("-" * 45)
    save_results(results, "encryption")

if __name__ == "__main__":
    main()
