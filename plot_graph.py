"""
Cross-Domain Computational Cost Comparison
===========================================
Visualizes the theoretical computational cost of 5 cryptographic schemes
across varying access policy sizes (l), based on formulas from Table IV.

Usage:
    pip install matplotlib pandas numpy
    python cross_domain_benchmark.py

NOTE: Replace T_PRE with your actual measured benchmark value.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import rcParams

# ─────────────────────────────────────────────
# 0.  Publication-quality matplotlib settings
# ─────────────────────────────────────────────
rcParams.update({
    "font.family":        "serif",
    "font.serif":         ["Times New Roman", "DejaVu Serif"],
    "font.size":          11,
    "axes.titlesize":     12,
    "axes.labelsize":     11,
    "xtick.labelsize":    10,
    "ytick.labelsize":    10,
    "legend.fontsize":    9.5,
    "legend.framealpha":  0.92,
    "legend.edgecolor":   "#cccccc",
    "figure.dpi":         150,
    "savefig.dpi":        300,
    "savefig.bbox":       "tight",
    "axes.grid":          True,
    "grid.linestyle":     "--",
    "grid.linewidth":     0.55,
    "grid.alpha":         0.55,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
})

# ─────────────────────────────────────────────
# 1.  Primitive execution times (ms)
#     *** Replace T_PRE with your measured value ***
# ─────────────────────────────────────────────
T_PRE      = 0.6349   # ← YOUR VALUE HERE (EC Proxy Re-Encryption, ms)
T_BC       = 25.0   # Hyperledger Fabric read/query
T_mul_Rq   = 0.5    # Polynomial-ring multiplication
T_ecm      = 0.8    # EC scalar multiplication
T_eca      = 0.05   # EC addition
T_P        = 3.5    # Bilinear pairing
T_E        = 1.2    # Exponentiation
T_ET       = 1.5    # Target-group exponentiation
T_H        = 0.01   # Cryptographic hash

# ─────────────────────────────────────────────
# 2.  System parameters (constants)
# ─────────────────────────────────────────────
I_prime = 10    # Number of indexes
n_AA    = 3     # Number of attribute authorities
n_s     = 5     # Number of sub-authorities
c_m     = 5     # Constant multiplier for hash

# ─────────────────────────────────────────────
# 3.  Access policy size range
# ─────────────────────────────────────────────
l_values = np.arange(5, 55, 5)   # 5, 10, 15, …, 50

# ─────────────────────────────────────────────
# 4.  Formula implementations  (Table IV)
# ─────────────────────────────────────────────
def scheme_19(l):
    """(2l + 6)·T_mul_Rq + T_BC"""
    return (2 * l + 6) * T_mul_Rq + T_BC

def scheme_20(l):
    """T_ecm + c_m·T_H + T_BC  (l-independent)"""
    return T_ecm + c_m * T_H + T_BC

def scheme_22(l):
    """
    Prover side : 3·I'·T_P + I'·T_E + 2·I'·T_ET
    Verifier side: 2·n_AA·T_P + (3·n_AA + l + n_s)·T_E + 2·n_AA·T_ET
    """
    prover   = 3*I_prime*T_P + I_prime*T_E + 2*I_prime*T_ET
    verifier = (2*n_AA*T_P
                + (3*n_AA + l + n_s)*T_E
                + 2*n_AA*T_ET)
    return prover + verifier

def scheme_33(l):
    """10·T_ecm + 3·T_eca + 6·T_H  (l-independent)"""
    return 10*T_ecm + 3*T_eca + 6*T_H

def scheme_ours(l):
    """T_PRE + T_BC  (l-independent)"""
    return T_PRE + T_BC

# ─────────────────────────────────────────────
# 5.  Compute costs & build DataFrame
# ─────────────────────────────────────────────
data = {
    "l":           l_values,
    "Scheme [19]": scheme_19(l_values),
    "Scheme [20]": scheme_20(l_values),
    "Scheme [22]": scheme_22(l_values),
    "Scheme [33]": scheme_33(l_values),
    "Ours":        scheme_ours(l_values),
}
df = pd.DataFrame(data).set_index("l")

print("=" * 62)
print("Cross-Domain Computational Cost (ms) — Table IV")
print("=" * 62)
print(df.to_string(float_format="{:.3f}".format))
print("=" * 62)

# ─────────────────────────────────────────────
# 6.  Plot configuration
# ─────────────────────────────────────────────
SCHEME_STYLES = {
    #  label         color       marker  linestyle  linewidth
    "Scheme [19]": ("#d62728", "o",     "-",       1.8),
    "Scheme [20]": ("#1f77b4", "s",     "--",      1.8),
    "Scheme [22]": ("#2ca02c", "^",     "-.",      1.8),
    "Scheme [33]": ("#ff7f0e", "D",     ":",       1.8),
    "Ours":        ("#9467bd", "P",     "-",       2.4),
}

fig, ax = plt.subplots(figsize=(7.2, 4.8))   # IEEE single-column width ≈ 3.5 in; double ≈ 7.2

for scheme, (color, marker, ls, lw) in SCHEME_STYLES.items():
    ax.plot(
        df.index,
        df[scheme],
        color=color,
        marker=marker,
        linestyle=ls,
        linewidth=lw,
        markersize=6,
        markerfacecolor="white" if scheme != "Ours" else color,
        markeredgewidth=1.6,
        label=scheme,
        zorder=3,
    )

# ─── Annotations for "Ours" flat line ────────────────────────────────────────
ours_val = df["Ours"].iloc[0]
ax.annotate(
    f"Ours: {ours_val:.1f} ms",
    xy=(l_values[-1], ours_val),
    xytext=(l_values[-1] - 8, ours_val + 3.5),
    fontsize=8.5,
    color=SCHEME_STYLES["Ours"][0],
    arrowprops=dict(arrowstyle="->", color=SCHEME_STYLES["Ours"][0], lw=1.2),
)

# ─── Axes ────────────────────────────────────────────────────────────────────
ax.set_xlabel("Access Policy Size ($l$)", labelpad=6)
ax.set_ylabel("Computational Cost (ms)", labelpad=6)
ax.set_title(
    "Cross-Domain Phase: Computational Cost Comparison\n"
    "($I' = 10,\\ n_{AA} = 3,\\ n_s = 5,\\ c_m = 5$)",
    pad=10,
)
ax.set_xticks(l_values)
ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax.tick_params(which="minor", length=3, width=0.6)
ax.set_xlim(l_values[0] - 1, l_values[-1] + 1)
ax.set_ylim(bottom=0)

# ─── Legend ──────────────────────────────────────────────────────────────────
legend = ax.legend(
    loc="upper left",
    ncol=1,
    title="Scheme",
    title_fontsize=9,
    handlelength=2.8,
    borderpad=0.7,
)

# ─── T_PRE watermark (reminder if still placeholder) ─────────────────────────
if T_PRE == 15.0:
    ax.text(
        0.99, 0.02,
        "★ Replace T_PRE with measured value",
        transform=ax.transAxes,
        ha="right", va="bottom",
        fontsize=7.5, color="gray", style="italic",
    )

plt.tight_layout()

OUTPUT_FILE = "cross_domain_cost_comparison.pdf"
fig.savefig(OUTPUT_FILE)                          # vector PDF for LaTeX
fig.savefig(OUTPUT_FILE.replace(".pdf", ".png"))  # raster PNG for quick preview
print(f"\n✓  Saved  →  {OUTPUT_FILE}  &  .png")
plt.show()
