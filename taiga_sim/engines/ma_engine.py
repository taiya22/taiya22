"""M&A engine: acquisition pipeline, PMI, synergy modeling.

Acquisition discipline:
- Standard deals: strict EV/EBITDA multiple discipline (buy cheap)
- Strategic exception: high-growth targets with overwhelming competitive
  advantages (e.g. Instagram-type, Manus AI-type acquisitions) are
  evaluated on revenue growth + strategic value, not EBITDA multiples.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taiga_sim.models.simulation import SimulationState

from taiga_sim.models.organization import Company, CompanyType


@dataclass
class AcquisitionTarget:
    """A potential acquisition target."""

    name: str
    company_type: CompanyType
    revenue: float
    ebitda: float
    asking_ev_ebitda: float
    headcount: int

    # Strategic exception fields
    is_strategic: bool = False  # True = high-growth / distribution play
    revenue_growth_rate: float = 0.05  # annual revenue growth
    has_tech_moat: bool = False  # proprietary tech advantage
    has_distribution_moat: bool = False  # customer base / network effect
    competitive_advantage_tags: list[str] = field(default_factory=list)

    @property
    def asking_price(self) -> float:
        if self.is_strategic and self.ebitda <= 0:
            # Pre-profit strategic target: price on revenue multiple
            return self.revenue * self._strategic_revenue_multiple
        return self.ebitda * self.asking_ev_ebitda

    @property
    def _strategic_revenue_multiple(self) -> float:
        """Revenue multiple for high-growth pre-profit targets."""
        base = 3.0
        if self.revenue_growth_rate > 1.0:  # >100% growth
            base = 8.0
        elif self.revenue_growth_rate > 0.5:
            base = 5.0
        return base


# Phase-based M&A parameters
PHASE_MA_PARAMS = {
    # phase: (pipeline_size, max_acquisitions, deal_success_rate)
    0: (0, 0, 0),
    1: (8, 2, 0.35),
    2: (12, 3, 0.35),
    3: (20, 4, 0.40),
    4: (25, 5, 0.40),
    5: (20, 4, 0.45),
    6: (15, 3, 0.45),
}


class MAEngine:
    """Handles M&A pipeline, execution, and PMI."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def _phase_params(self, phase_num: int) -> tuple[int, int, float]:
        return PHASE_MA_PARAMS.get(phase_num, (5, 1, 0.30))

    def generate_pipeline(self, state: SimulationState) -> list[AcquisitionTarget]:
        """Generate M&A pipeline for the current year based on phase."""
        phase = state.current_phase
        if phase is None:
            return []

        pipeline_size, _, _ = self._phase_params(phase.phase)
        if pipeline_size == 0:
            return []

        # Randomize pipeline count around target
        count = max(1, pipeline_size + self.rng.randint(-3, 3))

        targets = []
        if phase.phase <= 2:
            targets = self._gen_early_stage(state, count)
        elif phase.phase <= 4:
            targets = self._gen_mid_stage(state, count)
        else:
            targets = self._gen_late_stage(state, count)

        return targets

    def _gen_early_stage(self, state: SimulationState, count: int) -> list[AcquisitionTarget]:
        """Phase 1-2: small manufacturing, succession deals."""
        targets = []
        for i in range(count):
            revenue = self.rng.uniform(5_0000_0000, 25_0000_0000)
            ebitda_margin = self.rng.uniform(0.08, 0.20)
            targets.append(AcquisitionTarget(
                name=f"Target_{state.year}_{i+1}",
                company_type=CompanyType.PRODUCT,
                revenue=revenue,
                ebitda=revenue * ebitda_margin,
                asking_ev_ebitda=self.rng.uniform(2.5, 5.0),
                headcount=self.rng.randint(15, 120),
                revenue_growth_rate=self.rng.uniform(0.0, 0.08),
            ))
        return targets

    def _gen_mid_stage(self, state: SimulationState, count: int) -> list[AcquisitionTarget]:
        """Phase 3-4: larger, diversified, plus strategic targets."""
        targets = []
        types = list(CompanyType)
        for i in range(count):
            # 15% chance of strategic high-growth target
            is_strategic = self.rng.random() < 0.15
            if is_strategic:
                targets.append(self._gen_strategic_target(state, i, scale="mid"))
            else:
                revenue = self.rng.uniform(30_0000_0000, 500_0000_0000)
                ebitda_margin = self.rng.uniform(0.10, 0.22)
                targets.append(AcquisitionTarget(
                    name=f"Target_{state.year}_{i+1}",
                    company_type=self.rng.choice(types),
                    revenue=revenue,
                    ebitda=revenue * ebitda_margin,
                    asking_ev_ebitda=self.rng.uniform(3.5, 7.0),
                    headcount=self.rng.randint(80, 1200),
                    revenue_growth_rate=self.rng.uniform(0.02, 0.15),
                ))
        return targets

    def _gen_late_stage(self, state: SimulationState, count: int) -> list[AcquisitionTarget]:
        """Phase 5-6: global scale, larger strategic targets."""
        targets = []
        types = list(CompanyType)
        for i in range(count):
            # 20% chance of strategic high-growth target
            is_strategic = self.rng.random() < 0.20
            if is_strategic:
                targets.append(self._gen_strategic_target(state, i, scale="large"))
            else:
                revenue = self.rng.uniform(200_0000_0000, 5000_0000_0000)
                ebitda_margin = self.rng.uniform(0.12, 0.25)
                targets.append(AcquisitionTarget(
                    name=f"Target_{state.year}_{i+1}",
                    company_type=self.rng.choice(types),
                    revenue=revenue,
                    ebitda=revenue * ebitda_margin,
                    asking_ev_ebitda=self.rng.uniform(4.0, 8.0),
                    headcount=self.rng.randint(300, 5000),
                    revenue_growth_rate=self.rng.uniform(0.03, 0.12),
                ))
        return targets

    def _gen_strategic_target(
        self, state: SimulationState, idx: int, scale: str,
    ) -> AcquisitionTarget:
        """Generate a strategic high-growth acquisition target.

        These are the Instagram / Manus AI type deals:
        - Very high revenue growth (50-200%+)
        - May be pre-profit or low-margin
        - Have tech moat or distribution moat
        - Valued on revenue multiples, not EBITDA
        """
        if scale == "mid":
            revenue = self.rng.uniform(5_0000_0000, 100_0000_0000)
        else:
            revenue = self.rng.uniform(50_0000_0000, 1000_0000_0000)

        growth_rate = self.rng.uniform(0.50, 2.50)  # 50-250% annual growth
        ebitda_margin = self.rng.uniform(-0.10, 0.10)  # may be unprofitable

        has_tech = self.rng.random() < 0.70
        has_dist = self.rng.random() < 0.60
        tags = []
        if has_tech:
            tags.append("proprietary_technology")
        if has_dist:
            tags.append("distribution_network")
        if growth_rate > 1.0:
            tags.append("hypergrowth")

        # Strategic targets command higher multiples on revenue
        rev_multiple = 3.0 + growth_rate * 2.0  # 4x-8x revenue
        implied_ev_ebitda = 50.0  # effectively irrelevant; priced on revenue

        types_for_strategic = [
            CompanyType.VENTURE, CompanyType.EXPERIENCE, CompanyType.PRODUCT,
        ]

        return AcquisitionTarget(
            name=f"Strategic_{state.year}_{idx+1}",
            company_type=self.rng.choice(types_for_strategic),
            revenue=revenue,
            ebitda=max(0, revenue * ebitda_margin),
            asking_ev_ebitda=implied_ev_ebitda,  # not used for pricing
            headcount=self.rng.randint(20, 500),
            is_strategic=True,
            revenue_growth_rate=growth_rate,
            has_tech_moat=has_tech,
            has_distribution_moat=has_dist,
            competitive_advantage_tags=tags,
        )

    def evaluate_target(
        self,
        target: AcquisitionTarget,
        state: SimulationState,
    ) -> bool:
        """Decide whether to proceed with acquisition.

        Two tracks:
        1. Standard: strict EBITDA multiple discipline
        2. Strategic exception: revenue growth + moat evaluation
        """
        config = state.config.ma

        # Check group leverage constraint (applies to all deals)
        current_debt = sum(
            c.acquisition_price * 0.4 for c in state.holding.companies
        )
        current_ebitda = sum(c.ebitda for c in state.holding.companies) * 4
        if current_ebitda > 0:
            current_leverage = current_debt / current_ebitda
            if current_leverage >= config.group_max_leverage:
                return False

        if target.is_strategic:
            return self._evaluate_strategic(target, state)
        else:
            return self._evaluate_standard(target, state, config)

    def _evaluate_standard(self, target, state, config) -> bool:
        """Standard deal: strict multiple discipline. Buy cheap."""
        # Hard ceiling: target_ev_ebitda * 1.1 (tight discipline)
        if target.asking_ev_ebitda > config.target_ev_ebitda * 1.1:
            return False

        _, _, success_rate = self._phase_params(
            state.current_phase.phase if state.current_phase else 1
        )
        return self.rng.random() < success_rate

    def _evaluate_strategic(self, target: AcquisitionTarget, state) -> bool:
        """Strategic exception: evaluate on growth + moat, not EBITDA multiple.

        Criteria (must meet ALL):
        1. Revenue growth rate > 50% annually
        2. At least one strong moat (tech OR distribution)
        3. Affordable relative to group EV (< 15% of current EV)
        """
        # Gate 1: growth threshold
        if target.revenue_growth_rate < 0.50:
            return False

        # Gate 2: must have at least one moat
        if not target.has_tech_moat and not target.has_distribution_moat:
            return False

        # Gate 3: affordability (don't bet the farm)
        price = target.asking_price
        group_ev = state.holding.enterprise_value
        if group_ev > 0 and price > group_ev * 0.15:
            return False

        # Higher success rate for clearly exceptional targets
        base_rate = 0.30
        if target.has_tech_moat and target.has_distribution_moat:
            base_rate = 0.50
        if target.revenue_growth_rate > 1.0:
            base_rate += 0.10

        return self.rng.random() < min(0.60, base_rate)

    def execute_acquisition(
        self,
        target: AcquisitionTarget,
        state: SimulationState,
    ) -> Company:
        """Execute an acquisition and add to portfolio."""
        price = target.asking_price

        company = Company(
            id=f"co_{state.year}_{len(state.holding.companies)+1}",
            name=target.name,
            company_type=target.company_type,
            acquired_year=state.year,
            acquisition_price=price,
            acquisition_ebitda=target.ebitda,
            revenue=target.revenue,
            ebitda=target.ebitda,
            operating_margin=target.ebitda / target.revenue if target.revenue > 0 else 0,
            headcount=target.headcount,
            pmi_phase=1,
            # Lifecycle: strategic targets start in growth phase
            lifecycle_stage="growth" if target.is_strategic else "maturity",
            revenue_growth_rate=target.revenue_growth_rate,
        )

        state.holding.companies.append(company)
        state.ma_events.append({
            "year": state.year,
            "quarter": state.quarter,
            "company": company.name,
            "price": price,
            "ebitda": target.ebitda,
            "ev_ebitda": target.asking_ev_ebitda,
            "is_strategic": target.is_strategic,
            "revenue_growth": target.revenue_growth_rate,
            "moats": target.competitive_advantage_tags,
        })

        return company

    def advance_pmi(self, company: Company, quarters_since_acquisition: int) -> None:
        """Advance PMI and apply EBITDA improvements."""
        if company.pmi_phase >= 4:
            return

        if quarters_since_acquisition <= 2:
            company.pmi_phase = 1
            improvement = 0.05 / 2
        elif quarters_since_acquisition <= 6:
            company.pmi_phase = 2
            improvement = 0.125 / 4
        elif quarters_since_acquisition <= 12:
            company.pmi_phase = 3
            improvement = 0.15 / 6
        else:
            company.pmi_phase = 4
            return

        company.ebitda *= (1 + improvement)
        if company.revenue > 0:
            company.operating_margin = company.ebitda / company.revenue

    def compute_synergies(self, state: SimulationState) -> float:
        """Compute group-level synergies (scales with portfolio size)."""
        n_companies = len(state.holding.companies)
        if n_companies < 2:
            return 0.0

        total_cogs = sum(c.revenue * 0.55 for c in state.holding.companies)
        procurement_saving_rate = min(0.08, 0.03 + 0.003 * n_companies)
        procurement_synergy = total_cogs * procurement_saving_rate

        # Shared services scale with company count
        shared_services_saving = n_companies * 1000_0000  # 1000万 per company

        # Cross-sell synergy: grows quadratically with portfolio
        cross_sell = n_companies * (n_companies - 1) * 500_0000  # pairwise

        return procurement_synergy + shared_services_saving + cross_sell
