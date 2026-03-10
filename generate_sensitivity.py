#!/usr/bin/env python3
"""Sensitivity analysis — Tornado chart showing which parameters most affect Year 30 EV.

Each parameter is varied ±30% from baseline while holding others constant.
Runs N trials per configuration to get median EV, then ranks by impact.
"""

from __future__ import annotations

import copy
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from taiga_sim.engines.simulation_runner import SimulationRunner
from taiga_sim.models.simulation import SimulationConfig

CHO = 1_0000_0000_0000


# ── Parameter definitions ───────────────────────────────────────────

PARAMETERS = [
    # (label, config_path, baseline_override, swing_pct)
    ("M&A EV/EBITDA ceiling",        "ma.target_ev_ebitda",                    None, 0.30),
    ("M&A max leverage (deal)",       "ma.max_leverage",                        None, 0.30),
    ("M&A max leverage (group)",      "ma.group_max_leverage",                  None, 0.30),
    ("PMI EBITDA improvement",        "ma.pmi_ebitda_improvement",              None, 0.30),
    ("Macro shock probability",       "macro.shock_probability",                None, 0.50),
    ("Macro shock EV decline",        "macro.shock_ev_decline",                 None, 0.30),
    ("GDP growth rate",               "macro.gdp_growth_rate",                  None, 0.50),
    ("Seed funding",                  "seed_funding",                           None, 0.30),
    ("Initial equity dilution",       "initial_equity_dilution",                None, 0.30),
    ("PMI margin improvement",        "conglomerate.pmi_margin_improvement",    None, 0.30),
    ("Monitoring decay rate",         "conglomerate.monitoring_decay_rate",      None, 0.50),
    ("Unrelated discount",            "conglomerate.unrelated_discount",        None, 0.30),
    ("Platform premium max",          "conglomerate.platform_premium_max",      None, 0.30),
    ("Annual turnover rate",          "hr.annual_turnover_rate",                None, 0.50),
    ("Bonus pool rate",               "compensation.bonus_pool_rate",           None, 0.30),
    ("Keshiki reserve rate",          "compensation.keshiki_reserve_rate",      None, 0.30),
]


def set_nested_attr(obj, path: str, value):
    """Set attribute on nested object using dot notation."""
    parts = path.split(".")
    for part in parts[:-1]:
        obj = getattr(obj, part)
    setattr(obj, parts[-1], value)


def get_nested_attr(obj, path: str):
    parts = path.split(".")
    for part in parts:
        obj = getattr(obj, part)
    return obj


def run_trials(config: SimulationConfig, n_trials: int, years: int = 30) -> list[float]:
    """Run n_trials and return list of final EV values."""
    evs = []
    for seed in range(n_trials):
        runner = SimulationRunner(config=config, seed=seed)
        reports = runner.run(years=years)
        evs.append(reports[-1].enterprise_value)
    return evs


def main():
    n_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 50

    base_config = SimulationConfig()
    print(f"Running sensitivity analysis ({n_trials} trials per config)...")
    t0 = time.time()

    # Baseline
    print("  Baseline...", end=" ", flush=True)
    base_evs = run_trials(base_config, n_trials)
    base_median = float(np.median(base_evs))
    print(f"median EV = {base_median/CHO:.2f} Cho")

    results = []

    for label, path, override, swing in PARAMETERS:
        baseline_val = get_nested_attr(base_config, path) if override is None else override

        # Low scenario
        config_lo = copy.deepcopy(base_config)
        val_lo = baseline_val * (1 - swing)
        set_nested_attr(config_lo, path, val_lo)
        evs_lo = run_trials(config_lo, n_trials)
        median_lo = float(np.median(evs_lo))

        # High scenario
        config_hi = copy.deepcopy(base_config)
        val_hi = baseline_val * (1 + swing)
        set_nested_attr(config_hi, path, val_hi)
        evs_hi = run_trials(config_hi, n_trials)
        median_hi = float(np.median(evs_hi))

        spread = abs(median_hi - median_lo)
        results.append((label, median_lo, median_hi, baseline_val, swing, spread))
        print(f"  {label:<35} Lo={median_lo/CHO:>7.2f}  Hi={median_hi/CHO:>7.2f}  Spread={spread/CHO:.2f} Cho")

    elapsed = time.time() - t0
    print(f"\nTotal time: {elapsed:.0f}s")

    # Sort by spread descending
    results.sort(key=lambda x: x[5], reverse=True)

    # ── Tornado Chart ───────────────────────────────────────────────
    plt.rcParams.update({"font.size": 11, "figure.facecolor": "white"})
    fig, ax = plt.subplots(figsize=(14, 10))

    labels = [r[0] for r in results]
    lows = [r[1] / CHO for r in results]
    highs = [r[2] / CHO for r in results]
    base_cho = base_median / CHO

    y_pos = np.arange(len(labels))

    # Draw bars from base_median
    for i, (lo, hi) in enumerate(zip(lows, highs)):
        left = min(lo, hi)
        right = max(lo, hi)

        # Color: left of baseline = red region, right = green
        if lo < hi:
            # Low param -> low EV (red), High param -> high EV (green)
            ax.barh(i, base_cho - left, left=left, height=0.6, color="#EF5350", alpha=0.8)
            ax.barh(i, right - base_cho, left=base_cho, height=0.6, color="#66BB6A", alpha=0.8)
        else:
            # Inverted: low param -> high EV, high param -> low EV
            ax.barh(i, right - base_cho, left=base_cho, height=0.6, color="#EF5350", alpha=0.8)
            ax.barh(i, base_cho - left, left=left, height=0.6, color="#66BB6A", alpha=0.8)

        # Value annotations
        ax.text(left - 0.3, i, f"{left:.1f}", va="center", ha="right", fontsize=9)
        ax.text(right + 0.3, i, f"{right:.1f}", va="center", ha="left", fontsize=9)

    ax.axvline(base_cho, color="black", linewidth=1.5, linestyle="-", label=f"Baseline: {base_cho:.1f} Cho")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Year 30 Median EV (Cho / Trillion JPY)")
    ax.set_title(
        f"Sensitivity Analysis — Tornado Chart\n"
        f"({n_trials} trials/config, parameters varied ±swing %)",
        fontweight="bold", fontsize=13,
    )
    ax.legend(loc="lower right", fontsize=10)
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3)

    plt.tight_layout()
    output_path = "/home/user/taiya22/data/sensitivity_tornado.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Chart saved to {output_path}")


if __name__ == "__main__":
    main()
