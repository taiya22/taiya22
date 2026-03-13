#!/usr/bin/env python3
"""Generate motivation simulation charts comparing different organizational archetypes.

Scenarios:
1. Taiga (motivation-architecture-optimized) vs Conventional PE (incentive-heavy)
2. Crowded-out organization recovery: with vs without intervention
3. Role-level breakdown: how complexity moderates outcomes over time
"""

import copy
import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from taiga_sim.engines.motivation_engine import (
    MotivationConfig,
    MotivationEngine,
    OrganizationMotivationState,
    create_taiga_default_state,
    create_conventional_pe_state,
    create_crowded_out_recovery_state,
)


def run_scenario(name: str, state, engine: MotivationEngine, years: int = 10,
                 has_recovery: bool = False):
    """Run a scenario and return results."""
    results = engine.run_simulation(state, years=years,
                                    has_recovery_intervention=has_recovery)
    print(f"\n{'='*60}")
    print(f"Scenario: {name}")
    print(f"{'='*60}")
    print(f"{'Year':<6} {'IM':>8} {'Perf-Q':>10} {'Perf-Qty':>10} "
          f"{'Composite':>10} {'CO Damage':>10} {'Culture':>10}")
    print("-" * 64)
    for r in results:
        print(f"{r.year:<6} {r.avg_intrinsic_motivation:>8.3f} "
              f"{r.avg_performance_quality:>10.3f} "
              f"{r.avg_performance_quantity:>10.3f} "
              f"{r.avg_performance_composite:>10.3f} "
              f"{r.total_crowding_out_damage:>10.4f} "
              f"{r.motivation_culture_score:>10.3f}")
    return results


def generate_charts(output_dir: str = "docs"):
    """Generate all motivation simulation charts."""
    if not HAS_MPL:
        print("matplotlib not available — skipping chart generation.")
        print("Install with: pip install matplotlib")
        return

    engine = MotivationEngine()
    years = 10

    # -----------------------------------------------------------------------
    # Scenario 1: Taiga vs Conventional PE
    # -----------------------------------------------------------------------
    taiga_results = engine.run_simulation(
        create_taiga_default_state(), years=years
    )
    conv_results = engine.run_simulation(
        create_conventional_pe_state(), years=years
    )

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Motivation Architecture Comparison: Taiga vs Conventional PE\n"
        "(Based on Second-Order Meta-Analytic Effect Sizes)",
        fontsize=13, fontweight="bold",
    )

    yr = [r.year for r in taiga_results]

    # Panel 1: Intrinsic Motivation
    ax = axes[0, 0]
    ax.plot(yr, [r.avg_intrinsic_motivation for r in taiga_results],
            "b-o", label="Taiga (optimized)", linewidth=2, markersize=4)
    ax.plot(yr, [r.avg_intrinsic_motivation for r in conv_results],
            "r--s", label="Conventional PE", linewidth=2, markersize=4)
    ax.set_title("Intrinsic Motivation (avg)")
    ax.set_ylabel("Motivation Level")
    ax.set_xlabel("Year")
    ax.legend()
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)

    # Panel 2: Performance Quality
    ax = axes[0, 1]
    ax.plot(yr, [r.avg_performance_quality for r in taiga_results],
            "b-o", label="Taiga", linewidth=2, markersize=4)
    ax.plot(yr, [r.avg_performance_quality for r in conv_results],
            "r--s", label="Conventional PE", linewidth=2, markersize=4)
    ax.set_title("Performance Quality (creativity, problem-solving)")
    ax.set_ylabel("Effect Size")
    ax.set_xlabel("Year")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 3: Performance Quantity
    ax = axes[1, 0]
    ax.plot(yr, [r.avg_performance_quantity for r in taiga_results],
            "b-o", label="Taiga", linewidth=2, markersize=4)
    ax.plot(yr, [r.avg_performance_quantity for r in conv_results],
            "r--s", label="Conventional PE", linewidth=2, markersize=4)
    ax.set_title("Performance Quantity (output volume)")
    ax.set_ylabel("Effect Size")
    ax.set_xlabel("Year")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 4: Composite Performance
    ax = axes[1, 1]
    ax.plot(yr, [r.avg_performance_composite for r in taiga_results],
            "b-o", label="Taiga", linewidth=2, markersize=4)
    ax.plot(yr, [r.avg_performance_composite for r in conv_results],
            "r--s", label="Conventional PE", linewidth=2, markersize=4)
    ax.set_title("Composite Performance (quality-weighted)")
    ax.set_ylabel("Effect Size")
    ax.set_xlabel("Year")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path1 = f"{output_dir}/motivation_comparison.png"
    fig.savefig(path1, dpi=150, bbox_inches="tight")
    print(f"Saved: {path1}")
    plt.close()

    # -----------------------------------------------------------------------
    # Scenario 2: Crowded-Out Recovery (with vs without intervention)
    # -----------------------------------------------------------------------
    recovery_with = engine.run_simulation(
        create_crowded_out_recovery_state(), years=years,
        has_recovery_intervention=True,
    )
    recovery_without = engine.run_simulation(
        create_crowded_out_recovery_state(), years=years,
        has_recovery_intervention=False,
    )

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(
        "Crowding-Out Recovery: Post-M&A Organization\n"
        "(Research Gap 3: Can damaged intrinsic motivation be restored?)",
        fontsize=13, fontweight="bold",
    )

    yr2 = [r.year for r in recovery_with]

    # IM Recovery
    ax = axes[0]
    ax.plot(yr2, [r.avg_intrinsic_motivation for r in recovery_with],
            "g-o", label="With intervention\n(autonomy support + reframing)",
            linewidth=2, markersize=4)
    ax.plot(yr2, [r.avg_intrinsic_motivation for r in recovery_without],
            "k--s", label="Without intervention",
            linewidth=2, markersize=4)
    ax.axhline(y=0.70, color="blue", linestyle=":", alpha=0.5,
               label="Healthy baseline (0.70)")
    ax.set_title("Intrinsic Motivation Recovery")
    ax.set_ylabel("Motivation Level")
    ax.set_xlabel("Year")
    ax.legend(fontsize=8)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)

    # Quality
    ax = axes[1]
    ax.plot(yr2, [r.avg_performance_quality for r in recovery_with],
            "g-o", label="With intervention", linewidth=2, markersize=4)
    ax.plot(yr2, [r.avg_performance_quality for r in recovery_without],
            "k--s", label="Without intervention", linewidth=2, markersize=4)
    ax.set_title("Performance Quality")
    ax.set_ylabel("Effect Size")
    ax.set_xlabel("Year")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Culture Score
    ax = axes[2]
    ax.plot(yr2, [r.motivation_culture_score for r in recovery_with],
            "g-o", label="With intervention", linewidth=2, markersize=4)
    ax.plot(yr2, [r.motivation_culture_score for r in recovery_without],
            "k--s", label="Without intervention", linewidth=2, markersize=4)
    ax.set_title("Motivation Culture Score")
    ax.set_ylabel("Score")
    ax.set_xlabel("Year")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path2 = f"{output_dir}/motivation_recovery.png"
    fig.savefig(path2, dpi=150, bbox_inches="tight")
    print(f"Saved: {path2}")
    plt.close()

    # -----------------------------------------------------------------------
    # Scenario 3: Role-level breakdown (Taiga)
    # -----------------------------------------------------------------------
    taiga_detail = engine.run_simulation(
        create_taiga_default_state(), years=years
    )

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(
        "Role-Level Motivation Dynamics: Complexity Moderates Everything\n"
        "(Taiga Architecture — 10-Year Projection)",
        fontsize=13, fontweight="bold",
    )

    role_names = ["Executive / Fund Manager", "Professional / Manager",
                  "Operations / Admin"]
    colors = ["#2196F3", "#FF9800", "#4CAF50"]
    styles = ["-o", "-s", "-^"]

    for panel_idx, (metric, title, ylabel) in enumerate([
        ("intrinsic_motivation", "Intrinsic Motivation by Role", "Level"),
        ("performance_quality", "Performance Quality by Role", "Effect Size"),
        ("performance_composite", "Composite Performance by Role", "Effect Size"),
    ]):
        ax = axes[panel_idx]
        for role_idx, role_name in enumerate(role_names):
            values = []
            for snapshot in taiga_detail:
                for r in snapshot.roles:
                    if r.role_name == role_name:
                        values.append(getattr(r, metric))
                        break
            ax.plot(yr, values, styles[role_idx], color=colors[role_idx],
                    label=role_name, linewidth=2, markersize=4)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Year")
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path3 = f"{output_dir}/motivation_role_breakdown.png"
    fig.savefig(path3, dpi=150, bbox_inches="tight")
    print(f"Saved: {path3}")
    plt.close()

    print(f"\nAll charts saved to {output_dir}/")


def main():
    engine = MotivationEngine()

    # Run all scenarios with text output
    run_scenario("Taiga (Motivation Architecture)", create_taiga_default_state(), engine)
    run_scenario("Conventional PE (Incentive-Heavy)", create_conventional_pe_state(), engine)
    run_scenario("Recovery WITH Intervention",
                 create_crowded_out_recovery_state(), engine,
                 has_recovery=True)
    run_scenario("Recovery WITHOUT Intervention",
                 create_crowded_out_recovery_state(), engine,
                 has_recovery=False)

    # Generate charts
    generate_charts()


if __name__ == "__main__":
    main()
