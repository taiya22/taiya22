"""Crisis engine: macro shocks, 5 resilience mechanisms.

Macro shock model based on historical data:
- Reinhart & Rogoff (2009): major financial crises every ~10-15 years
- Average recession: revenue -10 to -25%, EBITDA -20 to -40%
- Recovery time: 2-4 years typically
- Deterministic shocks at ~Year 8-12 and ~Year 20-24 (Lehman/COVID-like)
  plus random smaller shocks
"""

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
    crisis_type: str = "random"  # "lehman", "covid", "sector", "random"


class CrisisEngine:
    """Simulates macro shocks and activates resilience mechanisms."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self._major_shock_years: set[str] = set()  # track which major shock windows have fired

    def check_for_shock(self, state: SimulationState) -> CrisisEvent | None:
        """Roll for macro-economic shock.

        Two layers:
        1. Structural shocks: high probability around Year 8-12, Year 20-24
           (modeling the statistical inevitability of major recessions)
        2. Random shocks: base probability each year (mild to moderate)
        """
        if state.macro.is_shock_active:
            return None

        year = state.year

        # Layer 1: Structural major shocks (Lehman/COVID-like)
        # High probability in certain windows, near-guaranteed over 30 years
        major_shock = self._check_structural_shock(year)
        if major_shock:
            return self._create_event(state, major_shock)

        # Layer 2: Random shocks (sector-specific, policy errors, etc.)
        # Base probability: ~5-8% per year for mild-to-moderate shocks
        if self.rng.random() < state.macro.shock_probability:
            return self._create_event(state, "random")

        return None

    def _check_structural_shock(self, year: int) -> str | None:
        """Check for structural (near-inevitable) major shocks.

        Historical pattern: major crises roughly every 10-15 years
        - 1997 Asian crisis, 2001 dot-com, 2008 Lehman, 2020 COVID
        """
        # First major shock window: Year 8-12
        if 8 <= year <= 12 and "major_1" not in self._major_shock_years:
            prob = {8: 0.15, 9: 0.25, 10: 0.35, 11: 0.30, 12: 0.20}.get(year, 0.10)
            if self.rng.random() < prob:
                self._major_shock_years.add("major_1")
                return "lehman"

        # Second major shock window: Year 20-25
        if 20 <= year <= 25 and "major_2" not in self._major_shock_years:
            prob = {20: 0.10, 21: 0.20, 22: 0.30, 23: 0.25, 24: 0.15, 25: 0.10}.get(year, 0.10)
            if self.rng.random() < prob:
                self._major_shock_years.add("major_2")
                return "covid"

        return None

    def _create_event(self, state: SimulationState, crisis_type: str) -> CrisisEvent:
        """Create a crisis event based on type."""
        # Severity by type (Reinhart & Rogoff 2009 data)
        if crisis_type == "lehman":
            decline = self.rng.uniform(0.30, 0.50)  # severe: Lehman was ~50%
            duration = self.rng.randint(6, 10)  # 1.5-2.5 years
        elif crisis_type == "covid":
            decline = self.rng.uniform(0.20, 0.40)  # sharp but shorter
            duration = self.rng.randint(4, 8)  # 1-2 years
        elif crisis_type == "sector":
            decline = self.rng.uniform(0.10, 0.25)  # sector-specific
            duration = self.rng.randint(3, 6)
        else:  # random
            decline = self.rng.uniform(0.08, 0.25)  # mild to moderate
            duration = self.rng.randint(2, 6)

        event = CrisisEvent(
            year=state.year,
            quarter=state.quarter,
            ev_decline_pct=decline,
            duration_quarters=duration,
            mechanisms_triggered=[],
            crisis_type=crisis_type,
        )

        # Apply shock
        state.macro.is_shock_active = True
        state.macro.shock_remaining_quarters = duration

        pre_shock_ev = state.holding.enterprise_value
        shock_ev = pre_shock_ev * (1 - decline)
        state.holding.enterprise_value = shock_ev

        # Also hit company revenues/EBITDA directly
        for company in state.holding.companies:
            rev_hit = decline * self.rng.uniform(0.3, 0.7)  # partial revenue impact
            ebitda_hit = decline * self.rng.uniform(0.5, 1.0)  # EBITDA hit harder
            company.revenue *= 1 - rev_hit
            company.ebitda *= 1 - ebitda_hit

        # Mechanism triggers
        decline_from_high = 1 - (shock_ev / state.holding.historical_high_ev)

        if decline_from_high >= 0.20:
            event.mechanisms_triggered.append("crisis_profit_sharing")
            event.mechanisms_triggered.append("crisis_evaluation")

        if decline_from_high >= 0.30:
            event.mechanisms_triggered.append("special_investment_window")
            event.mechanisms_triggered.append("hwm_reset")

        state.crisis_events.append(
            {
                "year": event.year,
                "quarter": event.quarter,
                "type": crisis_type,
                "decline_pct": event.ev_decline_pct,
                "duration_quarters": event.duration_quarters,
                "mechanisms": event.mechanisms_triggered,
            }
        )

        return event

    def apply_mechanisms(self, state: SimulationState, event: CrisisEvent) -> dict:
        """Apply the 5 crisis resilience mechanisms as needed."""
        results: dict[str, object] = {}
        holding = state.holding

        if "hwm_reset" in event.mechanisms_triggered:
            new_hwm = state.holding.enterprise_value * 1.10
            holding.historical_high_ev = new_hwm
            results["hwm_reset"] = {"new_hwm": new_hwm}

        if "crisis_profit_sharing" in event.mechanisms_triggered:
            group_fcf = sum(c.fcf for c in holding.companies) * 4
            if group_fcf > 0 and holding.enterprise_value > 0:
                crisis_pool = group_fcf * 0.10
                results["crisis_profit_sharing"] = {"pool": crisis_pool}

        if "special_investment_window" in event.mechanisms_triggered:
            results["special_investment_window"] = {
                "ev_at_window": holding.enterprise_value,
            }

        if holding.keshiki_reserve > 0:
            monthly_burn = sum(m.base_salary for m in holding.members) / 12
            months_covered = holding.keshiki_reserve / monthly_burn if monthly_burn > 0 else 0
            results["keshiki_reserve"] = {
                "months_covered": months_covered,
            }
            if months_covered < 12:
                for member in holding.members:
                    if not member.is_founder:
                        reduction = member.base_salary * 0.20 / 12
                        member.self_investment += reduction

        if "crisis_evaluation" in event.mechanisms_triggered:
            results["crisis_evaluation"] = {"top_axis": "Scene Protection"}

        return results

    def advance_crisis(self, state: SimulationState) -> None:
        """Advance crisis timer by one quarter."""
        if not state.macro.is_shock_active:
            return

        state.macro.shock_remaining_quarters -= 1
        if state.macro.shock_remaining_quarters <= 0:
            state.macro.is_shock_active = False
            state.macro.shock_remaining_quarters = 0
