"""Simulation runner: orchestrates all engines for a 30-year simulation.

Incorporates realistic failure modes:
- M&A post-acquisition value destruction (KPMG: ~50% fail to create value)
- Business performance volatility and temporary downturns
- New venture failures (corporate: ~60% failure rate)
- Carve-outs/divestitures for underperforming businesses
- Macro shocks (Reinhart & Rogoff: major recession every ~10-15 years)
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

from taiga_sim.engines.compensation_engine import CompensationEngine
from taiga_sim.engines.crisis_engine import CrisisEngine
from taiga_sim.engines.financial_engine import FinancialEngine
from taiga_sim.engines.hr_engine import HREngine
from taiga_sim.engines.investor_engine import InvestorEngine
from taiga_sim.engines.kpi_engine import KPIEngine
from taiga_sim.engines.ma_engine import MAEngine
from taiga_sim.models.simulation import SimulationConfig, SimulationState
from taiga_sim.utils.formatters import fmt_jpy, fmt_table


@dataclass
class AnnualReport:
    """Summary of one year's simulation results."""

    year: int
    phase: str
    revenue: float  # annualized
    ebitda: float
    enterprise_value: float
    fcf: float
    headcount: int
    num_companies: int
    founder_ownership_pct: float
    seed_investor_moic: float
    seed_investor_irr: float
    keshiki_reserve: float
    foundation_cumulative: float
    signal_counts: dict = field(default_factory=dict)
    crisis_active: bool = False
    ma_events_this_year: int = 0
    divestitures_this_year: int = 0
    # Conglomerate premium metrics
    conglomerate_premium_pct: float = 0.0  # e.g. +10% or -13%
    pmi_capability: float = 0.0
    governance_quality: float = 0.5
    n_company_types: int = 0


class SimulationRunner:
    """Orchestrates the full 30-year simulation."""

    def __init__(
        self,
        config: SimulationConfig | None = None,
        seed: int = 42,
    ):
        self.config = config or SimulationConfig()
        self.rng = random.Random(seed)

        # Initialize engines
        self.financial = FinancialEngine(rng=self.rng)
        self.ma = MAEngine(rng=self.rng)
        self.compensation = CompensationEngine()
        self.hr = HREngine(rng=self.rng)
        self.kpi = KPIEngine()
        self.crisis = CrisisEngine(rng=self.rng)
        self.investor = InvestorEngine()

        # State
        self.state = SimulationState(config=self.config, macro=self.config.macro)
        self.annual_reports: list[AnnualReport] = []

    def initialize(self) -> None:
        """Set up Year 0: seed funding and founding team."""
        state = self.state
        state.year = 0
        state.quarter = 1

        holding = state.holding
        holding.enterprise_value = self.config.seed_funding / self.config.initial_equity_dilution
        holding.historical_high_ev = holding.enterprise_value

        self.hr.initialize_founding_team(state)
        self.investor.update_dilution(state)

    def _apply_business_volatility(self, state: SimulationState) -> None:
        """Apply random performance shocks to individual businesses.

        Research basis:
        - ~15-20% of portfolio companies underperform in any year (BCG)
        - New ventures (lifecycle_stage=introduction) have ~60% failure rate
          over their lifetime (CB Insights corporate venture data)
        - Mature businesses can have temporary downturns (-10 to -30% EBITDA)
        """
        for company in list(state.holding.companies):
            # New venture failure check (introduction stage)
            if company.lifecycle_stage == "introduction":
                # 15% annual failure probability -> ~60% cumulative over 3+ years
                if self.rng.random() < 0.15:
                    company.ebitda *= 0.3  # severe underperformance
                    company.revenue *= 0.7
                    if self.rng.random() < 0.40:
                        # Complete failure -> mark for divestiture
                        company.signal = "red"
                        company.red_since_year = state.year
                        company.consecutive_wacc_miss_years = 3

            # General performance volatility (all stages)
            volatility_roll = self.rng.random()
            if volatility_roll < 0.08:
                # 8% chance of significant downturn (-15 to -30%)
                shock = self.rng.uniform(-0.30, -0.15)
                company.ebitda *= (1 + shock)
                company.revenue *= (1 + shock * 0.5)  # revenue less volatile
                # Escalate signal: green -> yellow -> red
                if company.signal == "yellow":
                    company.signal = "red"
                    company.red_since_year = state.year
                elif company.signal == "green":
                    company.signal = "yellow"
                    company.yellow_since_year = state.year
            elif volatility_roll < 0.15:
                # 7% chance of mild downturn (-5 to -15%)
                shock = self.rng.uniform(-0.15, -0.05)
                company.ebitda *= (1 + shock)
                # Mild downturns can push to yellow
                if company.signal == "green" and self.rng.random() < 0.30:
                    company.signal = "yellow"
                    company.yellow_since_year = state.year
            else:
                # Good year: recover from yellow back to green (50% chance)
                if company.signal == "yellow" and self.rng.random() < 0.50:
                    company.signal = "green"
                    company.yellow_since_year = None

            # Declining-stage companies have higher chance of degrading signals
            if company.lifecycle_stage == "decline":
                if company.signal == "green" and self.rng.random() < 0.12:
                    company.signal = "yellow"
                    company.yellow_since_year = state.year
                elif company.signal == "yellow" and self.rng.random() < 0.15:
                    company.signal = "red"
                    company.red_since_year = state.year

    def _execute_divestitures(self, state: SimulationState) -> int:
        """Divest red-signal businesses (portfolio rebalancing).

        Research basis:
        - Kaplan & Weisbach (1992): ~44% of acquisitions are eventually divested
        - Average time to divestiture: 5-7 years for failed deals
        - Carve-outs can recover 40-80% of acquisition price
        """
        divested = 0
        for company in list(state.holding.companies):
            if company.signal != "red":
                continue
            if company.red_since_year is None:
                continue

            years_in_red = state.year - company.red_since_year
            if years_in_red < 2:
                continue  # give turnaround time

            # Probability of divestiture increases with time in red
            divest_prob = min(0.80, 0.30 + years_in_red * 0.15)
            if self.rng.random() < divest_prob:
                # Carve-out: recover partial value
                recovery_rate = self.rng.uniform(0.40, 0.80)
                recovery_value = company.acquisition_price * recovery_rate

                state.holding.companies.remove(company)
                state.ma_events.append({
                    "year": state.year,
                    "quarter": 1,
                    "company": company.name,
                    "type": "divestiture",
                    "recovery_value": recovery_value,
                    "acquisition_price": company.acquisition_price,
                    "recovery_rate": recovery_rate,
                })
                divested += 1

        return divested

    def _post_acquisition_value_check(self, state: SimulationState) -> None:
        """Check for post-acquisition value destruction.

        Research basis:
        - KPMG: ~50% of M&As fail to create value
        - McKinsey: 60-70% fail to achieve projected synergies
        - Modeled as: some acquisitions have persistent underperformance
          in years 2-4 post-acquisition
        """
        for company in state.holding.companies:
            years_since = state.year - company.acquired_year
            if years_since < 2 or years_since > 4:
                continue
            if company.pmi_phase >= 4:
                continue

            # 25% of in-PMI acquisitions experience value destruction
            if self.rng.random() < 0.25:
                destruction = self.rng.uniform(0.05, 0.20)
                company.ebitda *= (1 - destruction)

    def run_year(self, year: int) -> AnnualReport:
        """Run one full year of simulation (4 quarters)."""
        state = self.state
        state.year = year

        phase = state.current_phase
        phase_name = phase.name if phase else "unknown"

        if phase and phase.phase >= 3:
            state.holding.foundation_active = True

        # --- Annual events ---

        # 1. Crisis check
        crisis_event = None
        if year > 0:
            crisis_event = self.crisis.check_for_shock(state)

        # 2. M&A pipeline (phase-based limits)
        ma_count = 0
        if year >= 1:
            _, max_acq, _ = self.ma._phase_params(phase.phase if phase else 1)
            targets = self.ma.generate_pipeline(state)
            for target in targets:
                if self.ma.evaluate_target(target, state):
                    self.ma.execute_acquisition(target, state)
                    ma_count += 1
                    if ma_count >= max_acq:
                        break

        # 3. Business volatility and failures
        if year >= 1:
            self._apply_business_volatility(state)
            self._post_acquisition_value_check(state)

        # 4. Divestitures (carve-outs of red-signal businesses)
        divest_count = 0
        if year >= 3:
            divest_count = self._execute_divestitures(state)

        # 5. Hiring and turnover
        if year >= 1:
            self.hr.simulate_hiring(state)
            self.hr.simulate_turnover(state)

        # 6. Evaluation
        self.hr.evaluate_members(state)
        self.hr.assign_units(state)

        # --- Advance PMI capability (DBS-like) ---
        self.financial.advance_pmi_capability(state)

        # --- Quarterly simulation ---
        annual_revenue = 0.0
        annual_ebitda = 0.0
        annual_fcf = 0.0

        for q in range(1, 5):
            state.quarter = q

            pmi_cap = state.holding.pmi_capability
            pmi_margin = state.config.conglomerate.pmi_margin_improvement
            for company in state.holding.companies:
                quarters_since = (year - company.acquired_year) * 4 + q
                self.ma.advance_pmi(
                    company, quarters_since,
                    pmi_capability=pmi_cap,
                    pmi_margin_improvement=pmi_margin,
                )

            if q == 1:
                for company in state.holding.companies:
                    self.financial.advance_lifecycle(company)

            sub_results = []
            for company in state.holding.companies:
                result = self.financial.simulate_company_quarter(company, state)
                sub_results.append(result)

            if sub_results:
                holding_pl = self.financial.simulate_holding_quarter(state, sub_results)
                consolidated = self.financial.consolidate(state, sub_results, holding_pl)

                annual_revenue += consolidated.pl.revenue
                annual_ebitda += consolidated.pl.ebitda
                annual_fcf += consolidated.cf.fcf

            synergy = self.ma.compute_synergies(state)
            annual_ebitda += synergy / 4

            self.crisis.advance_crisis(state)

        # --- Post-quarter processing ---

        kpi_results = self.kpi.evaluate_all(state)
        signal_counts = kpi_results.get("_summary", {}).get("signal_counts", {})

        if year >= 1:
            self.compensation.calculate_all(state)

        self.investor.update_dilution(state)
        seed_return = self.investor.calculate_seed_investor_return(state)

        if crisis_event:
            self.crisis.apply_mechanisms(state, crisis_event)

        if state.holding.companies:
            total_ebitda_q = sum(c.ebitda for c in state.holding.companies)
            ev = self.financial.compute_enterprise_value(state, total_ebitda_q)
            state.holding.enterprise_value = ev
            if ev > state.holding.historical_high_ev:
                state.holding.historical_high_ev = ev

        state.annual_ev_history.append(state.holding.enterprise_value)
        state.annual_revenue_history.append(annual_revenue)
        state.annual_ebitda_history.append(annual_ebitda)
        state.annual_fcf_history.append(annual_fcf)

        # Compute conglomerate premium for reporting
        cong_multiplier = self.financial.compute_conglomerate_premium(state)
        cong_premium_pct = (cong_multiplier - 1.0) * 100  # as percentage
        n_types = len(set(c.company_type for c in state.holding.companies)) if state.holding.companies else 0

        report = AnnualReport(
            year=year,
            phase=phase_name,
            revenue=annual_revenue,
            ebitda=annual_ebitda,
            enterprise_value=state.holding.enterprise_value,
            fcf=annual_fcf,
            headcount=len(state.holding.members),
            num_companies=len(state.holding.companies),
            founder_ownership_pct=state.holding.founder_ownership_pct,
            seed_investor_moic=seed_return.moic,
            seed_investor_irr=seed_return.irr,
            keshiki_reserve=state.holding.keshiki_reserve,
            foundation_cumulative=state.holding.foundation_cumulative,
            signal_counts=signal_counts,
            crisis_active=state.macro.is_shock_active,
            ma_events_this_year=ma_count,
            divestitures_this_year=divest_count,
            conglomerate_premium_pct=round(cong_premium_pct, 2),
            pmi_capability=round(state.holding.pmi_capability, 3),
            governance_quality=round(state.holding.governance_quality, 3),
            n_company_types=n_types,
        )
        self.annual_reports.append(report)
        return report

    def run(self, years: int | None = None) -> list[AnnualReport]:
        """Run the full simulation."""
        total = years or self.config.total_years
        self.initialize()
        for year in range(0, total + 1):
            self.run_year(year)
        return self.annual_reports

    def export_results(self, output_path: str = "data/simulation_results.json") -> str:
        """Export simulation results to JSON."""
        results = []
        for r in self.annual_reports:
            results.append({
                "year": r.year,
                "phase": r.phase,
                "revenue_jpy": r.revenue,
                "revenue_display": fmt_jpy(r.revenue),
                "ebitda_jpy": r.ebitda,
                "ebitda_display": fmt_jpy(r.ebitda),
                "ev_jpy": r.enterprise_value,
                "ev_display": fmt_jpy(r.enterprise_value),
                "fcf_jpy": r.fcf,
                "headcount": r.headcount,
                "num_companies": r.num_companies,
                "founder_ownership_pct": round(r.founder_ownership_pct * 100, 2),
                "seed_moic": round(r.seed_investor_moic, 1),
                "seed_irr_pct": round(r.seed_investor_irr * 100, 1),
                "keshiki_reserve": fmt_jpy(r.keshiki_reserve),
                "foundation_cumulative": fmt_jpy(r.foundation_cumulative),
                "signals": r.signal_counts,
                "crisis_active": r.crisis_active,
                "ma_events": r.ma_events_this_year,
                "divestitures": r.divestitures_this_year,
                "conglomerate_premium_pct": r.conglomerate_premium_pct,
                "pmi_capability": r.pmi_capability,
                "governance_quality": r.governance_quality,
                "n_company_types": r.n_company_types,
            })

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        return str(path)

    def print_summary(self) -> str:
        """Print a human-readable summary of the simulation."""
        lines = []
        lines.append("=" * 110)
        lines.append("TAIGA CAPITAL GROUP - 30年シミュレーション結果")
        lines.append("=" * 110)
        lines.append(
            f"{'Year':>4} {'Phase':<8} {'売上':>10} {'EBITDA':>10} "
            f"{'EV':>10} {'社員':>5} {'事業':>4} {'売却':>3} {'創業者%':>7} "
            f"{'MOIC':>8} {'IRR%':>6} {'CP%':>6} {'OS':>5} {'危機':>3}"
        )
        lines.append("-" * 120)

        for r in self.annual_reports:
            crisis_mark = "●" if r.crisis_active else ""
            divest_mark = f"({r.divestitures_this_year})" if r.divestitures_this_year > 0 else ""
            cp_sign = "+" if r.conglomerate_premium_pct >= 0 else ""
            lines.append(
                f"{r.year:>4} {r.phase:<8} "
                f"{fmt_table(r.revenue):>10} "
                f"{fmt_table(r.ebitda):>10} "
                f"{fmt_table(r.enterprise_value):>10} "
                f"{r.headcount:>5} {r.num_companies:>4} {divest_mark:>3} "
                f"{r.founder_ownership_pct * 100:>6.1f}% "
                f"{r.seed_investor_moic:>8.1f} "
                f"{r.seed_investor_irr * 100:>5.1f}% "
                f"{cp_sign}{r.conglomerate_premium_pct:>4.1f}% "
                f"{r.pmi_capability:>4.2f} "
                f"{crisis_mark:>3}"
            )

        lines.append("=" * 110)

        if self.annual_reports:
            final = self.annual_reports[-1]
            lines.append(f"\n【最終年 Year {final.year} サマリー】")
            lines.append(f"  売上高:       {fmt_jpy(final.revenue)}")
            lines.append(f"  EBITDA:       {fmt_jpy(final.ebitda)}")
            lines.append(f"  企業価値:     {fmt_jpy(final.enterprise_value)}")
            lines.append(f"  社員数:       {final.headcount:,}名")
            lines.append(f"  事業会社数:   {final.num_companies}社")
            lines.append(f"  創業者持分:   {final.founder_ownership_pct * 100:.1f}%")
            lines.append(f"  投資家MOIC:   {final.seed_investor_moic:,.1f}x")
            lines.append(f"  投資家IRR:    {final.seed_investor_irr * 100:.1f}%")
            lines.append(f"  景色積立金:   {fmt_jpy(final.keshiki_reserve)}")
            lines.append(f"  財団累計拠出: {fmt_jpy(final.foundation_cumulative)}")

            # Count total divestitures
            total_divest = sum(r.divestitures_this_year for r in self.annual_reports)
            total_ma = sum(r.ma_events_this_year for r in self.annual_reports)
            lines.append(f"  累計M&A:      {total_ma}件")
            lines.append(f"  累計売却:     {total_divest}件")
            lines.append(f"  コングロマリットP/D: {'+' if final.conglomerate_premium_pct >= 0 else ''}{final.conglomerate_premium_pct:.1f}%")
            lines.append(f"  PMI Capability:      {final.pmi_capability:.1%}")
            lines.append(f"  ガバナンス品質:      {final.governance_quality:.1%}")

        return "\n".join(lines)
