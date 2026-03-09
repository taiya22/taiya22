#!/usr/bin/env python3
"""Generate Monte Carlo fan charts with P10/P25/P50/P75/P90 percentile bands."""

import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from taiga_sim.monte_carlo import MonteCarloResult, run_monte_carlo
from taiga_sim.models.simulation import SimulationConfig


def _oku(values: list[float]) -> list[float]:
    """Convert JPY to Oku-JPY (億円)."""
    return [v / 1_0000_0000 for v in values]


def _cho(values: list[float]) -> list[float]:
    """Convert JPY to Cho-JPY (兆円)."""
    return [v / 1_0000_0000_0000 for v in values]


def generate_charts(result: MonteCarloResult, output_path: str) -> None:
    """Create a 3x2 panel of Monte Carlo fan charts."""

    plt.rcParams.update({
        "font.size": 11,
        "figure.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.3,
    })

    fig, axes = plt.subplots(3, 2, figsize=(16, 20))
    fig.suptitle(
        f"Taiga Capital Group - Monte Carlo Simulation ({result.n_trials:,} Trials, {result.years} Years)",
        fontsize=15, fontweight="bold", y=0.98,
    )

    # ── Helper: draw fan chart ──────────────────────────────────────
    def _fan(ax, dist_list, title, ylabel, scale_fn=_oku, log=True, fmt_fn=None):
        years = [d.year for d in dist_list]
        p10 = scale_fn([d.p10 for d in dist_list])
        p25 = scale_fn([d.p25 for d in dist_list])
        p50 = scale_fn([d.p50 for d in dist_list])
        p75 = scale_fn([d.p75 for d in dist_list])
        p90 = scale_fn([d.p90 for d in dist_list])
        mean = scale_fn([d.mean for d in dist_list])

        # P10-P90 band
        ax.fill_between(years, p10, p90, alpha=0.12, color="steelblue", label="P10–P90")
        # P25-P75 band
        ax.fill_between(years, p25, p75, alpha=0.25, color="steelblue", label="P25–P75")
        # Median line
        ax.plot(years, p50, "b-", linewidth=2.5, label="P50 (Median)")
        # Mean line
        ax.plot(years, mean, "r--", linewidth=1.2, alpha=0.7, label="Mean")

        ax.set_title(title, fontweight="bold")
        ax.set_xlabel("Year")
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=9, loc="upper left")

        if log:
            ax.set_yscale("log")
            ax.set_ylim(bottom=max(min(v for v in p10 if v > 0) * 0.5, 0.1))

        if fmt_fn:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_fn))
        else:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    # ── 1. Enterprise Value (Cho JPY / Trillion) ──
    _fan(axes[0, 0], result.ev,
         "Enterprise Value (Cho JPY)", "Cho JPY",
         scale_fn=_cho, log=True,
         fmt_fn=lambda x, _: f"{x:,.1f}")

    # ── 2. Revenue (Oku JPY / 100M) ──
    _fan(axes[0, 1], result.revenue,
         "Revenue (Oku JPY)", "Oku JPY",
         scale_fn=_oku, log=True)

    # ── 3. EBITDA (Oku JPY) ──
    _fan(axes[1, 0], result.ebitda,
         "EBITDA (Oku JPY)", "Oku JPY",
         scale_fn=_oku, log=True)

    # ── 4. Seed Investor MOIC ──
    _fan(axes[1, 1], result.moic,
         "Seed Investor MOIC", "MOIC (x)",
         scale_fn=lambda vals: vals, log=True,
         fmt_fn=lambda x, _: f"{x:,.0f}x")

    # ── 5. IRR fan chart ──
    def _pct(vals):
        return [v * 100 for v in vals]

    _fan(axes[2, 0], result.irr,
         "Seed Investor IRR (%)", "%",
         scale_fn=_pct, log=False,
         fmt_fn=lambda x, _: f"{x:.0f}%")

    # ── 6. Final-year EV histogram ──
    ax = axes[2, 1]
    final_ev_cho = [v / 1_0000_0000_0000 for v in result.final_ev]
    ax.hist(final_ev_cho, bins=40, color="steelblue", edgecolor="white", alpha=0.8)
    med = np.median(final_ev_cho)
    ax.axvline(med, color="red", linestyle="--", linewidth=2, label=f"Median: {med:,.1f} Cho")
    p10 = np.percentile(final_ev_cho, 10)
    p90 = np.percentile(final_ev_cho, 90)
    ax.axvline(p10, color="orange", linestyle=":", linewidth=1.5, label=f"P10: {p10:,.1f} Cho")
    ax.axvline(p90, color="green", linestyle=":", linewidth=1.5, label=f"P90: {p90:,.1f} Cho")
    ax.set_title(f"Year {result.years} EV Distribution", fontweight="bold")
    ax.set_xlabel("Enterprise Value (Cho JPY)")
    ax.set_ylabel("Frequency")
    ax.legend(fontsize=9)

    # Phase annotations
    phase_boundaries = [0, 1, 4, 7, 11, 16, 21]
    for ax_row in axes:
        for a in ax_row:
            for yr in phase_boundaries:
                a.axvline(x=yr, color="gray", linestyle=":", alpha=0.15)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Monte Carlo charts saved to {output_path}")


def main():
    n_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 100

    print(f"Running Monte Carlo ({n_trials:,} trials)...")
    t0 = time.time()
    result = run_monte_carlo(n_trials=n_trials, years=30)
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.1f}s")

    output_path = "/home/user/taiya22/data/monte_carlo_charts.png"
    generate_charts(result, output_path)


if __name__ == "__main__":
    main()
