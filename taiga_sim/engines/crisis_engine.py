"""Crisis engine: macro shocks, 5 resilience mechanisms."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taiga_sim.models.simulation import SimulationState


@dataclass
class CrisisEvent:
    """A crisis event in the simulation."""

    year: int
    quarter: int
    ev_decline_pct: float
    duration_quarters: int
    mechanisms_triggered: list[str]


class CrisisEngine:
    """Simulates macro shocks and activates resilience mechanisms."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def check_for_shock(self, state: SimulationState) -> CrisisEvent | None:
        """Roll for a macro-economic shock at the start of each year."""
        if state.macro.is_shock_active:
            return None  # already in crisis

        if self.rng.random() >= state.macro.shock_probability:
            return None  # no shock this year

        # Generate shock parameters
        decline = self.rng.uniform(0.15, 0.50)  # 15-50% EV decline
        duration = self.rng.randint(4, 12)  # 1-3 years

        event = CrisisEvent(
            year=state.year,
            quarter=state.quarter,
            ev_decline_pct=decline,
            duration_quarters=duration,
            mechanisms_triggered=[],
        )

        # Apply shock
        state.macro.is_shock_active = True
        state.macro.shock_remaining_quarters = duration

        pre_shock_ev = state.holding.enterprise_value
        shock_ev = pre_shock_ev * (1 - decline)
        state.holding.enterprise_value = shock_ev

        # Determine which mechanisms trigger
        decline_from_high = 1 - (shock_ev / state.holding.historical_high_ev)

        if decline_from_high >= 0.20:
            event.mechanisms_triggered.append("crisis_profit_sharing")
            event.mechanisms_triggered.append("crisis_evaluation")

        if decline_from_high >= 0.30:
            event.mechanisms_triggered.append("special_investment_window")
            event.mechanisms_triggered.append("hwm_reset")

        state.crisis_events.append({
            "year": event.year,
            "quarter": event.quarter,
            "decline_pct": event.ev_decline_pct,
            "duration_quarters": event.duration_quarters,
            "mechanisms": event.mechanisms_triggered,
        })

        return event

    def apply_mechanisms(self, state: SimulationState, event: CrisisEvent) -> dict:
        """Apply the 5 crisis resilience mechanisms as needed."""
        results = {}
        holding = state.holding

        # Mechanism 1: HWM Reset
        if "hwm_reset" in event.mechanisms_triggered:
            new_hwm = state.holding.enterprise_value * 1.10  # current + 10%
            holding.historical_high_ev = new_hwm
            results["hwm_reset"] = {
                "new_hwm": new_hwm,
                "requires": "経営会議全員一致 + 外部評価委員会認定",
            }

        # Mechanism 2: Crisis profit sharing
        if "crisis_profit_sharing" in event.mechanisms_triggered:
            # Special pool linked to cash yield
            group_fcf = sum(c.fcf for c in holding.companies) * 4
            if group_fcf > 0 and holding.enterprise_value > 0:
                cash_yield = group_fcf / holding.enterprise_value
                crisis_pool = group_fcf * 0.10  # 10% of FCF as crisis bonus
                results["crisis_profit_sharing"] = {"pool": crisis_pool, "cash_yield": cash_yield}

        # Mechanism 3: Special investment window
        if "special_investment_window" in event.mechanisms_triggered:
            results["special_investment_window"] = {
                "status": "open",
                "ev_at_window": holding.enterprise_value,
                "discount_to_hwm_pct": (1 - holding.enterprise_value / holding.historical_high_ev) * 100,
            }

        # Mechanism 4: Keshiki reserve deployment
        if holding.keshiki_reserve > 0:
            monthly_burn = sum(m.base_salary for m in holding.members) / 12
            months_covered = holding.keshiki_reserve / monthly_burn if monthly_burn > 0 else 0
            results["keshiki_reserve"] = {
                "balance": holding.keshiki_reserve,
                "months_covered": months_covered,
                "salary_reduction": months_covered < 12,  # reduce to 80% if <12 months
            }

            if months_covered < 12:
                # Auto-convert salary reduction to B-class shares
                for member in holding.members:
                    if not member.is_founder:
                        reduction = member.base_salary * 0.20 / 12  # 20% monthly reduction
                        member.self_investment += reduction  # converted to B-class shares

        # Mechanism 5: Crisis evaluation
        if "crisis_evaluation" in event.mechanisms_triggered:
            results["crisis_evaluation"] = {
                "top_axis": "景色を守る（Scene Protection）",
                "special_bonus": True,
            }

        return results

    def advance_crisis(self, state: SimulationState) -> None:
        """Advance crisis timer by one quarter."""
        if not state.macro.is_shock_active:
            return

        state.macro.shock_remaining_quarters -= 1
        if state.macro.shock_remaining_quarters <= 0:
            state.macro.is_shock_active = False
            state.macro.shock_remaining_quarters = 0
