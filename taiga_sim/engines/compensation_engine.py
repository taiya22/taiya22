"""Compensation engine: True Ownership Program 3-layer calculation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taiga_sim.models.simulation import SimulationState

from taiga_sim.models.compensation import (
    CompensationLayer1,
    CompensationLayer2,
    CompensationLayer3,
    TotalCompensation,
)
from taiga_sim.models.organization import Member


class CompensationEngine:
    """Calculates compensation for all members each year."""

    def calculate_layer1(
        self,
        member: Member,
        group_operating_income: float,
        config_bonus_pool_rate: float,
    ) -> CompensationLayer1:
        """Calculate base salary + annual bonus."""
        bonus_pool = max(0, group_operating_income * config_bonus_pool_rate)

        # Individual bonus = pool share * coefficient
        # Pool share is simplified as pool / headcount (weighted by role later)
        layer1 = CompensationLayer1(
            base_salary=member.base_salary,
            bonus_pool_rate=config_bonus_pool_rate,
            bonus_pool_total=bonus_pool,
            individual_coefficient=member.evaluation_coefficient,
            bonus=0.0,  # set below
        )
        return layer1

    def calculate_layer2(
        self,
        member: Member,
        ev_increase: float,
        sharing_rate: float,
        tier: str,  # "executive", "senior", "middle_junior"
        tier_headcount: int,
    ) -> CompensationLayer2:
        """Calculate profit sharing (fund carry equivalent)."""
        if ev_increase <= 0:
            return CompensationLayer2(ev_increase=0, sharing_rate=sharing_rate)

        pool = ev_increase * sharing_rate

        # Tier allocation
        tier_rates = {
            "executive": 0.40,
            "senior": 0.30,
            "middle_junior": 0.20,
            "special": 0.10,
        }
        tier_rate = tier_rates.get(tier, 0.20)
        tier_pool = pool * tier_rate
        individual_share = tier_pool / max(1, tier_headcount)

        # 3-year vesting
        year1 = individual_share * 0.33
        year2 = 0.0  # from prior year's grant
        year3 = 0.0  # from 2 years ago grant

        # Check member's unvested shares
        if len(member.unvested_profit_share) >= 1:
            year2 = member.unvested_profit_share[-1] * 0.33
        if len(member.unvested_profit_share) >= 2:
            year3 = member.unvested_profit_share[-2] * 0.34

        layer2 = CompensationLayer2(
            ev_increase=ev_increase,
            sharing_rate=sharing_rate,
            pool_total=pool,
            individual_share=individual_share,
            year1_vested=year1,
            year2_vested=year2,
            year3_vested=year3,
        )

        # Track unvested
        member.unvested_profit_share.append(individual_share)
        if len(member.unvested_profit_share) > 3:
            member.unvested_profit_share.pop(0)

        return layer2

    def calculate_layer3(
        self,
        member: Member,
        current_ev: float,
        initial_ev_at_purchase: float,
        group_cash_yield: float,
    ) -> CompensationLayer3:
        """Calculate self-investment (co-invest) returns."""
        if member.self_investment <= 0:
            return CompensationLayer3()

        # Valuation grows proportionally to EV
        growth_factor = current_ev / initial_ev_at_purchase if initial_ev_at_purchase > 0 else 1.0

        current_valuation = member.self_investment * growth_factor
        annual_dividend = member.self_investment * group_cash_yield

        return CompensationLayer3(
            cumulative_investment=member.self_investment,
            current_valuation=current_valuation,
            annual_dividend=annual_dividend,
        )

    def calculate_all(
        self,
        state: SimulationState,
    ) -> list[TotalCompensation]:
        """Calculate compensation for all members."""
        config = state.config.compensation
        holding = state.holding

        # Group financials
        group_operating_income = sum(c.ebitda for c in holding.companies) * 4  # annualized
        ev_increase = max(0, holding.enterprise_value - holding.historical_high_ev)
        group_fcf = sum(c.fcf for c in holding.companies) * 4
        cash_yield = group_fcf / holding.enterprise_value if holding.enterprise_value > 0 else 0

        results = []
        len(holding.members)

        # Calculate bonus pool
        bonus_pool = max(0, group_operating_income * config.bonus_pool_rate)

        # Calculate per-member bonus based on coefficient
        total_coefficient = sum(m.evaluation_coefficient for m in holding.members)

        for member in holding.members:
            # Layer 1
            if total_coefficient > 0:
                bonus_share = (member.evaluation_coefficient / total_coefficient) * bonus_pool
            else:
                bonus_share = 0

            layer1 = CompensationLayer1(
                base_salary=member.base_salary,
                bonus_pool_rate=config.bonus_pool_rate,
                bonus_pool_total=bonus_pool,
                individual_coefficient=member.evaluation_coefficient,
                bonus=bonus_share,
            )

            # Layer 2 - determine tier
            if member.is_founder or member.grade.value == "S":
                tier = "executive"
            elif member.grade.value == "A":
                tier = "senior"
            else:
                tier = "middle_junior"

            tier_headcount = sum(
                1
                for m in holding.members
                if (m.is_founder or m.grade.value == "S") == (tier == "executive")
                and (m.grade.value == "A") == (tier == "senior")
            )

            layer2 = self.calculate_layer2(
                member,
                ev_increase,
                config.profit_sharing_rate,
                tier,
                max(1, tier_headcount),
            )

            # Layer 3
            layer3 = self.calculate_layer3(
                member,
                holding.enterprise_value,
                50_0000_0000,  # initial EV, simplified
                max(0, cash_yield),
            )

            results.append(
                TotalCompensation(
                    member_id=member.id,
                    year=state.year,
                    layer1=layer1,
                    layer2=layer2,
                    layer3=layer3,
                )
            )

        return results
