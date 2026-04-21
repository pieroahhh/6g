"""
Master runner — executes all phase benchmarks sequentially.

Usage:
    python run_all.py

Each phase writes its own CSV. Use plot_results.py afterward to
generate charts from the CSVs.
"""

import subprocess
import sys
import time

BENCHMARKS = [
    ("bench_01_setup.py",      "Phase 1: System Setup"),
    ("bench_02_keygen.py",     "Phase 2: Key Generation"),
    ("bench_03_encryption.py", "Phase 3: Encryption"),
]


def main():
    print("#" * 90)
    print("#  6G CROSS-DOMAIN BILATERAL ACCESS CONTROL — FULL DEVICE-SIDE BENCHMARK")
    print("#  Running all phases sequentially")
    print("#" * 90)
    print()

    start = time.time()
    for script, name in BENCHMARKS:
        print(f"\n{'#' * 90}")
        print(f"#  {name}")
        print(f"#  Script: {script}")
        print(f"{'#' * 90}\n")
        result = subprocess.run([sys.executable, script])
        if result.returncode != 0:
            print(f"\n[!] {script} failed with exit code {result.returncode}")
            sys.exit(result.returncode)
        print(f"\n[+] {name} complete")

    elapsed = time.time() - start
    print(f"\n{'#' * 90}")
    print(f"#  ALL BENCHMARKS COMPLETE in {elapsed:.1f} seconds")
    print(f"{'#' * 90}")
    print("\nCSV outputs are in the current directory.")
    print("Run: python plot_results.py  to generate charts.")


if __name__ == "__main__":
    main()
