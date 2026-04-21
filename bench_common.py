"""
Common utilities for device-side benchmarks.
6G Cross-Domain Bilateral Access Control - IoT device benchmarks.

Target: Raspberry Pi (IoT device simulation). Currently testing on laptop.
"""

import time
import os
import hashlib
import csv
import platform
import sys
from datetime import datetime


# ============================================================
# GLOBAL CONFIGURATION
# ============================================================
ITERATIONS = 100             # Per-point iterations for averaging
SMALL_DATA_SIZE = 1024       # 1 KB — typical IoT sensor payload
ATTRIBUTE_COUNTS = [1, 2, 5, 10, 20, 40, 80, 160, 300, 500, 800, 1000, 1500, 2000]  # Matches Ref [20]

# Relative cost weights (SHA rounds per operation)
# These approximate the relative computational cost of each primitive
RLWE_ROUNDS_PER_ATTR = 15    # RLWE polynomial multiplication in R_q
PAIRING_ROUNDS_PER_ATTR = 20 # Bilinear pairing operation (very expensive)
ECC_ROUNDS_PER_ATTR = 8      # ECC point multiplication (moderate)
ABE_TEE_ROUNDS = 3           # ABE inside TEE — offloaded but adds fixed overhead
                             # (simulates TEE context switch + attribute mapping)


# ============================================================
# TIMING UTILITY
# ============================================================
def measure(func, iterations=ITERATIONS):
    """Run a function N times and return average time in milliseconds."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)
    avg = sum(times) / len(times)
    return round(avg, 4)


def measure_with_std(func, iterations=ITERATIONS):
    """Run a function N times; return (avg_ms, stdev_ms)."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)
    avg = sum(times) / len(times)
    var = sum((t - avg) ** 2 for t in times) / len(times)
    std = var ** 0.5
    return round(avg, 4), round(std, 4)


# ============================================================
# PRIMITIVE SIMULATIONS
# ============================================================
def simulate_rlwe_operation():
    """One RLWE polynomial multiplication in R_q — expensive."""
    data = os.urandom(512)
    for _ in range(RLWE_ROUNDS_PER_ATTR):
        data = hashlib.sha512(data).digest()
    return data


def simulate_pairing_operation():
    """One bilinear pairing operation — very expensive."""
    data = os.urandom(256)
    for _ in range(PAIRING_ROUNDS_PER_ATTR):
        data = hashlib.sha512(data).digest()
    return data


def simulate_ecc_point_mult():
    """One ECC point multiplication — moderate cost."""
    data = os.urandom(128)
    for _ in range(ECC_ROUNDS_PER_ATTR):
        data = hashlib.sha256(data).digest()
    return data


def simulate_tee_abe_call(num_attrs):
    """
    Our scheme: ABE executed inside TEE on edge server.
    From the device's perspective, this is just a request-response
    across the TEE boundary — constant cost regardless of attribute count.
    The device does NOT iterate over attributes.
    """
    # TEE context switch / enclave call overhead (fixed)
    data = os.urandom(64)
    for _ in range(ABE_TEE_ROUNDS):
        data = hashlib.sha256(data).digest()
    return data


# ============================================================
# SYSTEM INFO
# ============================================================
def print_system_info(title):
    print("=" * 90)
    print(title)
    print("=" * 90)
    print(f"Platform:     {platform.platform()}")
    print(f"Machine:      {platform.machine()}")
    print(f"Processor:    {platform.processor()}")
    print(f"Python:       {sys.version.split()[0]}")
    print(f"Timestamp:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Iterations:   {ITERATIONS}")
    print("=" * 90)


def save_results(results, phase_name):
    """Save results to timestamped CSV."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    machine = platform.machine().replace(' ', '_')
    filename = f"benchmark_{phase_name}_{machine}_{timestamp}.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[+] Results saved: {filename}")
    return filename
