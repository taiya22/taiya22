"""Investor engine: returns, control/ownership, IPO scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taiga_sim.models.simulation import SimulationState


@dataclass
class InvestorReturn:
    """Return metrics for an investor."""

    initial_investment: float = 0.0
    current_value: float = 0.0
    moic: float = 0.0
    irr: float = 0.0
    years_held: int = 0


@dataclass
class ControlPosition:
    """Founder's control position."""

    founder_ownership_pct: float = 0.0
    stable_shareholder_pct: float = 0.0
    combined_pct: float = 0.0
    has_veto_power: bool = False  # 33.4%+ = special resolution veto
    has_majority: bool = False  # 50%+


class InvestorEngine:
    """Calculates investor returns and control scenarios."""

    def calculate_investor_return(
        self,
        initial_investment: float,
        ownership_pct: float,
        state: SimulationState,
    ) -> InvestorReturn:
        """Calculate return metrics for a given investor."""
        current_value = state.holding.enterprise_value * ownership_pct
        years = max(1, state.year)
        moic = current_value / initial_investment if initial_investment > 0 else 0

        # IRR calculation: (FV/PV)^(1/n) - 1
        irr = moic ** (1.0 / years) - 1 if moic > 0 and years > 0 else 0.0

        return InvestorReturn(
            initial_investment=initial_investment,
            current_value=current_value,
            moic=moic,
            irr=irr,
            years_held=years,
        )

    def calculate_seed_investor_return(self, state: SimulationState) -> InvestorReturn:
        """Calculate returns for the initial seed investor (5億, 10%)."""
        return self.calculate_investor_return(
            initial_investment=5_0000_0000,
            ownership_pct=0.10,
            state=state,
        )

    def simulate_secondary_sale(
        self,
        state: SimulationState,
        seller_ownership_pct: float,
    ) -> dict:
        """Simulate Year 7 VC secondary sale."""
        sale_value = state.holding.enterprise_value * seller_ownership_pct
        seed_return = self.calculate_investor_return(
            5_0000_0000,
            seller_ownership_pct,
            state,
        )
        return {
            "sale_value": sale_value,
            "buyer_type": "PE/Growth Fund",
            "seller_moic": seed_return.moic,
            "seller_irr": seed_return.irr,
        }

    def calculate_control_position(self, state: SimulationState) -> ControlPosition:
        """Calculate founder's control position."""
        holding = state.holding
        founder_pct = holding.founder_ownership_pct
        stable_pct = holding.stable_shareholder_pct
        combined = founder_pct + stable_pct

        return ControlPosition(
            founder_ownership_pct=founder_pct,
            stable_shareholder_pct=stable_pct,
            combined_pct=combined,
            has_veto_power=founder_pct >= 0.334,
            has_majority=combined >= 0.50,
        )

    def simulate_ipo_scenarios(self, state: SimulationState) -> dict:
        """Simulate the 3 IPO scenarios."""
        holding = state.holding
        ev = holding.enterprise_value

        scenarios = {}

        # Scenario A: Dual-class allowed (制度変更)
        scenarios["A_dual_class"] = {
            "market": "TSE Prime (制度変更後)",
            "founder_voting_pct": min(0.90, holding.founder_ownership_pct * 10),  # 10x voting
            "founder_economic_pct": holding.founder_ownership_pct,
            "control": "absolute",
            "probability": 0.20,  # 20% chance of regulatory change
        }

        # Scenario B: TSE baseline (1:1 voting)
        float_pct = 0.25  # 25% float
        post_ipo_founder = holding.founder_ownership_pct * (1 - float_pct)
        scenarios["B_tse_baseline"] = {
            "market": "TSE Prime",
            "founder_ownership_pct": post_ipo_founder,
            "stable_shareholder_pct": holding.stable_shareholder_pct,
            "combined_pct": post_ipo_founder + holding.stable_shareholder_pct,
            "has_veto": post_ipo_founder >= 0.334,
            "has_majority": (post_ipo_founder + holding.stable_shareholder_pct) >= 0.50,
            "probability": 0.60,
        }

        # Scenario C: NYSE (dual-class possible)
        scenarios["C_nyse"] = {
            "market": "NYSE",
            "founder_voting_pct": min(0.90, holding.founder_ownership_pct * 10),
            "founder_economic_pct": holding.founder_ownership_pct * (1 - float_pct),
            "requirement": "時価総額1兆円以上",
            "meets_requirement": ev >= 1_0000_0000_0000,
            "probability": 0.20,
        }

        return scenarios

    def update_dilution(self, state: SimulationState) -> None:
        """Update founder ownership accounting for dilution events."""
        holding = state.holding
        year = state.year

        # Year 0: 10% dilution from seed
        if year == 0:
            holding.founder_ownership_pct = 0.90

        # Gradual dilution from employee stock (small)
        if year > 0:
            annual_dilution = 0.005  # 0.5% per year to employees
            holding.founder_ownership_pct *= 1 - annual_dilution

        # IPO dilution
        if year == state.config.ipo_target_year and not holding.is_public:
            ipo_float = 0.25
            holding.founder_ownership_pct *= 1 - ipo_float
            holding.is_public = True

        # Build stable shareholder base
        if year >= 5:
            # Foundation + employee stock ownership + friendly institutions
            holding.stable_shareholder_pct = min(
                0.25,
                0.05 + year * 0.005,
            )
