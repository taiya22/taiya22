#!/usr/bin/env python3
"""Success vs Failure path anatomy — comparing trials that hit 30 Cho EV vs those that don't.

Identifies early divergence points: what's different at Year 5, 10, 15
between successful and failed paths?
"""

from __future__ import annotations

import sys
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
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


def classify_trials(
    all_trials: list[list[AnnualReport]],
    threshold: float = 30 * CHO,
) -> tuple[list[list[AnnualReport]], list[list[AnnualReport]]]:
    """Split into success (final EV >= threshold) and failure."""
    success = [t for t in all_trials if t[-1].enterprise_value >= threshold]
    failure = [t for t in all_trials if t[-1].enterprise_value < threshold]
    return success, failure


def extract_metric_by_year(
    trials: list[list[AnnualReport]],
    metric: str,
) -> np.ndarray:
    """Return array shape (n_trials, n_years)."""
    return np.array([[getattr(r, metric) for r in trial] for trial in trials])


def cumulative_ma(trials: list[list[AnnualReport]]) -> np.ndarray:
    """Cumulative M&A events per trial per year."""
    arr = np.array([[r.ma_events_this_year for r in trial] for trial in trials])
    return np.cumsum(arr, axis=1)


def cumulative_divestitures(trials: list[list[AnnualReport]]) -> np.ndarray:
    arr = np.array([[r.divestitures_this_year for r in trial] for trial in trials])
    return np.cumsum(arr, axis=1)


def crisis_years_count(trials: list[list[AnnualReport]]) -> np.ndarray:
    """Cumulative crisis-active years."""
    arr = np.array([[1 if r.crisis_active else 0 for r in trial] for trial in trials])
    return np.cumsum(arr, axis=1)


def main():
    n_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 100

    print(f"Running {n_trials} trials for path anatomy...")
    t0 = time.time()
    all_trials = run_all_trials(n_trials, years=30)
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.1f}s")

    # Classify: 30 Cho threshold
    success, failure = classify_trials(all_trials, 30 * CHO)
    n_s, n_f = len(success), len(failure)
    print(f"\nSuccess (>=30 Cho): {n_s} trials ({n_s / n_trials * 100:.0f}%)")
    print(f"Failure (<30 Cho):  {n_f} trials ({n_f / n_trials * 100:.0f}%)")

    if n_s < 3 or n_f < 3:
        print("Not enough trials in one group for meaningful comparison. Try more trials.")
        # Use 10 Cho as fallback threshold
        print("Falling back to 10 Cho threshold...")
        success, failure = classify_trials(all_trials, 10 * CHO)
        n_s, n_f = len(success), len(failure)
        threshold_label = "10 Cho"
        print(f"Success (>=10 Cho): {n_s} trials ({n_s / n_trials * 100:.0f}%)")
        print(f"Failure (<10 Cho):  {n_f} trials ({n_f / n_trials * 100:.0f}%)")
    else:
        threshold_label = "30 Cho"

    if n_s < 2 or n_f < 2:
        print("Still insufficient data. Exiting.")
        return

    years = list(range(len(all_trials[0])))

    # ── Metrics to compare ──
    plt.rcParams.update(
        {"font.size": 11, "figure.facecolor": "white", "axes.grid": True, "grid.alpha": 0.3}
    )
    fig, axes = plt.subplots(3, 3, figsize=(20, 18))
    fig.suptitle(
        f"Success vs Failure Path Anatomy (threshold: EV >= {threshold_label})\n"
        f"Success: {n_s} trials | Failure: {n_f} trials | Total: {n_trials}",
        fontsize=14,
        fontweight="bold",
        y=0.99,
    )

    def plot_comparison(ax, metric_fn, title, ylabel, divisor=1, fmt_fn=None):
        """Plot median + IQR band for success vs failure."""
        s_data = metric_fn(success)
        f_data = metric_fn(failure)
        s_med = np.median(s_data / divisor, axis=0)
        f_med = np.median(f_data / divisor, axis=0)
        s_q25 = np.percentile(s_data / divisor, 25, axis=0)
        s_q75 = np.percentile(s_data / divisor, 75, axis=0)
        f_q25 = np.percentile(f_data / divisor, 25, axis=0)
        f_q75 = np.percentile(f_data / divisor, 75, axis=0)

        ax.fill_between(years, s_q25, s_q75, alpha=0.15, color="#4CAF50")
        ax.fill_between(years, f_q25, f_q75, alpha=0.15, color="#F44336")
        ax.plot(years, s_med, color="#4CAF50", linewidth=2.5, label=f"Success (n={n_s})")
        ax.plot(years, f_med, color="#F44336", linewidth=2.5, label=f"Failure (n={n_f})")
        ax.set_title(title, fontweight="bold")
        ax.set_xlabel("Year")
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=9)

    # 1. Enterprise Value
    plot_comparison(
        axes[0, 0],
        lambda t: extract_metric_by_year(t, "enterprise_value"),
        "Enterprise Value",
        "EV (Cho)",
        CHO,
    )

    # 2. Revenue
    plot_comparison(
        axes[0, 1],
        lambda t: extract_metric_by_year(t, "revenue"),
        "Revenue",
        "Revenue (Oku)",
        OKU,
    )

    # 3. EBITDA
    plot_comparison(
        axes[0, 2],
        lambda t: extract_metric_by_year(t, "ebitda"),
        "EBITDA",
        "EBITDA (Oku)",
        OKU,
    )

    # 4. Number of companies
    plot_comparison(
        axes[1, 0],
        lambda t: extract_metric_by_year(t, "num_companies"),
        "Portfolio Companies",
        "# Companies",
        1,
    )

    # 5. Cumulative M&A
    plot_comparison(
        axes[1, 1],
        cumulative_ma,
        "Cumulative M&A Deals",
        "# Deals",
        1,
    )

    # 6. Cumulative Divestitures
    plot_comparison(
        axes[1, 2],
        cumulative_divestitures,
        "Cumulative Divestitures",
        "# Divestitures",
        1,
    )

    # 7. Cumulative crisis years
    plot_comparison(
        axes[2, 0],
        crisis_years_count,
        "Cumulative Crisis Years",
        "# Crisis Years",
        1,
    )

    # 8. Headcount
    plot_comparison(
        axes[2, 1],
        lambda t: extract_metric_by_year(t, "headcount"),
        "Headcount",
        "# Employees",
        1,
    )

    # 9. Early divergence summary (bar chart at key years)
    ax = axes[2, 2]
    check_years = [3, 5, 7, 10, 15]
    metrics_to_check = [
        ("EV (Oku)", "enterprise_value", OKU),
        ("Revenue (Oku)", "revenue", OKU),
        ("# Companies", "num_companies", 1),
        ("Cum M&A", None, 1),  # special
    ]

    # Print the text-based comparison
    print(f"\n{'=' * 70}")
    print("Early Divergence Point Analysis")
    print(f"{'=' * 70}")
    print(f"{'Metric':<20} {'Year':>4}  {'Success Median':>15} {'Failure Median':>15} {'Ratio':>8}")
    print("-" * 70)

    divergence_data = []
    for yr in check_years:
        for mlabel, metric, div in metrics_to_check:
            if metric is not None:
                s_vals = [getattr(t[yr], metric) / div for t in success]
                f_vals = [getattr(t[yr], metric) / div for t in failure]
            else:
                # Cumulative M&A
                s_vals = [sum(r.ma_events_this_year for r in t[: yr + 1]) for t in success]
                f_vals = [sum(r.ma_events_this_year for r in t[: yr + 1]) for t in failure]
            s_med = float(np.median(s_vals))
            f_med = float(np.median(f_vals))
            ratio = s_med / f_med if f_med > 0 else float("inf")
            divergence_data.append((yr, mlabel, s_med, f_med, ratio))
            print(f"{mlabel:<20} Y{yr:>3}  {s_med:>15,.1f} {f_med:>15,.1f} {ratio:>7.2f}x")

    # Plot: ratio at Year 5 and Year 10 for key metrics
    ax.set_title("Success/Failure Ratio at Key Years", fontweight="bold")
    bar_metrics = ["EV (Oku)", "Revenue (Oku)", "# Companies", "Cum M&A"]
    x = np.arange(len(bar_metrics))
    width = 0.15
    colors_yr = ["#2196F3", "#4CAF50", "#FF9800", "#F44336", "#9C27B0"]

    for j, yr in enumerate(check_years):
        ratios = []
        for bm in bar_metrics:
            match = [d for d in divergence_data if d[0] == yr and d[1] == bm]
            ratios.append(match[0][4] if match else 1.0)
        bars = ax.bar(
            x + j * width, ratios, width, label=f"Year {yr}", color=colors_yr[j], alpha=0.8
        )
        for bar, r in zip(bars, ratios, strict=False):
            if r < 10:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.05,
                    f"{r:.1f}x",
                    ha="center",
                    va="bottom",
                    fontsize=7,
                )

    ax.set_xticks(x + width * 2)
    ax.set_xticklabels(bar_metrics, fontsize=9)
    ax.set_ylabel("Success / Failure Ratio")
    ax.axhline(1.0, color="gray", linestyle="--", alpha=0.5)
    ax.legend(fontsize=8, ncol=2)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    output_path = "/home/user/taiya22/data/path_anatomy.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nChart saved to {output_path}")


if __name__ == "__main__":
    main()
