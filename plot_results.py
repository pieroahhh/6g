"""
Plot benchmark results.

Reads the most recent CSV for each phase and generates publication-quality
line charts in the style of Ref [20] (SSL-XIoMT) — one line per scheme,
markers at each data point, attribute count on the x-axis.

Usage:
    python plot_results.py            # linear y-axis (matches Ref [20])
    python plot_results.py --log      # log y-axis (better for wide ranges)

Run AFTER the benchmarks have produced CSVs.
"""

import glob
import csv
import os
import sys


def try_import_matplotlib():
    try:
        import matplotlib
        matplotlib.use('Agg')  # non-interactive, works headless on Pi
        import matplotlib.pyplot as plt
        return plt
    except ImportError:
        print("[!] matplotlib not installed. Install with:")
        print("    pip install matplotlib")
        sys.exit(1)


def latest_csv(pattern):
    """Return the most recent file matching the glob pattern, or None."""
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def load_csv(path):
    """Load CSV as dict-of-lists keyed by column name."""
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return {}
    cols = {key: [] for key in rows[0].keys()}
    for r in rows:
        for k, v in r.items():
            try:
                cols[k].append(float(v))
            except ValueError:
                cols[k].append(v)
    return cols


# Scheme labels, colors, markers — consistent across all plots
SCHEME_STYLE = {
    "our_scheme":   ("Ours",     "red",       "o", "-"),
    "ref19_rlwe":   ("Ref [19]", "green",     "s", "--"),
    "ref20_ssl":    ("Ref [20]", "blue",      "^", "-."),
    "ref22_tsmabe": ("Ref [22]", "orange",    "D", ":"),
    "ref33_bccg":   ("Ref [33]", "purple",    "v", "--"),
}


def plot_phase(csv_path, title, outfile, schemes, log_scale=False):
    plt = try_import_matplotlib()
    data = load_csv(csv_path)
    if not data:
        print(f"[!] Empty CSV: {csv_path}")
        return

    x = data["num_attributes"]

    fig, ax = plt.subplots(figsize=(8, 5))
    for key in schemes:
        if key not in data:
            continue
        label, color, marker, linestyle = SCHEME_STYLE[key]
        ax.plot(x, data[key],
                label=label, color=color, marker=marker,
                linestyle=linestyle, linewidth=2, markersize=7)

    ax.set_xlabel("Number of Attributes", fontsize=12)
    ax.set_ylabel("Computation Time (ms)", fontsize=12)
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.legend(loc='best', fontsize=11, frameon=True)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.tick_params(axis='both', labelsize=11)

    if log_scale:
        ax.set_yscale('log')

    plt.tight_layout()
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.savefig(outfile.replace('.png', '.pdf'), bbox_inches='tight')
    plt.close()
    print(f"[+] Saved: {outfile} (+ .pdf)")


def main():
    plt = try_import_matplotlib()  # fail fast if missing
    log_scale = "--log" in sys.argv
    suffix = "_log" if log_scale else ""

    # Phase 1: Setup — all 5 schemes
    csv1 = latest_csv("benchmark_setup_*.csv")
    if csv1:
        plot_phase(csv1,
                   "Setup Phase (Device-side)",
                   f"plot_01_setup{suffix}.png",
                   ["our_scheme", "ref19_rlwe", "ref20_ssl",
                    "ref22_tsmabe", "ref33_bccg"],
                   log_scale=log_scale)
    else:
        print("[!] No setup CSV found — run bench_01_setup.py first")

    # Phase 2: KeyGen — all 5 schemes
    csv2 = latest_csv("benchmark_keygen_*.csv")
    if csv2:
        plot_phase(csv2,
                   "Key Generation Phase (Device-side)",
                   f"plot_02_keygen{suffix}.png",
                   ["our_scheme", "ref19_rlwe", "ref20_ssl",
                    "ref22_tsmabe", "ref33_bccg"],
                   log_scale=log_scale)
    else:
        print("[!] No keygen CSV found — run bench_02_keygen.py first")

    # Phase 3: Encryption — only 3 schemes (Ours, Ref 19, Ref 20)
    csv3 = latest_csv("benchmark_encryption_*.csv")
    if csv3:
        plot_phase(csv3,
                   "Encryption Phase (Device-side, online)",
                   f"plot_03_encryption{suffix}.png",
                   ["our_scheme", "ref19_rlwe", "ref20_ssl"],
                   log_scale=log_scale)
    else:
        print("[!] No encryption CSV found — run bench_03_encryption.py first")

    print("\nDone. PNG + PDF outputs are ready for your paper.")


if __name__ == "__main__":
    main()
