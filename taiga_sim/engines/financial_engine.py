"""Financial simulation engine: P/L, B/S, CF for group and subsidiaries.

Organic growth is modeled per-company using product lifecycle theory:
  Introduction -> Growth -> Maturity -> Decline
Each stage has distinct growth rates, margin profiles, and capex needs.
Group financials are Sum-of-the-Parts of all operating companies.

EV/EBITDA multiple is dynamic, driven by:
  - Group scale (larger = higher multiple)
  - Growth rate (faster growing = premium)
  - Brand strength (builds over time with consistent execution)
  - Portfolio diversification (conglomerate premium vs discount)

Conglomerate premium/discount model (research-based):
  - Berger & Ofek (1995): unrelated diversification discount -13% to -15%
  - Villalonga (2004): related diversification yields premium
  - Research Affiliates (2026): tech conglomerates avg +70% premium
  - Stein (1997): monitoring efficiency decays with # divisions
  - Danaher: operating system yields +600-700bps margin improvement
  - Arte & Larimo (2022): inverted U-shape for diversification-performance
  - Khanna & Palepu (2000): institutional voids create premium in emerging markets
"""

from __future__ import annotations

import math
import random
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
from taiga_sim.models.organization import Company, CompanyType

# Product lifecycle growth profiles (annual rates)
# Calibrated to produce realistic growth trajectories
LIFECYCLE_PROFILES = {
    #                  growth_rate, gross_margin, opex_ratio, capex_ratio, duration_years
    "introduction": (0.30, 0.32, 0.35, 0.08, 3),  # high growth, low margin, high burn
    "growth": (0.12, 0.40, 0.28, 0.06, 5),  # strong growth, improving margins
    "maturity": (0.015, 0.45, 0.22, 0.035, 15),  # stable, high margins, cash cow
    "decline": (-0.04, 0.38, 0.25, 0.02, 10),  # shrinking, margin compression
}

# Company type modifiers on lifecycle
COMPANY_TYPE_MODIFIERS = {
    CompanyType.PRODUCT: {"growth_boost": 0.0, "margin_boost": 0.02, "maturity_years": 18},
    CompanyType.EXPERIENCE: {"growth_boost": 0.10, "margin_boost": -0.03, "maturity_years": 8},
    CompanyType.STRATEGY: {"growth_boost": 0.05, "margin_boost": 0.05, "maturity_years": 12},
    CompanyType.VENTURE: {"growth_boost": 0.20, "margin_boost": -0.05, "maturity_years": 6},
    CompanyType.TERRA: {"growth_boost": -0.02, "margin_boost": 0.03, "maturity_years": 25},
}


class FinancialEngine:
    """Computes quarterly financials for each company and the consolidated group."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def advance_lifecycle(self, company: Company) -> None:
        """Advance a company's product lifecycle stage based on age."""
        company.lifecycle_age += 1
        stage = company.lifecycle_stage
        mod = COMPANY_TYPE_MODIFIERS.get(company.company_type, {})
        maturity_extension = mod.get("maturity_years", 12)

        # Transition rules
        profile = LIFECYCLE_PROFILES[stage]
        base_duration = profile[4]

        if stage == "introduction" and company.lifecycle_age > base_duration:
            company.lifecycle_stage = "growth"
            company.lifecycle_age = 0
        elif stage == "growth" and company.lifecycle_age > base_duration:
            company.lifecycle_stage = "maturity"
            company.lifecycle_age = 0
        elif stage == "maturity" and company.lifecycle_age > maturity_extension:
            company.lifecycle_stage = "decline"
            company.lifecycle_age = 0

    def get_company_growth_rate(self, company: Company, state: SimulationState) -> float:
        """Calculate annual organic growth rate based on lifecycle + macro."""
        stage = company.lifecycle_stage
        base_growth, _, _, _, _ = LIFECYCLE_PROFILES[stage]
        mod = COMPANY_TYPE_MODIFIERS.get(company.company_type, {})
        growth_boost = mod.get("growth_boost", 0.0)

        # For strategic acquisitions in growth phase, use their inherent rate
        # (decaying over time as hypergrowth normalizes)
        if company.revenue_growth_rate > base_growth + growth_boost:
            # Decay high growth rates toward lifecycle baseline over ~5 years
            decay = 0.80  # 20% annual decay toward baseline
            company.revenue_growth_rate = (
                base_growth
                + growth_boost
                + (company.revenue_growth_rate - base_growth - growth_boost) * decay
            )
            effective_growth = company.revenue_growth_rate
        else:
            effective_growth = base_growth + growth_boost

        # Macro overlay
        macro_adj = state.macro.gdp_growth_rate - 0.015  # deviation from baseline
        if state.macro.is_shock_active:
            macro_adj = -0.08  # severe contraction during crisis

        return effective_growth + macro_adj

    def simulate_company_quarter(
        self,
        company: Company,
        state: SimulationState,
    ) -> FinancialStatements:
        """Simulate one quarter of financials for a single operating company."""
        year = state.year
        quarter = state.quarter

        # Get lifecycle-based growth rate
        annual_growth = self.get_company_growth_rate(company, state)
        quarterly_growth = (1 + annual_growth) ** 0.25 - 1

        # Revenue
        new_revenue = company.revenue * (1 + quarterly_growth)

        # Get lifecycle-based cost structure
        stage = company.lifecycle_stage
        _, base_gross_margin, base_opex_ratio, capex_ratio, _ = LIFECYCLE_PROFILES[stage]
        mod = COMPANY_TYPE_MODIFIERS.get(company.company_type, {})
        margin_boost = mod.get("margin_boost", 0.0)

        gross_margin = base_gross_margin + margin_boost
        cogs = new_revenue * (1 - gross_margin)

        # Opex split
        opex_ratio = base_opex_ratio
        personnel_pct = opex_ratio * 0.60
        sga_pct = opex_ratio * 0.40

        depreciation_rate = 0.065 if stage != "decline" else 0.04
        depreciation = new_revenue * depreciation_rate
        personnel = new_revenue * personnel_pct
        sga = new_revenue * sga_pct

        pl = ProfitLoss(
            revenue=new_revenue,
            cogs=cogs,
            sga=sga,
            personnel_cost=personnel,
            depreciation=depreciation,
            interest_expense=0.0,
            tax_rate=0.30,
        )

        # Update company state
        company.revenue = new_revenue
        company.ebitda = pl.ebitda
        company.operating_margin = pl.operating_income / new_revenue if new_revenue > 0 else 0

        # B/S
        bs = BalanceSheet(
            cash=0,
            accounts_receivable=new_revenue * 0.15,
            inventory=new_revenue * 0.10,
            ppe=company.acquisition_price * 0.3,
            goodwill=company.acquisition_price * 0.5,
        )

        # CF
        capex = -new_revenue * capex_ratio
        cf = CashFlow(
            net_income=pl.net_income,
            depreciation=depreciation,
            working_capital_change=0.0,
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

        total_sub_net_income = sum(r.pl.net_income for r in subsidiary_results)
        total_sub_ebitda = sum(r.pl.ebitda for r in subsidiary_results)
        total_sub_revenue = sum(r.pl.revenue for r in subsidiary_results)

        dividend_income = max(0, total_sub_net_income * 0.70)
        mgmt_fee = total_sub_revenue * 0.02

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

        operating_income_estimate = total_income - hq_personnel - hq_admin

        group_fcf = sum(r.cf.fcf for r in subsidiary_results)
        foundation_contribution = 0.0
        if holding.foundation_active and group_fcf > 0:
            foundation_contribution = group_fcf * config.compensation.foundation_fcf_rate

        keshiki_contribution = max(
            0, operating_income_estimate * config.compensation.keshiki_reserve_rate
        )

        profit_sharing = 0.0
        ev = self.compute_enterprise_value(state, total_sub_ebitda)
        if ev > holding.historical_high_ev:
            ev_increase = ev - holding.historical_high_ev
            profit_sharing = ev_increase * config.compensation.profit_sharing_rate / 4

        return HoldingProfitLoss(
            dividend_income=dividend_income,
            management_fee_income=mgmt_fee,
            hq_personnel_cost=hq_personnel,
            hq_admin_cost=hq_admin,
            profit_sharing_contribution=profit_sharing,
            keshiki_reserve_contribution=keshiki_contribution,
            foundation_contribution=foundation_contribution,
        )

    def compute_conglomerate_premium(self, state: SimulationState) -> float:
        """Compute conglomerate premium/discount as a multiplier on EV.

        Research-based model combining:
        1. Diversification type mix (related vs unrelated) - Villalonga (2004)
        2. Operating system maturity (DBS effect) - Danaher case
        3. Monitoring efficiency decay - Stein (1997)
        4. Governance quality - multiple studies
        5. Inverted U-shape for segment count - Arte & Larimo (2022)
        6. Japanese institutional context - Khanna & Palepu (2000)

        Returns: multiplier (e.g. 1.10 = +10% premium, 0.87 = -13% discount)
        """
        cfg = state.config.conglomerate
        holding = state.holding
        companies = holding.companies

        if len(companies) <= 1:
            return 1.0  # no conglomerate effect with single business

        # --- 1. Diversification type: related vs unrelated ---
        # Count unique company types (proxy for diversification breadth)
        type_counts: dict = {}
        for c in companies:
            type_counts[c.company_type] = type_counts.get(c.company_type, 0) + 1
        n_types = len(type_counts)
        n_companies = len(companies)

        # Relatedness ratio: fraction of companies sharing a type with others
        companies_in_clusters = sum(count for count in type_counts.values() if count >= 2)
        relatedness_ratio = companies_in_clusters / n_companies if n_companies > 0 else 0

        # Blend between related premium and unrelated discount
        # High relatedness -> premium; low relatedness -> discount
        diversification_effect = (
            relatedness_ratio * cfg.related_premium
            + (1 - relatedness_ratio) * cfg.unrelated_discount
        )

        # --- 2. Inverted U-shape for segment count (Arte & Larimo 2022) ---
        # Peak at optimal_segment_count, declines on both sides
        segment_deviation = abs(n_types - cfg.optimal_segment_count)
        segment_penalty = -0.02 * (segment_deviation**1.5) / cfg.diversification_curve_width
        diversification_effect += segment_penalty

        # --- 3. PMI capability premium (Danaher DBS effect) ---
        # Mature PMI capability converts discount into premium
        pmi_cap = holding.pmi_capability
        os_premium = pmi_cap * cfg.related_premium * 1.5  # up to +15%

        # --- 4. Monitoring efficiency decay (Stein 1997) ---
        monitoring_penalty = 0.0
        if n_companies > cfg.monitoring_decay_threshold:
            excess = n_companies - cfg.monitoring_decay_threshold
            monitoring_penalty = -excess * cfg.monitoring_decay_rate
            # PMI capability mitigates monitoring decay
            monitoring_penalty *= 1.0 - pmi_cap * 0.6

        # --- 5. Governance quality ---
        gov = holding.governance_quality
        governance_effect = cfg.governance_bonus_max * gov - cfg.governance_penalty_max * (1 - gov)

        # --- 6. Japanese market institutional context ---
        # Weaker institutions in Japan = diversification somewhat more valuable
        japan_context = -cfg.japan_institutional_discount  # positive contribution

        # --- 7. Platform/tech premium for venture-heavy portfolios ---
        venture_ratio = (
            type_counts.get(CompanyType.VENTURE, 0) / n_companies if n_companies > 0 else 0
        )
        platform_premium = 0.0
        if venture_ratio > 0.2 and pmi_cap > 0.5:
            platform_premium = min(
                cfg.platform_premium_max, venture_ratio * pmi_cap * cfg.platform_premium_max
            )

        # --- Combine all effects ---
        total_premium = (
            diversification_effect
            + os_premium
            + monitoring_penalty
            + governance_effect
            + japan_context
            + platform_premium
        )

        # Clamp to reasonable range: -25% discount to +50% premium
        total_premium = float(max(-0.25, min(0.50, total_premium)))

        return 1.0 + total_premium

    def advance_pmi_capability(self, state: SimulationState) -> None:
        """Advance the group's PMI capability (DBS-like).

        Matures based on:
        - Time (experience accumulation)
        - Number of completed PMIs (learning-by-doing)
        - Governance quality improves with scale and track record
        """
        cfg = state.config.conglomerate
        holding = state.holding
        year = state.year

        # Operating system matures over configured years
        if year > 0:
            target_maturity = min(1.0, year / cfg.pmi_capability_years)
            # Smooth convergence: don't jump instantly
            holding.pmi_capability += (target_maturity - holding.pmi_capability) * 0.3

        # Governance improves with track record and scale
        n_companies = len(holding.companies)
        if n_companies >= 3:
            gov_target = min(0.95, 0.5 + n_companies * 0.02 + year * 0.01)
            holding.governance_quality += (gov_target - holding.governance_quality) * 0.2

    def compute_enterprise_value(
        self,
        state: SimulationState,
        total_ebitda: float,
    ) -> float:
        """Compute enterprise value using dynamic EBITDA multiple.

        Multiple is driven by:
        1. Base: starts at 4x, scales with maturity
        2. Growth premium: faster-growing groups get higher multiples
        3. Brand premium: builds over time with consistent execution
        4. Scale premium: larger groups command higher multiples
        5. Conglomerate premium/discount: research-based model

        The conglomerate premium is applied as a multiplier on the final EV,
        following Berger & Ofek (1995) methodology of measuring excess value.
        """
        year = state.year
        holding = state.holding
        annualized_ebitda = total_ebitda * 4

        if annualized_ebitda <= 0:
            return max(0, holding.enterprise_value * 0.95)  # drift down if no earnings

        # 1. Base multiple (time-based foundation, reflecting track record premium)
        if year <= 3:
            base = 4.0 + year * 0.3
        elif year <= 10:
            base = 5.0 + (year - 3) * 0.5
        elif year <= 20:
            base = 8.5 + (year - 10) * 0.5
        else:
            base = 13.5 + (year - 20) * 0.5  # mature platform premium

        # 2. Growth premium: revenue CAGR over last 3 years
        growth_premium = 0.0
        if len(state.annual_revenue_history) >= 3:
            rev_now = state.annual_revenue_history[-1]
            rev_3y = state.annual_revenue_history[-3]
            if rev_3y > 0 and rev_now > rev_3y:
                cagr_3y = (rev_now / rev_3y) ** (1 / 3) - 1
                if cagr_3y > 0.10:
                    growth_premium = min(5.0, cagr_3y * 12)  # up to +5x

        # 3. Brand premium: builds with years of consistent positive growth
        consecutive_growth_years = 0
        for i in range(1, len(state.annual_revenue_history)):
            if state.annual_revenue_history[i] > state.annual_revenue_history[i - 1]:
                consecutive_growth_years += 1
            else:
                consecutive_growth_years = 0
        brand_premium = min(4.0, consecutive_growth_years * 0.20)

        # 4. Scale premium: larger EBITDA -> modestly higher multiple
        ebitda_oku = annualized_ebitda / 1_0000_0000
        scale_premium = 0.0
        if ebitda_oku > 100:
            scale_premium = min(3.0, math.log10(ebitda_oku / 100) * 2.0)

        multiple = base + growth_premium + brand_premium + scale_premium
        # Post-IPO public market premium (higher multiples for listed companies)
        # Comparable: Danaher 30x, Constellation Software 35x, growth conglomerates 25-40x
        max_multiple = 25.0
        if state.holding.is_public or year >= state.config.ipo_target_year:
            max_multiple = 40.0  # public market premium for growth conglomerates
        multiple = max(4.0, min(max_multiple, multiple))

        # Base EV from sum-of-the-parts multiple
        base_ev = annualized_ebitda * multiple

        # 5. Apply conglomerate premium/discount (research-based)
        # This follows Berger & Ofek (1995) "excess value" methodology:
        # EV = SoTP * (1 + premium/discount)
        conglomerate_multiplier = self.compute_conglomerate_premium(state)

        return base_ev * conglomerate_multiplier

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

        ev = self.compute_enterprise_value(state, total_ebitda)
        state.holding.enterprise_value = ev
        if ev > state.holding.historical_high_ev:
            state.holding.historical_high_ev = ev

        state.holding.keshiki_reserve += holding_pl.keshiki_reserve_contribution
        state.holding.profit_sharing_pool += holding_pl.profit_sharing_contribution
        if holding_pl.foundation_contribution > 0:
            state.holding.foundation_cumulative += holding_pl.foundation_contribution

        consolidated_pl = ProfitLoss(
            revenue=total_revenue,
            cogs=sum(r.pl.cogs for r in subsidiary_results),
            sga=sum(r.pl.sga for r in subsidiary_results) + holding_pl.hq_admin_cost,
            personnel_cost=sum(r.pl.personnel_cost for r in subsidiary_results)
            + holding_pl.hq_personnel_cost,
            depreciation=sum(r.pl.depreciation for r in subsidiary_results),
            interest_expense=sum(r.pl.interest_expense for r in subsidiary_results)
            + holding_pl.interest_expense,
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
