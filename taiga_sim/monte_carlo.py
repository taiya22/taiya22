"""Monte Carlo simulation: run N trials and compute P10/P50/P90 distributions.

Uses different random seeds per trial while keeping the same config,
then aggregates results into percentile bands.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from taiga_sim.engines.simulation_runner import AnnualReport, SimulationRunner
from taiga_sim.models.simulation import SimulationConfig
from taiga_sim.utils.formatters import fmt_jpy


@dataclass
class YearlyDistribution:
    """Percentile distribution for a single year."""

    year: int
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float
    mean: float


@dataclass
class MonteCarloResult:
    """Full Monte Carlo results across all years."""

    n_trials: int
    years: int
    ev: list[YearlyDistribution]
    revenue: list[YearlyDistribution]
    ebitda: list[YearlyDistribution]
    moic: list[YearlyDistribution]
    irr: list[YearlyDistribution]
    num_companies: list[YearlyDistribution]
    # Raw final-year values for histogram
    final_ev: list[float] = field(default_factory=list)
    final_moic: list[float] = field(default_factory=list)
    final_irr: list[float] = field(default_factory=list)


def _percentile(data: list[float], pct: float) -> float:
    """Compute percentile (0-100) from sorted data."""
    sorted_data = sorted(data)
    n = len(sorted_data)
    idx = (pct / 100) * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return sorted_data[lo] * (1 - frac) + sorted_data[hi] * frac


def _make_distribution(year: int, values: list[float]) -> YearlyDistribution:
    return YearlyDistribution(
        year=year,
        p10=_percentile(values, 10),
        p25=_percentile(values, 25),
        p50=_percentile(values, 50),
        p75=_percentile(values, 75),
        p90=_percentile(values, 90),
        mean=statistics.mean(values),
    )


def run_monte_carlo(
    config: SimulationConfig | None = None,
    n_trials: int = 1000,
    years: int = 30,
    base_seed: int = 0,
) -> MonteCarloResult:
    """Run n_trials simulations with different seeds and aggregate."""
    config = config or SimulationConfig()

    # Collect all trial reports: trial_reports[trial_idx][year_idx]
    all_trials: list[list[AnnualReport]] = []

    for i in range(n_trials):
        runner = SimulationRunner(config=config, seed=base_seed + i)
        reports = runner.run(years=years)
        all_trials.append(reports)

    # Aggregate by year
    n_years = years + 1  # year 0 through year N
    ev_dist = []
    rev_dist = []
    ebitda_dist = []
    moic_dist = []
    irr_dist = []
    companies_dist = []

    for yr_idx in range(n_years):
        ev_vals = [t[yr_idx].enterprise_value for t in all_trials]
        rev_vals = [t[yr_idx].revenue for t in all_trials]
        ebitda_vals = [t[yr_idx].ebitda for t in all_trials]
        moic_vals = [t[yr_idx].seed_investor_moic for t in all_trials]
        irr_vals = [t[yr_idx].seed_investor_irr for t in all_trials]
        comp_vals = [float(t[yr_idx].num_companies) for t in all_trials]

        year = all_trials[0][yr_idx].year
        ev_dist.append(_make_distribution(year, ev_vals))
        rev_dist.append(_make_distribution(year, rev_vals))
        ebitda_dist.append(_make_distribution(year, ebitda_vals))
        moic_dist.append(_make_distribution(year, moic_vals))
        irr_dist.append(_make_distribution(year, irr_vals))
        companies_dist.append(_make_distribution(year, comp_vals))

    # Final-year raw values for histograms
    final_ev = [t[-1].enterprise_value for t in all_trials]
    final_moic = [t[-1].seed_investor_moic for t in all_trials]
    final_irr = [t[-1].seed_investor_irr for t in all_trials]

    return MonteCarloResult(
        n_trials=n_trials,
        years=years,
        ev=ev_dist,
        revenue=rev_dist,
        ebitda=ebitda_dist,
        moic=moic_dist,
        irr=irr_dist,
        num_companies=companies_dist,
        final_ev=final_ev,
        final_moic=final_moic,
        final_irr=final_irr,
    )


def format_monte_carlo_summary(result: MonteCarloResult) -> str:
    """Pretty-print the Monte Carlo results."""
    lines = []
    lines.append("=" * 90)
    lines.append(f"モンテカルロ・シミュレーション ({result.n_trials:,}回試行, {result.years}年)")
    lines.append("=" * 90)

    # Final year summary
    ev = result.ev[-1]
    rev = result.revenue[-1]
    ebitda = result.ebitda[-1]
    moic = result.moic[-1]
    irr = result.irr[-1]
    comp = result.num_companies[-1]

    lines.append(f"\n【Year {result.years} 最終結果の分布】")
    lines.append(f"{'指標':<16} {'P10':>14} {'P25':>14} {'P50':>14} {'P75':>14} {'P90':>14}")
    lines.append("-" * 90)

    def _row(label: str, d: YearlyDistribution, fmt):
        lines.append(
            f"{label:<16} {fmt(d.p10):>14} {fmt(d.p25):>14} "
            f"{fmt(d.p50):>14} {fmt(d.p75):>14} {fmt(d.p90):>14}"
        )

    _row("企業価値",     ev,     fmt_jpy)
    _row("売上高",       rev,    fmt_jpy)
    _row("EBITDA",       ebitda, fmt_jpy)
    _row("投資家MOIC",   moic,   lambda v: f"{v:,.0f}x")
    _row("投資家IRR",    irr,    lambda v: f"{v*100:.1f}%")
    _row("事業会社数",   comp,   lambda v: f"{v:.0f}社")

    lines.append("-" * 90)
    lines.append(f"  平均EV: {fmt_jpy(ev.mean)}  |  中央値EV: {fmt_jpy(ev.p50)}")

    # Year-by-year EV percentile bands
    lines.append(f"\n【企業価値 (EV) 年次推移】")
    lines.append(f"{'Year':>4}  {'P10':>14}  {'P50':>14}  {'P90':>14}  {'Mean':>14}")
    lines.append("-" * 68)
    for d in result.ev:
        lines.append(
            f"{d.year:>4}  {fmt_jpy(d.p10):>14}  {fmt_jpy(d.p50):>14}  "
            f"{fmt_jpy(d.p90):>14}  {fmt_jpy(d.mean):>14}"
        )

    return "\n".join(lines)
