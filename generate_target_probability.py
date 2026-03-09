#!/usr/bin/env python3
"""Target achievement probability analysis from Monte Carlo simulation.

Answers questions like:
- "What is the probability of reaching EV 10 Cho by Year 20?"
- "By what year do we have a 50% chance of hitting 1 Cho EV?"
- "What's the probability of achieving 100x MOIC?"
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from taiga_sim.engines.simulation_runner import AnnualReport, SimulationRunner
from taiga_sim.models.simulation import SimulationConfig

OKU = 1_0000_0000       # 1 Oku = 100M JPY
CHO = 1_0000_0000_0000  # 1 Cho = 1T JPY


# ── Target definitions ──────────────────────────────────────────────

@dataclass
class Target:
    label: str
    metric: str        # attribute on AnnualReport
    threshold: float   # raw JPY or dimensionless
    color: str


EV_TARGETS = [
    Target("EV 100 Oku",  "enterprise_value", 100 * OKU,  "#2196F3"),
    Target("EV 1,000 Oku", "enterprise_value", 1000 * OKU, "#4CAF50"),
    Target("EV 1 Cho",    "enterprise_value", 1 * CHO,    "#FF9800"),
    Target("EV 10 Cho",   "enterprise_value", 10 * CHO,   "#F44336"),
    Target("EV 30 Cho",   "enterprise_value", 30 * CHO,   "#9C27B0"),
]

REV_TARGETS = [
    Target("Rev 100 Oku",   "revenue", 100 * OKU,  "#2196F3"),
    Target("Rev 1,000 Oku", "revenue", 1000 * OKU, "#4CAF50"),
    Target("Rev 5,000 Oku", "revenue", 5000 * OKU, "#FF9800"),
    Target("Rev 3 Cho",     "revenue", 3 * CHO,    "#F44336"),
]

MOIC_TARGETS = [
    Target("MOIC 10x",    "seed_investor_moic", 10,    "#2196F3"),
    Target("MOIC 100x",   "seed_investor_moic", 100,   "#4CAF50"),
    Target("MOIC 1,000x", "seed_investor_moic", 1000,  "#FF9800"),
    Target("MOIC 5,000x", "seed_investor_moic", 5000,  "#F44336"),
]

MILESTONE_TARGETS = [
    Target("EV 1 Cho (IPO-ready)", "enterprise_value", 1 * CHO, "#FF9800"),
    Target("EV 10 Cho",            "enterprise_value", 10 * CHO, "#F44336"),
    Target("MOIC 100x",            "seed_investor_moic", 100,    "#4CAF50"),
    Target("Rev 1,000 Oku",        "revenue", 1000 * OKU,       "#2196F3"),
]


# ── Simulation ──────────────────────────────────────────────────────

def run_all_trials(n_trials: int, years: int) -> list[list[AnnualReport]]:
    """Run n_trials and return all annual reports."""
    config = SimulationConfig()
    all_trials = []
    for i in range(n_trials):
        runner = SimulationRunner(config=config, seed=i)
        reports = runner.run(years=years)
        all_trials.append(reports)
    return all_trials


def compute_cumulative_probability(
    all_trials: list[list[AnnualReport]],
    target: Target,
) -> list[float]:
    """For each year, compute % of trials that have reached the target by that year."""
    n_trials = len(all_trials)
    n_years = len(all_trials[0])
    probs = []

    for yr_idx in range(n_years):
        count = 0
        for trial in all_trials:
            # Check if target was reached by this year (any year up to yr_idx)
            for t_idx in range(yr_idx + 1):
                val = getattr(trial[t_idx], target.metric)
                if val >= target.threshold:
                    count += 1
                    break
        probs.append(count / n_trials * 100)
    return probs


def compute_yearly_probability(
    all_trials: list[list[AnnualReport]],
    target: Target,
) -> list[float]:
    """For each year, compute % of trials above threshold AT that year."""
    n_trials = len(all_trials)
    n_years = len(all_trials[0])
    probs = []
    for yr_idx in range(n_years):
        count = sum(
            1 for trial in all_trials
            if getattr(trial[yr_idx], target.metric) >= target.threshold
        )
        probs.append(count / n_trials * 100)
    return probs


def find_year_for_probability(probs: list[float], pct: float) -> int | None:
    """Find the first year where cumulative probability >= pct%."""
    for yr, p in enumerate(probs):
        if p >= pct:
            return yr
    return None


# ── Chart generation ────────────────────────────────────────────────

def generate_charts(
    all_trials: list[list[AnnualReport]],
    output_path: str,
) -> None:
    n_trials = len(all_trials)
    years = list(range(len(all_trials[0])))

    plt.rcParams.update({
        "font.size": 11,
        "figure.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.3,
    })

    fig, axes = plt.subplots(3, 2, figsize=(16, 20))
    fig.suptitle(
        f"Target Achievement Probability ({n_trials:,} Trials, {len(years)-1} Years)",
        fontsize=15, fontweight="bold", y=0.98,
    )

    # ── 1. EV cumulative probability ──
    ax = axes[0, 0]
    for tgt in EV_TARGETS:
        probs = compute_cumulative_probability(all_trials, tgt)
        ax.plot(years, probs, color=tgt.color, linewidth=2, label=tgt.label)
    ax.set_title("EV Milestones - Cumulative Probability", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Probability (%)")
    ax.set_ylim(-5, 105)
    ax.axhline(50, color="gray", linestyle="--", alpha=0.4, linewidth=1)
    ax.axhline(90, color="gray", linestyle=":", alpha=0.3, linewidth=1)
    ax.legend(fontsize=9, loc="center right")

    # ── 2. Revenue cumulative probability ──
    ax = axes[0, 1]
    for tgt in REV_TARGETS:
        probs = compute_cumulative_probability(all_trials, tgt)
        ax.plot(years, probs, color=tgt.color, linewidth=2, label=tgt.label)
    ax.set_title("Revenue Milestones - Cumulative Probability", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Probability (%)")
    ax.set_ylim(-5, 105)
    ax.axhline(50, color="gray", linestyle="--", alpha=0.4, linewidth=1)
    ax.axhline(90, color="gray", linestyle=":", alpha=0.3, linewidth=1)
    ax.legend(fontsize=9, loc="center right")

    # ── 3. MOIC cumulative probability ──
    ax = axes[1, 0]
    for tgt in MOIC_TARGETS:
        probs = compute_cumulative_probability(all_trials, tgt)
        ax.plot(years, probs, color=tgt.color, linewidth=2, label=tgt.label)
    ax.set_title("Investor MOIC Milestones - Cumulative Probability", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Probability (%)")
    ax.set_ylim(-5, 105)
    ax.axhline(50, color="gray", linestyle="--", alpha=0.4, linewidth=1)
    ax.axhline(90, color="gray", linestyle=":", alpha=0.3, linewidth=1)
    ax.legend(fontsize=9, loc="center right")

    # ── 4. Key milestone "by when" summary (horizontal bar) ──
    ax = axes[1, 1]
    milestone_data = []
    for tgt in MILESTONE_TARGETS:
        probs = compute_cumulative_probability(all_trials, tgt)
        yr50 = find_year_for_probability(probs, 50)
        yr90 = find_year_for_probability(probs, 90)
        final_prob = probs[-1]
        milestone_data.append((tgt.label, yr50, yr90, final_prob, tgt.color))

    labels = [m[0] for m in milestone_data]
    yr50s = [m[1] if m[1] is not None else 31 for m in milestone_data]
    yr90s = [m[2] if m[2] is not None else 31 for m in milestone_data]
    colors = [m[4] for m in milestone_data]

    y_pos = np.arange(len(labels))
    bars50 = ax.barh(y_pos + 0.15, yr50s, height=0.3, color=colors, alpha=0.7, label="50% Prob Year")
    bars90 = ax.barh(y_pos - 0.15, yr90s, height=0.3, color=colors, alpha=0.35, label="90% Prob Year")

    # Annotate
    for i, (y50, y90, m) in enumerate(zip(yr50s, yr90s, milestone_data)):
        final_p = m[3]
        if y50 <= 30:
            ax.text(y50 + 0.3, i + 0.15, f"Y{y50}", va="center", fontsize=9, fontweight="bold")
        else:
            ax.text(0.5, i + 0.15, f"<50% (Final: {final_p:.0f}%)", va="center", fontsize=9)
        if y90 <= 30:
            ax.text(y90 + 0.3, i - 0.15, f"Y{y90}", va="center", fontsize=9, alpha=0.7)
        else:
            ax.text(0.5, i - 0.15, f"<90% (Final: {final_p:.0f}%)", va="center", fontsize=9, alpha=0.7)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Year")
    ax.set_xlim(0, 32)
    ax.set_title("When do targets hit 50% / 90%?", fontweight="bold")
    ax.legend(fontsize=9, loc="lower right")
    ax.invert_yaxis()

    # ── 5. Phase targets: probability of hitting phase targets on time ──
    ax = axes[2, 0]
    phase_targets = [
        ("P1 Y3: Rev 30 Oku",     3,  "revenue",          30 * OKU),
        ("P2 Y6: Rev 70 Oku",     6,  "revenue",          70 * OKU),
        ("P3 Y10: Rev 1000 Oku",  10, "revenue",          1000 * OKU),
        ("P4 Y15: Rev 2000 Oku",  15, "revenue",          2000 * OKU),
        ("P5 Y20: EV 1 Cho",      20, "enterprise_value", 1 * CHO),
        ("P6 Y30: EV 30 Cho",     30, "enterprise_value", 30 * CHO),
    ]
    phase_labels = []
    phase_probs = []
    phase_colors_list = ["#2196F3", "#4CAF50", "#FF9800", "#F44336", "#9C27B0", "#795548"]

    for (label, yr, metric, threshold), color in zip(phase_targets, phase_colors_list):
        count = sum(
            1 for trial in all_trials
            if getattr(trial[yr], metric) >= threshold
        )
        prob = count / n_trials * 100
        phase_labels.append(label)
        phase_probs.append(prob)

    bars = ax.barh(range(len(phase_labels)), phase_probs, color=phase_colors_list, alpha=0.8)
    for i, (p, label) in enumerate(zip(phase_probs, phase_labels)):
        ax.text(p + 1.5, i, f"{p:.0f}%", va="center", fontsize=10, fontweight="bold")
    ax.set_yticks(range(len(phase_labels)))
    ax.set_yticklabels(phase_labels)
    ax.set_xlabel("Probability (%)")
    ax.set_xlim(0, 115)
    ax.set_title("Phase Target On-Time Achievement", fontweight="bold")
    ax.axvline(50, color="gray", linestyle="--", alpha=0.4)
    ax.axvline(90, color="gray", linestyle=":", alpha=0.3)
    ax.invert_yaxis()

    # ── 6. Final Year 30 outcome distribution ──
    ax = axes[2, 1]
    final_ev = [trial[-1].enterprise_value / CHO for trial in all_trials]
    final_ev_arr = np.array(final_ev)

    # Outcome buckets
    buckets = [
        ("<1 Cho", final_ev_arr < 1),
        ("1-5 Cho", (final_ev_arr >= 1) & (final_ev_arr < 5)),
        ("5-10 Cho", (final_ev_arr >= 5) & (final_ev_arr < 10)),
        ("10-20 Cho", (final_ev_arr >= 10) & (final_ev_arr < 20)),
        ("20-30 Cho", (final_ev_arr >= 20) & (final_ev_arr < 30)),
        ("30+ Cho", final_ev_arr >= 30),
    ]
    bucket_labels = [b[0] for b in buckets]
    bucket_pcts = [b[1].sum() / n_trials * 100 for b in buckets]
    bucket_colors = ["#F44336", "#FF9800", "#FFC107", "#8BC34A", "#4CAF50", "#2196F3"]

    wedges, texts, autotexts = ax.pie(
        bucket_pcts, labels=bucket_labels, colors=bucket_colors,
        autopct=lambda p: f"{p:.0f}%" if p > 3 else "",
        startangle=90, counterclock=False,
        textprops={"fontsize": 10},
    )
    for t in autotexts:
        t.set_fontweight("bold")
    ax.set_title(f"Year 30 EV Outcome Distribution", fontweight="bold")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Charts saved to {output_path}")


# ── Text summary ────────────────────────────────────────────────────

def print_summary(all_trials: list[list[AnnualReport]]) -> None:
    n_trials = len(all_trials)
    print("=" * 80)
    print(f"Target Achievement Probability Analysis ({n_trials:,} trials)")
    print("=" * 80)

    all_targets = EV_TARGETS + REV_TARGETS + MOIC_TARGETS
    print(f"\n{'Target':<20} {'Y50%':>6} {'Y90%':>6} {'Final%':>8}")
    print("-" * 44)

    for tgt in all_targets:
        probs = compute_cumulative_probability(all_trials, tgt)
        yr50 = find_year_for_probability(probs, 50)
        yr90 = find_year_for_probability(probs, 90)
        final = probs[-1]
        y50s = f"Y{yr50}" if yr50 is not None else "N/A"
        y90s = f"Y{yr90}" if yr90 is not None else "N/A"
        print(f"{tgt.label:<20} {y50s:>6} {y90s:>6} {final:>7.1f}%")

    print("\n--- Phase Target On-Time ---")
    phase_targets = [
        ("P1 Y3: Rev 30 Oku",     3,  "revenue",          30 * OKU),
        ("P2 Y6: Rev 70 Oku",     6,  "revenue",          70 * OKU),
        ("P3 Y10: Rev 1000 Oku",  10, "revenue",          1000 * OKU),
        ("P4 Y15: Rev 2000 Oku",  15, "revenue",          2000 * OKU),
        ("P5 Y20: EV 1 Cho",      20, "enterprise_value", 1 * CHO),
        ("P6 Y30: EV 30 Cho",     30, "enterprise_value", 30 * CHO),
    ]
    for label, yr, metric, threshold in phase_targets:
        count = sum(1 for t in all_trials if getattr(t[yr], metric) >= threshold)
        print(f"  {label:<24} {count/n_trials*100:5.1f}%")


# ── Main ────────────────────────────────────────────────────────────

def main():
    n_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 100

    print(f"Running {n_trials:,} trials...")
    t0 = time.time()
    all_trials = run_all_trials(n_trials, years=30)
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.1f}s\n")

    print_summary(all_trials)

    output_path = "/home/user/taiya22/data/target_probability_charts.png"
    generate_charts(all_trials, output_path)


if __name__ == "__main__":
    main()
