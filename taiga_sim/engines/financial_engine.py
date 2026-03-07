"""Financial simulation engine: P/L, B/S, CF for group and subsidiaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taiga_sim.models.simulation import SimulationState

from taiga_sim.models.financial import (
    BalanceSheet,
    CashFlow,
    FinancialStatements,
    HoldingProfitLoss,
    ProfitLoss,
)
from taiga_sim.models.organization import Company


class FinancialEngine:
    """Computes quarterly financials for each company and the consolidated group."""

    def simulate_company_quarter(
        self,
        company: Company,
        state: SimulationState,
    ) -> FinancialStatements:
        """Simulate one quarter of financials for a single operating company."""
        year = state.year
        quarter = state.quarter
        config = state.config

        # Organic growth (quarterly = annual / 4)
        macro_growth = state.macro.gdp_growth_rate
        organic_growth_annual = 0.04  # default 3-5%
        if state.macro.is_shock_active:
            organic_growth_annual = -0.05
        quarterly_growth = (1 + organic_growth_annual + macro_growth) ** 0.25 - 1

        # Revenue
        new_revenue = company.revenue * (1 + quarterly_growth)

        # P/L
        gross_margin = 1.0 - 0.55  # ~45% gross margin typical
        cogs = new_revenue * 0.55
        depreciation_rate = 0.065  # 6.5% of revenue
        depreciation = new_revenue * depreciation_rate
        personnel_pct = 0.15
        sga_pct = 0.10
        personnel = new_revenue * personnel_pct
        sga = new_revenue * sga_pct

        interest_rate_quarterly = state.macro.interest_rate / 4
        interest = 0.0  # computed from B/S debt below

        pl = ProfitLoss(
            revenue=new_revenue,
            cogs=cogs,
            sga=sga,
            personnel_cost=personnel,
            depreciation=depreciation,
            interest_expense=interest,
            tax_rate=0.30,
        )

        # Update company state
        company.revenue = new_revenue
        company.ebitda = pl.ebitda
        company.operating_margin = (
            pl.operating_income / new_revenue if new_revenue > 0 else 0
        )

        # Simplified B/S
        working_capital_ratio = 0.175  # 17.5% of revenue
        capex_maintenance_ratio = 0.035  # 3.5% of revenue

        bs = BalanceSheet(
            cash=0,  # will be computed in consolidation
            accounts_receivable=new_revenue * 0.15,  # ~15% AR
            inventory=new_revenue * 0.10,
            ppe=company.acquisition_price * 0.3,  # simplified
            goodwill=company.acquisition_price * 0.5,
        )

        # CF
        wc_change = 0.0  # simplified for now
        capex = -new_revenue * capex_maintenance_ratio

        cf = CashFlow(
            net_income=pl.net_income,
            depreciation=depreciation,
            working_capital_change=wc_change,
            capex_maintenance=capex,
        )

        company.fcf = cf.fcf

        return FinancialStatements(year=year, quarter=quarter, pl=pl, bs=bs, cf=cf)

    def simulate_holding_quarter(
        self,
        state: SimulationState,
        subsidiary_results: list[FinancialStatements],
    ) -> HoldingProfitLoss:
        """Simulate one quarter of the holding company P/L."""
        config = state.config
        holding = state.holding

        # Income from subsidiaries
        total_sub_net_income = sum(r.pl.net_income for r in subsidiary_results)
        total_sub_ebitda = sum(r.pl.ebitda for r in subsidiary_results)
        total_sub_revenue = sum(r.pl.revenue for r in subsidiary_results)

        # Holding company income
        dividend_income = max(0, total_sub_net_income * 0.70)  # 70% payout ratio
        mgmt_fee = total_sub_revenue * 0.02  # 2% management fee

        # Holding costs scale down over time
        phase = state.current_phase
        if phase and phase.phase <= 1:
            cost_ratio = 0.60
        elif phase and phase.phase <= 3:
            cost_ratio = 0.30
        else:
            cost_ratio = 0.15

        total_income = dividend_income + mgmt_fee
        hq_personnel = total_income * cost_ratio * 0.60
        hq_admin = total_income * cost_ratio * 0.40

        # Contributions (from operating income, simplified)
        operating_income_estimate = total_income - hq_personnel - hq_admin

        group_fcf = sum(r.cf.fcf for r in subsidiary_results)
        foundation_contribution = 0.0
        if holding.foundation_active and group_fcf > 0:
            foundation_contribution = group_fcf * config.compensation.foundation_fcf_rate

        keshiki_contribution = max(0, operating_income_estimate * config.compensation.keshiki_reserve_rate)

        # Profit sharing pool (only when EV increases above high-water mark)
        profit_sharing = 0.0
        ev = self.compute_enterprise_value(state, total_sub_ebitda)
        if ev > holding.historical_high_ev:
            ev_increase = ev - holding.historical_high_ev
            profit_sharing = ev_increase * config.compensation.profit_sharing_rate / 4  # quarterly

        return HoldingProfitLoss(
            dividend_income=dividend_income,
            management_fee_income=mgmt_fee,
            hq_personnel_cost=hq_personnel,
            hq_admin_cost=hq_admin,
            profit_sharing_contribution=profit_sharing,
            keshiki_reserve_contribution=keshiki_contribution,
            foundation_contribution=foundation_contribution,
        )

    def compute_enterprise_value(
        self,
        state: SimulationState,
        total_ebitda: float,
    ) -> float:
        """Compute enterprise value using EBITDA × multiple."""
        year = state.year
        # EV/EBITDA multiple increases with maturity
        if year <= 1:
            multiple = 4.0
        elif year <= 3:
            multiple = 5.0
        elif year <= 5:
            multiple = 6.0
        elif year <= 7:
            multiple = 7.0
        elif year <= 10:
            multiple = 8.0
        elif year <= 15:
            multiple = 9.0
        else:
            multiple = 10.0

        annualized_ebitda = total_ebitda * 4  # quarterly to annual
        return max(0, annualized_ebitda * multiple)

    def consolidate(
        self,
        state: SimulationState,
        subsidiary_results: list[FinancialStatements],
        holding_pl: HoldingProfitLoss,
    ) -> FinancialStatements:
        """Create consolidated group financial statements."""
        total_revenue = sum(r.pl.revenue for r in subsidiary_results)
        total_ebitda = sum(r.pl.ebitda for r in subsidiary_results)
        total_net_income = sum(r.pl.net_income for r in subsidiary_results)
        total_fcf = sum(r.cf.fcf for r in subsidiary_results)

        # Update state
        ev = self.compute_enterprise_value(state, total_ebitda)
        state.holding.enterprise_value = ev
        if ev > state.holding.historical_high_ev:
            state.holding.historical_high_ev = ev

        # Update reserves
        state.holding.keshiki_reserve += holding_pl.keshiki_reserve_contribution
        state.holding.profit_sharing_pool += holding_pl.profit_sharing_contribution
        if holding_pl.foundation_contribution > 0:
            state.holding.foundation_cumulative += holding_pl.foundation_contribution

        consolidated_pl = ProfitLoss(
            revenue=total_revenue,
            cogs=sum(r.pl.cogs for r in subsidiary_results),
            sga=sum(r.pl.sga for r in subsidiary_results) + holding_pl.hq_admin_cost,
            personnel_cost=sum(r.pl.personnel_cost for r in subsidiary_results) + holding_pl.hq_personnel_cost,
            depreciation=sum(r.pl.depreciation for r in subsidiary_results),
            interest_expense=sum(r.pl.interest_expense for r in subsidiary_results) + holding_pl.interest_expense,
        )

        consolidated_cf = CashFlow(
            net_income=total_net_income + holding_pl.net_income,
            depreciation=consolidated_pl.depreciation,
            working_capital_change=sum(r.cf.working_capital_change for r in subsidiary_results),
            capex_maintenance=sum(r.cf.capex_maintenance for r in subsidiary_results),
            ma_investment=sum(r.cf.ma_investment for r in subsidiary_results),
        )

        return FinancialStatements(
            year=state.year,
            quarter=state.quarter,
            pl=consolidated_pl,
            cf=consolidated_cf,
        )
