"""KPI engine: business evaluation, traffic light system."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taiga_sim.models.simulation import SimulationState

from taiga_sim.models.organization import Company


class KPIEngine:
    """Evaluates business KPIs and manages the traffic light system."""

    def __init__(self, wacc: float = 0.08):
        self.wacc = wacc  # Weighted Average Cost of Capital

    def evaluate_company(self, company: Company, state: SimulationState) -> dict:
        """Evaluate a single company on all 5 KPIs."""
        # 1. ROIC
        invested_capital = company.acquisition_price  # simplified
        annual_nopat = company.ebitda * 4 * (1 - 0.30)  # after tax
        roic = annual_nopat / invested_capital if invested_capital > 0 else 0
        company.roic = roic

        # 2. LTV growth rate (simulated)
        ltv_growth = company.ltv_growth_rate

        # 3. Competitive advantage score (maintained externally)
        cas = company.competitive_advantage_score

        # 4. FCF + reinvestment ratio
        fcf = company.fcf * 4  # annualized
        reinvestment = company.reinvestment_ratio

        # 5. Strategic story progress (qualitative - represented as score)
        strategy_progress = min(100, max(0, cas * 4))  # proxy

        return {
            "roic": roic,
            "roic_vs_wacc": roic - self.wacc,
            "ltv_growth_rate": ltv_growth,
            "competitive_advantage_score": cas,
            "fcf_annual": fcf,
            "reinvestment_ratio": reinvestment,
            "strategy_progress": strategy_progress,
        }

    def update_traffic_light(self, company: Company, state: SimulationState) -> str:
        """Update traffic light signal for a company."""
        roic_above_wacc = company.roic > self.wacc
        ltv_positive = company.ltv_growth_rate >= 0
        cas_stable = company.competitive_advantage_score >= 12.5  # threshold

        # Green: all KPIs good AND not recently flagged by business volatility
        if roic_above_wacc and ltv_positive and cas_stable:
            # Only upgrade to green if not recently set to yellow/red by volatility
            # (give 1-year grace period before clearing signals)
            if company.signal == "green":
                company.consecutive_wacc_miss_years = 0
                return "green"
            elif company.signal == "yellow":
                # KPIs recovered - clear yellow
                company.signal = "green"
                company.consecutive_wacc_miss_years = 0
                company.yellow_since_year = None
                return "green"
            elif company.signal == "red":
                # Red companies need sustained KPI recovery to clear
                # Don't auto-clear red - that requires divestiture review
                return company.signal

        # Check for macro shock freeze
        if state.macro.is_shock_active:
            # Freeze red signal judgment for up to 2 years
            if company.signal == "red" and company.red_since_year is not None:
                return company.signal  # maintain current, don't escalate

        # Yellow conditions
        is_yellow = False
        if not roic_above_wacc:
            is_yellow = True
            company.consecutive_wacc_miss_years += 1
        elif not ltv_positive:
            is_yellow = True  # 2Q consecutive check simplified to annual
        elif not cas_stable:
            is_yellow = True

        if is_yellow and company.signal != "red":
            if company.yellow_since_year is None:
                company.yellow_since_year = state.year
            company.signal = "yellow"

            # Check for escalation to red
            if company.consecutive_wacc_miss_years >= 3 or (
                company.yellow_since_year and (state.year - company.yellow_since_year >= 2)
            ):
                company.signal = "red"
                company.red_since_year = state.year

        return company.signal

    def evaluate_all(self, state: SimulationState) -> dict:
        """Evaluate all companies and return group summary."""
        results: dict[str, object] = {}
        signal_counts: dict[str, int] = {"green": 0, "yellow": 0, "red": 0}

        for company in state.holding.companies:
            kpis = self.evaluate_company(company, state)
            signal = self.update_traffic_light(company, state)
            signal_counts[signal] += 1
            results[company.id] = {
                "kpis": kpis,
                "signal": signal,
            }

        results["_summary"] = {
            "signal_counts": signal_counts,
            "group_avg_roic": (
                sum(c.roic for c in state.holding.companies) / max(1, len(state.holding.companies))
            ),
        }

        return results
