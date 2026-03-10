#!/usr/bin/env python3
"""Risk metrics analysis — VaR, CVaR, Max Drawdown distributions.

Provides investor-grade risk reporting:
- Value at Risk (VaR) at 95% and 99% confidence
- Conditional VaR (Expected Shortfall)
- Maximum drawdown distribution across trials
- Year-by-year EV confidence intervals
- Downside scenario characterization
"""

from __future__ import annotations

import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from taiga_sim.engines.simulation_runner import AnnualReport, SimulationRunner
from taiga_sim.models.simulation import SimulationConfig

OKU = 1_0000_0000
CHO = 1_0000_0000_0000


def run_all_trials(n_trials: int, years: int = 30) -> list[list[AnnualReport]]:
    config = SimulationConfig()
    all_trials = []
    for i in range(n_trials):
        runner = SimulationRunner(config=config, seed=i)
        reports = runner.run(years=years)
        all_trials.append(reports)
    return all_trials


def compute_max_drawdown(ev_series: list[float]) -> tuple[float, int, int]:
    """Compute max drawdown as fraction, and peak/trough years."""
    peak = ev_series[0]
    peak_yr = 0
    max_dd = 0.0
    dd_peak_yr = 0
    dd_trough_yr = 0

    for yr, ev in enumerate(ev_series):
        if ev > peak:
            peak = ev
            peak_yr = yr
        dd = (peak - ev) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
            dd_peak_yr = peak_yr
            dd_trough_yr = yr

    return max_dd, dd_peak_yr, dd_trough_yr


def compute_annual_returns(ev_series: list[float]) -> list[float]:
    """Year-over-year EV returns."""
    returns = []
    for i in range(1, len(ev_series)):
        if ev_series[i - 1] > 0:
            returns.append((ev_series[i] - ev_series[i - 1]) / ev_series[i - 1])
        else:
            returns.append(0.0)
    return returns


def main():
    n_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 100

    print(f"Running {n_trials} trials for risk metrics...")
    t0 = time.time()
    all_trials = run_all_trials(n_trials, years=30)
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.1f}s")

    n_years = len(all_trials[0])
    years = list(range(n_years))

    # ── Extract EV time series ──
    ev_matrix = np.array([
        [r.enterprise_value for r in trial] for trial in all_trials
    ])  # (n_trials, n_years)

    # ── Max Drawdown per trial ──
    drawdowns = []
    dd_details = []
    for i, trial in enumerate(all_trials):
        ev_series = [r.enterprise_value for r in trial]
        dd, peak_yr, trough_yr = compute_max_drawdown(ev_series)
        drawdowns.append(dd)
        dd_details.append((dd, peak_yr, trough_yr))
    drawdowns = np.array(drawdowns)

    # ── Annual returns ──
    all_returns = []
    for trial in all_trials:
        ev_series = [r.enterprise_value for r in trial]
        all_returns.append(compute_annual_returns(ev_series))
    return_matrix = np.array(all_returns)  # (n_trials, n_years-1)

    # ── VaR / CVaR on final EV ──
    final_evs = ev_matrix[:, -1]
    sorted_evs = np.sort(final_evs)
    var_95 = np.percentile(final_evs, 5)   # 95% VaR: 5th percentile
    var_99 = np.percentile(final_evs, 1)   # 99% VaR: 1st percentile
    cvar_95 = float(np.mean(sorted_evs[sorted_evs <= var_95])) if np.any(sorted_evs <= var_95) else var_95
    cvar_99 = float(np.mean(sorted_evs[sorted_evs <= var_99])) if np.any(sorted_evs <= var_99) else var_99

    # ── Year-by-year VaR ──
    var_95_by_year = [np.percentile(ev_matrix[:, yr], 5) for yr in range(n_years)]
    var_99_by_year = [np.percentile(ev_matrix[:, yr], 1) for yr in range(n_years)]

    # ── Print summary ──
    print(f"\n{'='*70}")
    print("RISK METRICS SUMMARY")
    print(f"{'='*70}")
    print(f"\n--- Final Year EV Distribution ---")
    print(f"  Mean:     {np.mean(final_evs)/CHO:>8.2f} Cho")
    print(f"  Median:   {np.median(final_evs)/CHO:>8.2f} Cho")
    print(f"  Std Dev:  {np.std(final_evs)/CHO:>8.2f} Cho")
    print(f"  Min:      {np.min(final_evs)/CHO:>8.2f} Cho")
    print(f"  Max:      {np.max(final_evs)/CHO:>8.2f} Cho")
    print(f"\n--- Value at Risk (Final EV) ---")
    print(f"  VaR 95%:  {var_95/CHO:>8.2f} Cho  (95% chance EV is above this)")
    print(f"  VaR 99%:  {var_99/CHO:>8.2f} Cho  (99% chance EV is above this)")
    print(f"  CVaR 95%: {cvar_95/CHO:>8.2f} Cho  (expected EV in worst 5%)")
    print(f"  CVaR 99%: {cvar_99/CHO:>8.2f} Cho  (expected EV in worst 1%)")
    print(f"\n--- Max Drawdown ---")
    print(f"  Mean:     {np.mean(drawdowns)*100:>6.1f}%")
    print(f"  Median:   {np.median(drawdowns)*100:>6.1f}%")
    print(f"  Worst:    {np.max(drawdowns)*100:>6.1f}%")
    print(f"  90th pct: {np.percentile(drawdowns, 90)*100:>6.1f}%")

    # Annual return stats
    flat_returns = return_matrix.flatten()
    neg_returns = flat_returns[flat_returns < 0]
    print(f"\n--- Annual EV Return Distribution ---")
    print(f"  Mean annual return:   {np.mean(flat_returns)*100:>6.1f}%")
    print(f"  Std of annual return: {np.std(flat_returns)*100:>6.1f}%")
    print(f"  Worst single year:    {np.min(flat_returns)*100:>6.1f}%")
    print(f"  % of negative years:  {len(neg_returns)/len(flat_returns)*100:>6.1f}%")

    # ── Charts ──────────────────────────────────────────────────────
    plt.rcParams.update({"font.size": 11, "figure.facecolor": "white", "axes.grid": True, "grid.alpha": 0.3})
    fig, axes = plt.subplots(3, 2, figsize=(16, 20))
    fig.suptitle(
        f"Risk Metrics Analysis ({n_trials:,} Trials, 30 Years)",
        fontsize=14, fontweight="bold", y=0.98,
    )

    # ── 1. EV fan chart (confidence intervals) ──
    ax = axes[0, 0]
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    pct_data = {p: [np.percentile(ev_matrix[:, yr], p) for yr in range(n_years)] for p in percentiles}

    # Bands
    bands = [
        (1, 99, "#E3F2FD", "1-99th pct"),
        (5, 95, "#BBDEFB", "5-95th pct"),
        (10, 90, "#90CAF9", "10-90th pct"),
        (25, 75, "#64B5F6", "25-75th pct"),
    ]
    for lo, hi, color, label in bands:
        ax.fill_between(years, np.array(pct_data[lo])/CHO, np.array(pct_data[hi])/CHO,
                        color=color, alpha=0.8, label=label)
    ax.plot(years, np.array(pct_data[50])/CHO, color="#1565C0", linewidth=2.5, label="Median")
    ax.set_title("EV Fan Chart (Confidence Intervals)", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Enterprise Value (Cho)")
    ax.legend(fontsize=8, loc="upper left")

    # ── 2. VaR by year ──
    ax = axes[0, 1]
    median_ev = [np.median(ev_matrix[:, yr]) for yr in range(n_years)]
    ax.fill_between(years, np.array(var_99_by_year)/CHO, np.array(var_95_by_year)/CHO,
                    color="#FFCDD2", alpha=0.6, label="VaR 95-99% band")
    ax.plot(years, np.array(var_95_by_year)/CHO, color="#F44336", linewidth=2, label="VaR 95%")
    ax.plot(years, np.array(var_99_by_year)/CHO, color="#B71C1C", linewidth=2, linestyle="--", label="VaR 99%")
    ax.plot(years, np.array(median_ev)/CHO, color="#2196F3", linewidth=2, label="Median EV")
    ax.set_title("Value at Risk by Year", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Enterprise Value (Cho)")
    ax.legend(fontsize=9)

    # ── 3. Max Drawdown distribution ──
    ax = axes[1, 0]
    ax.hist(drawdowns * 100, bins=30, color="#FF9800", alpha=0.8, edgecolor="white")
    ax.axvline(np.median(drawdowns) * 100, color="#F44336", linewidth=2, linestyle="--",
               label=f"Median: {np.median(drawdowns)*100:.1f}%")
    ax.axvline(np.percentile(drawdowns, 90) * 100, color="#B71C1C", linewidth=2, linestyle=":",
               label=f"90th pct: {np.percentile(drawdowns, 90)*100:.1f}%")
    ax.set_title("Max Drawdown Distribution", fontweight="bold")
    ax.set_xlabel("Max Drawdown (%)")
    ax.set_ylabel("# Trials")
    ax.legend(fontsize=9)

    # ── 4. Annual return distribution ──
    ax = axes[1, 1]
    ax.hist(flat_returns * 100, bins=60, color="#42A5F5", alpha=0.8, edgecolor="white")
    ax.axvline(0, color="black", linewidth=1)
    ax.axvline(np.mean(flat_returns) * 100, color="#4CAF50", linewidth=2, linestyle="--",
               label=f"Mean: {np.mean(flat_returns)*100:.1f}%")
    var_annual_95 = np.percentile(flat_returns, 5)
    ax.axvline(var_annual_95 * 100, color="#F44336", linewidth=2, linestyle="--",
               label=f"5th pct: {var_annual_95*100:.1f}%")
    ax.set_title("Annual EV Return Distribution", fontweight="bold")
    ax.set_xlabel("Annual Return (%)")
    ax.set_ylabel("# Year-Trial Observations")
    ax.legend(fontsize=9)

    # ── 5. Drawdown timing heatmap ──
    ax = axes[2, 0]
    # When do drawdowns happen? (trough year distribution)
    trough_years = [d[2] for d in dd_details if d[0] > 0.05]  # only material drawdowns
    if trough_years:
        ax.hist(trough_years, bins=range(0, 32), color="#9C27B0", alpha=0.8, edgecolor="white")
    ax.set_title("Drawdown Trough Timing (>5% drawdowns)", fontweight="bold")
    ax.set_xlabel("Year of Maximum Trough")
    ax.set_ylabel("# Trials")

    # ── 6. Worst-case scenario paths ──
    ax = axes[2, 1]
    # Plot bottom 5 paths + median + top 5
    final_order = np.argsort(final_evs)
    n_extreme = min(5, n_trials // 10)

    for idx in final_order[:n_extreme]:
        ax.plot(years, ev_matrix[idx] / CHO, color="#F44336", alpha=0.4, linewidth=1)
    for idx in final_order[-n_extreme:]:
        ax.plot(years, ev_matrix[idx] / CHO, color="#4CAF50", alpha=0.4, linewidth=1)
    ax.plot(years, np.median(ev_matrix, axis=0) / CHO, color="#1565C0", linewidth=2.5, label="Median")
    ax.plot([], [], color="#F44336", alpha=0.6, label=f"Bottom {n_extreme} paths")
    ax.plot([], [], color="#4CAF50", alpha=0.6, label=f"Top {n_extreme} paths")
    ax.set_title("Extreme Scenario Paths", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Enterprise Value (Cho)")
    ax.legend(fontsize=9)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    output_path = "/home/user/taiya22/data/risk_metrics.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nChart saved to {output_path}")


if __name__ == "__main__":
    main()
