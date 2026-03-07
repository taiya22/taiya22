"""Simulation runner: orchestrates all engines for a 30-year simulation."""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

from taiga_sim.engines.compensation_engine import CompensationEngine
from taiga_sim.engines.crisis_engine import CrisisEngine
from taiga_sim.engines.financial_engine import FinancialEngine
from taiga_sim.engines.hr_engine import HREngine
from taiga_sim.engines.investor_engine import InvestorEngine
from taiga_sim.engines.kpi_engine import KPIEngine
from taiga_sim.engines.ma_engine import MAEngine
from taiga_sim.models.simulation import SimulationConfig, SimulationState


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
        self.financial = FinancialEngine()
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

        # Seed funding
        holding = state.holding
        holding.enterprise_value = self.config.seed_funding / self.config.initial_equity_dilution
        holding.historical_high_ev = holding.enterprise_value

        # Founding team
        self.hr.initialize_founding_team(state)

        # Initial cash
        # (tracked conceptually; actual B/S is per-company)

        # Investor dilution
        self.investor.update_dilution(state)

    def run_year(self, year: int) -> AnnualReport:
        """Run one full year of simulation (4 quarters)."""
        state = self.state
        state.year = year

        # Determine phase
        phase = state.current_phase
        phase_name = phase.name if phase else "unknown"

        # Activate foundation in Phase 3+
        if phase and phase.phase >= 3:
            state.holding.foundation_active = True

        # --- Annual events (once per year) ---

        # 1. Crisis check
        crisis_event = None
        if year > 0:
            crisis_event = self.crisis.check_for_shock(state)

        # 2. M&A pipeline (annual)
        ma_count = 0
        if year >= 1:
            targets = self.ma.generate_pipeline(state)
            for target in targets:
                if self.ma.evaluate_target(target, state):
                    self.ma.execute_acquisition(target, state)
                    ma_count += 1
                    if ma_count >= self.config.ma.annual_acquisitions:
                        break

        # 3. Hiring and turnover
        if year >= 1:
            self.hr.simulate_hiring(state)
            self.hr.simulate_turnover(state)

        # 4. Evaluation (annual)
        self.hr.evaluate_members(state)
        self.hr.assign_units(state)

        # --- Quarterly simulation ---
        annual_revenue = 0.0
        annual_ebitda = 0.0
        annual_fcf = 0.0

        for q in range(1, 5):
            state.quarter = q

            # PMI advancement
            for company in state.holding.companies:
                quarters_since = (year - company.acquired_year) * 4 + q
                self.ma.advance_pmi(company, quarters_since)

            # Financial simulation per company
            sub_results = []
            for company in state.holding.companies:
                result = self.financial.simulate_company_quarter(company, state)
                sub_results.append(result)

            if sub_results:
                # Holding company P/L
                holding_pl = self.financial.simulate_holding_quarter(state, sub_results)

                # Consolidation
                consolidated = self.financial.consolidate(state, sub_results, holding_pl)

                annual_revenue += consolidated.pl.revenue
                annual_ebitda += consolidated.pl.ebitda
                annual_fcf += consolidated.cf.fcf

            # Synergies
            synergy = self.ma.compute_synergies(state)
            annual_ebitda += synergy / 4  # quarterly synergy

            # Crisis progression
            self.crisis.advance_crisis(state)

        # --- Post-quarter annual processing ---

        # KPI evaluation
        kpi_results = self.kpi.evaluate_all(state)
        signal_counts = kpi_results.get("_summary", {}).get("signal_counts", {})

        # Compensation
        if year >= 1:
            self.compensation.calculate_all(state)

        # Investor returns
        self.investor.update_dilution(state)
        seed_return = self.investor.calculate_seed_investor_return(state)

        # Apply crisis mechanisms if active
        if crisis_event:
            self.crisis.apply_mechanisms(state, crisis_event)

        # Update EV based on annualized EBITDA
        if state.holding.companies:
            total_ebitda_q = sum(c.ebitda for c in state.holding.companies)
            ev = self.financial.compute_enterprise_value(state, total_ebitda_q)
            state.holding.enterprise_value = ev
            if ev > state.holding.historical_high_ev:
                state.holding.historical_high_ev = ev

        # Track history
        state.annual_ev_history.append(state.holding.enterprise_value)
        state.annual_revenue_history.append(annual_revenue)
        state.annual_ebitda_history.append(annual_ebitda)
        state.annual_fcf_history.append(annual_fcf)

        # Build annual report
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
        for report in self.annual_reports:
            results.append({
                "year": report.year,
                "phase": report.phase,
                "revenue_jpy": report.revenue,
                "revenue_oku": round(report.revenue / 1_0000_0000, 1),
                "ebitda_jpy": report.ebitda,
                "ebitda_oku": round(report.ebitda / 1_0000_0000, 1),
                "ev_jpy": report.enterprise_value,
                "ev_oku": round(report.enterprise_value / 1_0000_0000, 1),
                "fcf_jpy": report.fcf,
                "headcount": report.headcount,
                "num_companies": report.num_companies,
                "founder_ownership_pct": round(report.founder_ownership_pct * 100, 2),
                "seed_moic": round(report.seed_investor_moic, 1),
                "seed_irr_pct": round(report.seed_investor_irr * 100, 1),
                "keshiki_reserve_oku": round(report.keshiki_reserve / 1_0000_0000, 1),
                "foundation_oku": round(report.foundation_cumulative / 1_0000_0000, 1),
                "signals": report.signal_counts,
                "crisis_active": report.crisis_active,
                "ma_events": report.ma_events_this_year,
            })

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        return str(path)

    def print_summary(self) -> str:
        """Print a human-readable summary of the simulation."""
        lines = []
        lines.append("=" * 90)
        lines.append("TAIGA CAPITAL GROUP - 30年シミュレーション結果")
        lines.append("=" * 90)
        lines.append(
            f"{'Year':>5} {'Phase':<10} {'売上(億)':>10} {'EBITDA(億)':>10} "
            f"{'EV(億)':>10} {'社員数':>6} {'事業数':>6} {'創業者%':>8} "
            f"{'MOIC':>6} {'IRR%':>6} {'危機':>4}"
        )
        lines.append("-" * 90)

        for r in self.annual_reports:
            crisis_mark = "●" if r.crisis_active else ""
            lines.append(
                f"{r.year:>5} {r.phase:<10} "
                f"{r.revenue / 1_0000_0000:>10.1f} "
                f"{r.ebitda / 1_0000_0000:>10.1f} "
                f"{r.enterprise_value / 1_0000_0000:>10.1f} "
                f"{r.headcount:>6} {r.num_companies:>6} "
                f"{r.founder_ownership_pct * 100:>7.1f}% "
                f"{r.seed_investor_moic:>6.1f} "
                f"{r.seed_investor_irr * 100:>5.1f}% "
                f"{crisis_mark:>4}"
            )

        lines.append("=" * 90)

        # Final summary
        if self.annual_reports:
            final = self.annual_reports[-1]
            lines.append(f"\n【最終年 Year {final.year} サマリー】")
            lines.append(f"  売上高:      {final.revenue / 1_0000_0000:,.0f}億円")
            lines.append(f"  EBITDA:      {final.ebitda / 1_0000_0000:,.0f}億円")
            lines.append(f"  企業価値:    {final.enterprise_value / 1_0000_0000:,.0f}億円")
            lines.append(f"  社員数:      {final.headcount:,}名")
            lines.append(f"  事業会社数:  {final.num_companies}社")
            lines.append(f"  創業者持分:  {final.founder_ownership_pct * 100:.1f}%")
            lines.append(f"  初期投資家MOIC: {final.seed_investor_moic:.1f}x")
            lines.append(f"  初期投資家IRR:  {final.seed_investor_irr * 100:.1f}%")
            lines.append(f"  景色積立金:  {final.keshiki_reserve / 1_0000_0000:,.0f}億円")
            lines.append(f"  財団累計拠出: {final.foundation_cumulative / 1_0000_0000:,.0f}億円")

        return "\n".join(lines)
