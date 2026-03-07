"""HR engine: hiring, turnover, evaluation, unit assignment."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taiga_sim.models.simulation import SimulationState

from taiga_sim.models.organization import (
    EvaluationCoefficient,
    EvaluationScores,
    Member,
    MemberGrade,
    OwnershipScore,
    UnitType,
)


class HREngine:
    """Handles human capital simulation."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def initialize_founding_team(self, state: SimulationState) -> None:
        """Set up the founding team at Year 0."""
        founder = Member(
            id="m_founder",
            name="山脇",
            age=25,  # placeholder
            join_year=0,
            grade=MemberGrade.S,
            is_founder=True,
            base_salary=180_0000,  # 年180万円
            evaluation_coefficient=1.5,
            ownership_score=OwnershipScore(
                financial_literacy=18,
                decision_ownership=18,
                holistic_perspective=16,
                strategic_vision=18,
                skin_in_the_game=20,
            ),
        )

        member1 = Member(
            id="m_001",
            name="初期メンバー1",
            age=27,
            join_year=0,
            grade=MemberGrade.A,
            base_salary=400_0000,
            evaluation_coefficient=1.2,
        )

        member2 = Member(
            id="m_002",
            name="初期メンバー2",
            age=28,
            join_year=0,
            grade=MemberGrade.A,
            base_salary=400_0000,
            evaluation_coefficient=1.2,
        )

        state.holding.members = [founder, member1, member2]

    def simulate_hiring(self, state: SimulationState) -> list[Member]:
        """Simulate annual hiring based on phase and growth needs."""
        phase = state.current_phase
        if phase is None:
            return []

        # Hiring targets by phase
        hire_targets = {
            0: 0, 1: 3, 2: 8, 3: 20, 4: 50, 5: 80, 6: 150,
        }
        target = hire_targets.get(phase.phase, 5)

        # Randomize around target
        actual_hires = max(0, target + self.rng.randint(-2, 2))

        new_members = []
        for i in range(actual_hires):
            age = self.rng.randint(23, 35)
            grade_roll = self.rng.random()
            if grade_roll < 0.05:
                grade = MemberGrade.S
            elif grade_roll < 0.25:
                grade = MemberGrade.A
            elif grade_roll < 0.75:
                grade = MemberGrade.B
            else:
                grade = MemberGrade.C

            # Base salary scales with phase
            base_multipliers = {0: 1.0, 1: 1.0, 2: 1.1, 3: 1.2, 4: 1.3, 5: 1.4, 6: 1.5}
            base = 450_0000 * base_multipliers.get(phase.phase, 1.0) * 0.75  # 75% of market

            member = Member(
                id=f"m_{state.year:03d}_{i+1:03d}",
                name=f"メンバー_{state.year}_{i+1}",
                age=age,
                join_year=state.year,
                grade=grade,
                base_salary=base,
                evaluation_coefficient=1.0,
            )
            new_members.append(member)

        state.holding.members.extend(new_members)
        return new_members

    def simulate_turnover(self, state: SimulationState) -> list[Member]:
        """Simulate annual employee departures."""
        config = state.config.hr
        departed = []

        for member in list(state.holding.members):
            if member.is_founder:
                continue  # founder never leaves

            # Base turnover rate, modified by factors
            base_rate = config.annual_turnover_rate
            tenure = state.year - member.join_year

            # Lower turnover for higher ownership scores
            os_modifier = (50 - member.ownership_score.total) / 100  # higher score = lower modifier
            # Lower turnover for longer tenure (up to a point)
            tenure_modifier = max(-0.02, 0.02 - tenure * 0.005)

            adjusted_rate = max(0.01, base_rate + os_modifier * 0.03 + tenure_modifier)

            if self.rng.random() < adjusted_rate:
                departed.append(member)

        for member in departed:
            state.holding.members.remove(member)

        return departed

    def evaluate_members(self, state: SimulationState) -> None:
        """Run annual evaluation cycle: update scores and coefficients."""
        for member in state.holding.members:
            # Simulate evaluation scores (would be input in real system)
            member.evaluation = EvaluationScores(
                scene_creation=self.rng.uniform(40, 95),
                perspective_offering=self.rng.uniform(40, 90),
                ownership=self.rng.uniform(40, 90),
                behind_the_scene=self.rng.uniform(40, 85),
            )

            # Update Ownership Score (gradual drift with noise)
            os = member.ownership_score
            drift = self.rng.uniform(-1, 2)  # slight positive drift
            member.ownership_score = OwnershipScore(
                financial_literacy=os.financial_literacy + self.rng.uniform(-0.5, 1.0),
                decision_ownership=os.decision_ownership + self.rng.uniform(-0.5, 1.0),
                holistic_perspective=os.holistic_perspective + self.rng.uniform(-0.5, 1.0),
                strategic_vision=os.strategic_vision + self.rng.uniform(-0.5, 1.0),
                skin_in_the_game=os.skin_in_the_game + (1.0 if member.self_investment > 0 else -0.5),
            ).clamp()

            # Determine evaluation coefficient based on weighted score
            ws = member.evaluation.weighted_score
            if ws >= 85:
                member.evaluation_coefficient = 1.5
            elif ws >= 75:
                member.evaluation_coefficient = 1.2
            elif ws >= 55:
                member.evaluation_coefficient = 1.0
            elif ws >= 40:
                member.evaluation_coefficient = 0.8
            else:
                member.evaluation_coefficient = 0.5

    def assign_units(self, state: SimulationState) -> None:
        """Assign members to appropriate units based on grade and needs."""
        for member in state.holding.members:
            if member.unit is not None:
                continue

            if member.grade == MemberGrade.S and member.is_eligible_for_elite_unit(state.year):
                # S-grade -> Creation or Turnaround
                if self.rng.random() < 0.5:
                    member.unit = UnitType.CREATION
                else:
                    member.unit = UnitType.TURNAROUND
            else:
                member.unit = UnitType.OPERATING

        # Update unit rosters
        for unit in state.holding.units:
            unit.members = [
                m.id for m in state.holding.members if m.unit == unit.unit_type
            ]
