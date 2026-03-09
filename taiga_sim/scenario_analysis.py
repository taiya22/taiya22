"""Scenario analysis: Base / Bull / Bear comparison.

Runs the 30-year simulation under three macro assumptions and
produces a side-by-side comparison table.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from taiga_sim.engines.simulation_runner import AnnualReport, SimulationRunner
from taiga_sim.models.simulation import SimulationConfig
from taiga_sim.utils.formatters import fmt_jpy


# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

def _make_bear_config(base: SimulationConfig) -> SimulationConfig:
    """Bear case: prolonged low growth, tighter credit, more crises."""
    cfg = deepcopy(base)
    cfg.macro.gdp_growth_rate = 0.005       # 0.5% (stagnation)
    cfg.macro.interest_rate = 0.04           # 4% (tighter)
    cfg.macro.shock_probability = 0.10       # 10%/yr
    cfg.macro.shock_ev_decline = -0.40       # -40%
    cfg.macro.inflation_rate = 0.035         # 3.5%
    cfg.ma.target_ev_ebitda = 5.5            # more expensive multiples
    cfg.ma.max_leverage = 2.5                # tighter lending
    cfg.ma.group_max_leverage = 2.0
    cfg.conglomerate.pmi_margin_improvement = 0.045  # harder to extract value
    return cfg


def _make_bull_config(base: SimulationConfig) -> SimulationConfig:
    """Bull case: strong growth, easy credit, favourable markets."""
    cfg = deepcopy(base)
    cfg.macro.gdp_growth_rate = 0.030        # 3.0%
    cfg.macro.interest_rate = 0.01            # 1%
    cfg.macro.shock_probability = 0.03        # 3%/yr
    cfg.macro.shock_ev_decline = -0.20        # -20%
    cfg.macro.inflation_rate = 0.015          # 1.5%
    cfg.ma.target_ev_ebitda = 3.5             # cheaper multiples
    cfg.ma.max_leverage = 3.5                 # easier financing
    cfg.ma.group_max_leverage = 3.0
    cfg.conglomerate.pmi_margin_improvement = 0.080  # stronger synergy capture
    return cfg


SCENARIO_BUILDERS = {
    "bear": _make_bear_config,
    "base": lambda cfg: deepcopy(cfg),
    "bull": _make_bull_config,
}


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class ScenarioResult:
    """Final-year metrics for one scenario."""

    name: str
    reports: list[AnnualReport]

    # Convenience accessors ------------------------------------------------
    @property
    def final(self) -> AnnualReport:
        return self.reports[-1]

    @property
    def revenue(self) -> float:
        return self.final.revenue

    @property
    def ebitda(self) -> float:
        return self.final.ebitda

    @property
    def ev(self) -> float:
        return self.final.enterprise_value

    @property
    def moic(self) -> float:
        return self.final.seed_investor_moic

    @property
    def irr(self) -> float:
        return self.final.seed_investor_irr


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_scenarios(
    base_config: SimulationConfig | None = None,
    years: int = 30,
    seed: int = 42,
) -> dict[str, ScenarioResult]:
    """Run Base / Bull / Bear scenarios and return results keyed by name."""
    base_config = base_config or SimulationConfig()
    results: dict[str, ScenarioResult] = {}

    for name in ("bear", "base", "bull"):
        cfg = SCENARIO_BUILDERS[name](base_config)
        runner = SimulationRunner(config=cfg, seed=seed)
        reports = runner.run(years=years)
        results[name] = ScenarioResult(name=name, reports=reports)

    return results


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def format_comparison_table(results: dict[str, ScenarioResult]) -> str:
    """Pretty-print a side-by-side comparison table."""
    bear, base, bull = results["bear"], results["base"], results["bull"]

    def _pct(v: float) -> str:
        return f"{v * 100:.1f}%"

    rows = [
        ("売上高",           fmt_jpy(bear.revenue),  fmt_jpy(base.revenue),  fmt_jpy(bull.revenue)),
        ("EBITDA",           fmt_jpy(bear.ebitda),   fmt_jpy(base.ebitda),   fmt_jpy(bull.ebitda)),
        ("企業価値 (EV)",    fmt_jpy(bear.ev),       fmt_jpy(base.ev),       fmt_jpy(bull.ev)),
        ("事業会社数",       f"{bear.final.num_companies}社", f"{base.final.num_companies}社", f"{bull.final.num_companies}社"),
        ("社員数",           f"{bear.final.headcount:,}名",   f"{base.final.headcount:,}名",   f"{bull.final.headcount:,}名"),
        ("創業者持分",       _pct(bear.final.founder_ownership_pct), _pct(base.final.founder_ownership_pct), _pct(bull.final.founder_ownership_pct)),
        ("投資家 MOIC",      f"{bear.moic:,.1f}x",   f"{base.moic:,.1f}x",   f"{bull.moic:,.1f}x"),
        ("投資家 IRR",       _pct(bear.irr),          _pct(base.irr),          _pct(bull.irr)),
        ("PMI Capability",   _pct(bear.final.pmi_capability), _pct(base.final.pmi_capability), _pct(bull.final.pmi_capability)),
        ("CP%",              f"{bear.final.conglomerate_premium_pct:+.1f}%", f"{base.final.conglomerate_premium_pct:+.1f}%", f"{bull.final.conglomerate_premium_pct:+.1f}%"),
    ]

    # Count crises
    for label, sc in [("危機発生回数", None)]:
        bear_c = sum(1 for r in bear.reports if r.crisis_active)
        base_c = sum(1 for r in base.reports if r.crisis_active)
        bull_c = sum(1 for r in bull.reports if r.crisis_active)
        rows.append(("危機発生年数", f"{bear_c}年", f"{base_c}年", f"{bull_c}年"))

    w_label, w_col = 20, 18
    sep = "-" * (w_label + w_col * 3 + 10)

    lines = []
    lines.append("=" * len(sep))
    lines.append("シナリオ分析: Bear / Base / Bull  (30年)")
    lines.append("=" * len(sep))
    lines.append(f"{'指標':<{w_label}}  {'Bear':>{w_col}}  {'Base':>{w_col}}  {'Bull':>{w_col}}")
    lines.append(sep)
    for label, b, m, u in rows:
        lines.append(f"{label:<{w_label}}  {b:>{w_col}}  {m:>{w_col}}  {u:>{w_col}}")
    lines.append(sep)

    return "\n".join(lines)


def format_yearly_comparison(
    results: dict[str, ScenarioResult],
    metric: str = "ev",
) -> str:
    """Year-by-year comparison for a single metric."""
    bear, base, bull = results["bear"], results["base"], results["bull"]

    getter = {
        "ev": lambda r: r.enterprise_value,
        "revenue": lambda r: r.revenue,
        "ebitda": lambda r: r.ebitda,
        "moic": lambda r: r.seed_investor_moic,
    }[metric]

    formatter = {
        "ev": fmt_jpy,
        "revenue": fmt_jpy,
        "ebitda": fmt_jpy,
        "moic": lambda v: f"{v:,.1f}x",
    }[metric]

    lines = [f"\n{'Year':>4}  {'Bear':>14}  {'Base':>14}  {'Bull':>14}"]
    lines.append("-" * 54)

    max_len = min(len(bear.reports), len(base.reports), len(bull.reports))
    for i in range(max_len):
        yr = bear.reports[i].year
        lines.append(
            f"{yr:>4}  "
            f"{formatter(getter(bear.reports[i])):>14}  "
            f"{formatter(getter(base.reports[i])):>14}  "
            f"{formatter(getter(bull.reports[i])):>14}"
        )

    return "\n".join(lines)
