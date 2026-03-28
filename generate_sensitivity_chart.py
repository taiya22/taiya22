#!/usr/bin/env python3
"""Generate sensitivity tornado chart from pre-computed results."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Pre-computed results from 20 trials per config
BASE_MEDIAN = 22.05  # Cho

RESULTS = [
    # (label, lo_median_cho, hi_median_cho)
    ("M&A EV/EBITDA ceiling", 0.69, 24.00),
    ("PMI margin improvement", 20.00, 22.83),
    ("Monitoring decay rate", 22.83, 20.00),
    ("Unrelated discount", 22.83, 20.00),
    ("Platform premium max", 20.00, 22.83),
    ("PMI EBITDA improvement", 19.35, 22.05),
    ("M&A max leverage (deal)", 22.05, 22.05),
    ("M&A max leverage (group)", 22.05, 22.05),
    ("Macro shock probability", 22.05, 22.05),
    ("Macro shock EV decline", 22.05, 22.05),
    ("GDP growth rate", 22.05, 22.05),
    ("Seed funding", 22.05, 22.05),
    ("Initial equity dilution", 22.05, 22.05),
    ("Annual turnover rate", 22.05, 22.05),
    ("Bonus pool rate", 22.05, 22.05),
    ("Keshiki reserve rate", 22.05, 22.05),
]

# Sort by spread
results = sorted(RESULTS, key=lambda x: abs(x[2] - x[1]), reverse=True)

plt.rcParams.update({"font.size": 11, "figure.facecolor": "white"})
fig, ax = plt.subplots(figsize=(14, 10))

labels = [r[0] for r in results]
lows = [r[1] for r in results]
highs = [r[2] for r in results]

for i, (lo, hi) in enumerate(zip(lows, highs, strict=False)):
    left_val = min(lo, hi)
    right_val = max(lo, hi)

    if lo < hi:
        ax.barh(i, BASE_MEDIAN - left_val, left=left_val, height=0.6, color="#EF5350", alpha=0.8)
        ax.barh(
            i, right_val - BASE_MEDIAN, left=BASE_MEDIAN, height=0.6, color="#66BB6A", alpha=0.8
        )
    elif lo > hi:
        ax.barh(
            i, right_val - BASE_MEDIAN, left=BASE_MEDIAN, height=0.6, color="#EF5350", alpha=0.8
        )
        ax.barh(i, BASE_MEDIAN - left_val, left=left_val, height=0.6, color="#66BB6A", alpha=0.8)

    spread = abs(hi - lo)
    if spread > 0.1:
        ax.text(left_val - 0.3, i, f"{left_val:.1f}", va="center", ha="right", fontsize=9)
        ax.text(right_val + 0.3, i, f"{right_val:.1f}", va="center", ha="left", fontsize=9)

ax.axvline(
    BASE_MEDIAN,
    color="black",
    linewidth=1.5,
    linestyle="-",
    label=f"Baseline: {BASE_MEDIAN:.1f} Cho",
)
ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels)
ax.set_xlabel("Year 30 Median EV (Cho / Trillion JPY)")
ax.set_title(
    "Sensitivity Analysis — Tornado Chart\n(20 trials/config, parameters varied +/- 30-50%)",
    fontweight="bold",
    fontsize=13,
)

# Add legend for colors
ax.barh([], [], color="#EF5350", alpha=0.8, label="Downside (-swing)")
ax.barh([], [], color="#66BB6A", alpha=0.8, label="Upside (+swing)")
ax.legend(loc="lower right", fontsize=10)
ax.invert_yaxis()
ax.grid(axis="x", alpha=0.3)

plt.tight_layout()
output_path = "/home/user/taiya22/data/sensitivity_tornado.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"Chart saved to {output_path}")
