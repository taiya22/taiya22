"""Motivation engine: models intrinsic motivation × extrinsic incentive dynamics.

Uses second-order meta-analytic effect sizes to predict performance outcomes
under different motivation architecture configurations.

Key parameters (from meta_analysis_paper.docx):
- Intrinsic motivation → performance: ρ = .16 (low complexity) to .38 (high complexity)
- Extrinsic incentives → performance: d = 0.48 (low) to 0.04 (high complexity)
- Crowding-out effect: d = -0.10 (low) to -0.40 (high complexity)
- Verbal/informational feedback: d = +0.33
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from taiga_sim.models.simulation import SimulationState


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class MotivationConfig:
    """Configuration for the motivation simulation engine."""

    # --- Meta-analytic effect sizes (second-order estimates) ---

    # Intrinsic motivation → performance correlation (ρ) by complexity
    im_effect_low: float = 0.16
    im_effect_mid: float = 0.26
    im_effect_high: float = 0.38

    # Extrinsic incentive → performance (Cohen's d) by complexity
    ei_effect_low: float = 0.48
    ei_effect_mid: float = 0.22
    ei_effect_high: float = 0.04

    # Crowding-out risk (Cohen's d, negative = harmful) by complexity
    crowding_out_low: float = -0.10
    crowding_out_mid: float = -0.25
    crowding_out_high: float = -0.40

    # Informational/verbal feedback effect
    informational_feedback_effect: float = 0.33

    # Team incentive bonus (Condly et al.: team d=0.68 vs individual d=0.22)
    team_incentive_multiplier: float = 1.5

    # Autonomy-supportive intervention effect (Slemp et al., 2018: d=0.52)
    autonomy_support_effect: float = 0.52

    # --- Organizational parameters ---

    # Initial intrinsic motivation level (0-1 scale, 1 = maximum)
    initial_intrinsic_motivation: float = 0.70

    # Natural motivation decay rate per year without maintenance
    motivation_decay_rate: float = 0.03

    # Recovery rate from crowding-out per year (with intervention)
    recovery_rate_with_intervention: float = 0.10

    # Recovery rate without intervention (near zero — irreversibility)
    recovery_rate_without_intervention: float = 0.02


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

@dataclass
class RoleMotivationState:
    """Motivation state for a role category."""

    role_name: str
    complexity: str  # "low", "mid", "high"
    headcount: int = 1

    # Motivation levels (0-1 scale)
    intrinsic_motivation: float = 0.70
    extrinsic_incentive_strength: float = 0.50  # 0 = no incentives, 1 = maximum
    variable_pay_ratio: float = 0.25  # proportion of total comp that is variable

    # Design quality (0-1 scale)
    informational_framing: float = 0.50  # how informational (vs controlling) are rewards
    autonomy_support: float = 0.50
    team_based_incentives: float = 0.30  # proportion of incentives that are team-based

    # Outcomes (computed)
    performance_quality: float = 0.0
    performance_quantity: float = 0.0
    performance_composite: float = 0.0
    crowding_out_damage: float = 0.0


@dataclass
class OrganizationMotivationState:
    """Aggregated motivation state for the organization."""

    year: int = 0
    roles: List[RoleMotivationState] = field(default_factory=list)

    # Aggregate metrics
    avg_intrinsic_motivation: float = 0.0
    avg_performance_quality: float = 0.0
    avg_performance_quantity: float = 0.0
    avg_performance_composite: float = 0.0
    total_crowding_out_damage: float = 0.0
    prestige_ratio: float = 0.85  # proportion of leaders who are Prestige-type
    motivation_culture_score: float = 0.0


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class MotivationEngine:
    """Simulates motivation dynamics and performance outcomes.

    Core model:
        Performance_quality = f(intrinsic_motivation, complexity) + feedback_effect
        Performance_quantity = f(extrinsic_incentive, complexity)
        Crowding_out = g(incentive_strength, controlling_framing, complexity)
        Net_IM_change = -crowding_out + recovery + autonomy_support - decay
    """

    def __init__(self, config: Optional[MotivationConfig] = None):
        self.config = config or MotivationConfig()

    # --- Complexity-dependent effect lookups ---

    def _get_im_effect(self, complexity: str) -> float:
        """Get intrinsic motivation → performance effect by complexity."""
        return {
            "low": self.config.im_effect_low,
            "mid": self.config.im_effect_mid,
            "high": self.config.im_effect_high,
        }[complexity]

    def _get_ei_effect(self, complexity: str) -> float:
        """Get extrinsic incentive → performance effect by complexity."""
        return {
            "low": self.config.ei_effect_low,
            "mid": self.config.ei_effect_mid,
            "high": self.config.ei_effect_high,
        }[complexity]

    def _get_crowding_out_risk(self, complexity: str) -> float:
        """Get crowding-out risk (negative d) by complexity."""
        return {
            "low": self.config.crowding_out_low,
            "mid": self.config.crowding_out_mid,
            "high": self.config.crowding_out_high,
        }[complexity]

    # --- Core simulation ---

    def compute_performance(self, role: RoleMotivationState) -> RoleMotivationState:
        """Compute performance outcomes for a role given current motivation state."""
        im_effect = self._get_im_effect(role.complexity)
        ei_effect = self._get_ei_effect(role.complexity)

        # Performance quality: driven by intrinsic motivation
        # Scale: ρ * IM_level, plus informational feedback bonus
        feedback_bonus = (
            self.config.informational_feedback_effect
            * role.informational_framing
            * 0.5  # scale to reasonable range
        )
        role.performance_quality = (
            im_effect * role.intrinsic_motivation + feedback_bonus
        )

        # Performance quantity: driven by extrinsic incentives
        # Team-based incentives get a multiplier
        team_bonus = (
            role.team_based_incentives
            * (self.config.team_incentive_multiplier - 1.0)
        )
        role.performance_quantity = (
            ei_effect
            * role.extrinsic_incentive_strength
            * (1.0 + team_bonus)
        )

        # Composite: weighted average (quality weighted more for high complexity)
        quality_weight = {"low": 0.3, "mid": 0.5, "high": 0.7}[role.complexity]
        role.performance_composite = (
            quality_weight * role.performance_quality
            + (1 - quality_weight) * role.performance_quantity
        )

        return role

    def compute_crowding_out(self, role: RoleMotivationState) -> float:
        """Compute crowding-out damage for one period.

        Crowding out depends on:
        1. Incentive strength (variable pay ratio)
        2. How controlling (vs informational) the framing is
        3. Task complexity
        """
        base_risk = abs(self._get_crowding_out_risk(role.complexity))

        # Controlling framing amplifies crowding out
        controlling_factor = 1.0 - role.informational_framing  # 0 = fully informational

        # Higher variable pay ratio = more incentive pressure
        incentive_pressure = role.variable_pay_ratio

        # Crowding out = base_risk × controlling × incentive_pressure
        damage = base_risk * controlling_factor * incentive_pressure

        # If intrinsic motivation is already low, less to crowd out
        damage *= role.intrinsic_motivation

        role.crowding_out_damage = damage
        return damage

    def update_intrinsic_motivation(
        self,
        role: RoleMotivationState,
        has_recovery_intervention: bool = False,
    ) -> float:
        """Update intrinsic motivation for one period.

        ΔIM = -crowding_out - natural_decay + autonomy_support_effect + recovery
        """
        cfg = self.config

        # Crowding out damage (already computed)
        crowding_damage = role.crowding_out_damage

        # Natural decay
        decay = cfg.motivation_decay_rate

        # Autonomy support boost
        autonomy_boost = (
            cfg.autonomy_support_effect
            * role.autonomy_support
            * 0.1  # scale annual effect
        )

        # Recovery (if intervention active and IM is below initial)
        recovery = 0.0
        if role.intrinsic_motivation < cfg.initial_intrinsic_motivation:
            if has_recovery_intervention:
                recovery = cfg.recovery_rate_with_intervention
            else:
                recovery = cfg.recovery_rate_without_intervention

        # Net change
        delta = -crowding_damage - decay + autonomy_boost + recovery

        # Apply
        new_im = max(0.0, min(1.0, role.intrinsic_motivation + delta))
        role.intrinsic_motivation = new_im

        return new_im

    def simulate_year(
        self,
        state: OrganizationMotivationState,
        has_recovery_intervention: bool = False,
    ) -> OrganizationMotivationState:
        """Simulate one year of motivation dynamics for the organization."""
        state.year += 1

        total_headcount = sum(r.headcount for r in state.roles)
        if total_headcount == 0:
            return state

        # Process each role
        for role in state.roles:
            self.compute_crowding_out(role)
            self.update_intrinsic_motivation(role, has_recovery_intervention)
            self.compute_performance(role)

        # Aggregate
        state.avg_intrinsic_motivation = sum(
            r.intrinsic_motivation * r.headcount for r in state.roles
        ) / total_headcount

        state.avg_performance_quality = sum(
            r.performance_quality * r.headcount for r in state.roles
        ) / total_headcount

        state.avg_performance_quantity = sum(
            r.performance_quantity * r.headcount for r in state.roles
        ) / total_headcount

        state.avg_performance_composite = sum(
            r.performance_composite * r.headcount for r in state.roles
        ) / total_headcount

        state.total_crowding_out_damage = sum(
            r.crowding_out_damage * r.headcount for r in state.roles
        ) / total_headcount

        # Motivation culture score: weighted by IM and autonomy support
        state.motivation_culture_score = (
            state.avg_intrinsic_motivation * 0.6
            + sum(r.autonomy_support * r.headcount for r in state.roles)
            / total_headcount
            * 0.4
        )

        return state

    def run_simulation(
        self,
        initial_state: OrganizationMotivationState,
        years: int = 10,
        has_recovery_intervention: bool = False,
    ) -> List[OrganizationMotivationState]:
        """Run a multi-year simulation and return yearly snapshots."""
        import copy

        results = []
        state = copy.deepcopy(initial_state)

        # Record initial state (compute all aggregates)
        total_hc = sum(r.headcount for r in state.roles) or 1
        for role in state.roles:
            self.compute_performance(role)
        state.avg_intrinsic_motivation = sum(
            r.intrinsic_motivation * r.headcount for r in state.roles
        ) / total_hc
        state.avg_performance_quality = sum(
            r.performance_quality * r.headcount for r in state.roles
        ) / total_hc
        state.avg_performance_quantity = sum(
            r.performance_quantity * r.headcount for r in state.roles
        ) / total_hc
        state.avg_performance_composite = sum(
            r.performance_composite * r.headcount for r in state.roles
        ) / total_hc
        state.motivation_culture_score = (
            state.avg_intrinsic_motivation * 0.6
            + sum(r.autonomy_support * r.headcount for r in state.roles)
            / total_hc * 0.4
        )
        results.append(copy.deepcopy(state))

        for _ in range(years):
            state = self.simulate_year(state, has_recovery_intervention)
            results.append(copy.deepcopy(state))

        return results


# ---------------------------------------------------------------------------
# Scenario presets
# ---------------------------------------------------------------------------

def create_taiga_default_state() -> OrganizationMotivationState:
    """Create the default Taiga organizational motivation state.

    Based on motivation_architecture_guide.md Section 2.
    """
    roles = [
        # High complexity: fund managers, CEOs, strategists
        RoleMotivationState(
            role_name="Executive / Fund Manager",
            complexity="high",
            headcount=15,
            intrinsic_motivation=0.80,
            extrinsic_incentive_strength=0.30,
            variable_pay_ratio=0.20,
            informational_framing=0.80,
            autonomy_support=0.85,
            team_based_incentives=0.20,
        ),
        # Mid complexity: deal sourcing, PM, business development
        RoleMotivationState(
            role_name="Professional / Manager",
            complexity="mid",
            headcount=40,
            intrinsic_motivation=0.70,
            extrinsic_incentive_strength=0.50,
            variable_pay_ratio=0.30,
            informational_framing=0.60,
            autonomy_support=0.65,
            team_based_incentives=0.40,
        ),
        # Low complexity: operations, accounting, admin
        RoleMotivationState(
            role_name="Operations / Admin",
            complexity="low",
            headcount=25,
            intrinsic_motivation=0.55,
            extrinsic_incentive_strength=0.60,
            variable_pay_ratio=0.25,
            informational_framing=0.50,
            autonomy_support=0.50,
            team_based_incentives=0.50,
        ),
    ]

    return OrganizationMotivationState(year=0, roles=roles, prestige_ratio=0.85)


def create_conventional_pe_state() -> OrganizationMotivationState:
    """Create a conventional PE firm state (high extrinsic, controlling).

    Represents the 'Midas Capital' archetype — heavy incentive-driven culture.
    """
    roles = [
        RoleMotivationState(
            role_name="Executive / Fund Manager",
            complexity="high",
            headcount=15,
            intrinsic_motivation=0.60,
            extrinsic_incentive_strength=0.80,
            variable_pay_ratio=0.60,
            informational_framing=0.30,
            autonomy_support=0.40,
            team_based_incentives=0.10,
        ),
        RoleMotivationState(
            role_name="Professional / Manager",
            complexity="mid",
            headcount=40,
            intrinsic_motivation=0.55,
            extrinsic_incentive_strength=0.70,
            variable_pay_ratio=0.50,
            informational_framing=0.30,
            autonomy_support=0.35,
            team_based_incentives=0.20,
        ),
        RoleMotivationState(
            role_name="Operations / Admin",
            complexity="low",
            headcount=25,
            intrinsic_motivation=0.45,
            extrinsic_incentive_strength=0.65,
            variable_pay_ratio=0.35,
            informational_framing=0.40,
            autonomy_support=0.40,
            team_based_incentives=0.30,
        ),
    ]

    return OrganizationMotivationState(year=0, roles=roles, prestige_ratio=0.55)


def create_crowded_out_recovery_state() -> OrganizationMotivationState:
    """Create a state representing a post-M&A organization with damaged motivation.

    Simulates the scenario described in research_gaps.md Gap 3:
    an organization whose intrinsic motivation has been crowded out by
    a previous controlling incentive regime.
    """
    roles = [
        RoleMotivationState(
            role_name="Executive / Fund Manager",
            complexity="high",
            headcount=10,
            intrinsic_motivation=0.35,  # severely crowded out
            extrinsic_incentive_strength=0.70,
            variable_pay_ratio=0.55,
            informational_framing=0.25,
            autonomy_support=0.30,
            team_based_incentives=0.10,
        ),
        RoleMotivationState(
            role_name="Professional / Manager",
            complexity="mid",
            headcount=30,
            intrinsic_motivation=0.40,
            extrinsic_incentive_strength=0.65,
            variable_pay_ratio=0.45,
            informational_framing=0.30,
            autonomy_support=0.30,
            team_based_incentives=0.15,
        ),
        RoleMotivationState(
            role_name="Operations / Admin",
            complexity="low",
            headcount=20,
            intrinsic_motivation=0.40,
            extrinsic_incentive_strength=0.60,
            variable_pay_ratio=0.30,
            informational_framing=0.35,
            autonomy_support=0.35,
            team_based_incentives=0.25,
        ),
    ]

    return OrganizationMotivationState(year=0, roles=roles, prestige_ratio=0.45)
