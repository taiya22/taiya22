"""M&A engine: acquisition pipeline, PMI, synergy modeling.

Incorporates M&A strategy typology and academic research:

**M&A Types (strategy dimension):**
- Horizontal: same industry, scale economies (Capron 1999, Chatterjee 1986)
- Vertical: supply chain integration (Fan & Goyal 2006)
- Roll-up: serial acquisitions in fragmented industry (Kengelbach et al. 2012)
- Related Diversification: adjacent industry, shared capabilities (Rumelt 1982)
- Unrelated Diversification: conglomerate expansion (Berger & Ofek 1995)

**Key research findings modeled:**
1. Horizontal M&A has highest synergy potential but antitrust risk (Chatterjee 1986)
2. Roll-up creates value through learning curve + platform effect (Kengelbach 2012)
3. Related diversification outperforms unrelated (Rumelt 1982, Markides & Williamson 1994)
4. Organizational learning improves PMI over time (Haleblian & Finkelstein 1999, Hayward 2002)
5. Relative deal size affects integration risk (Kitching 1967, Ellis et al. 2011)
6. Acquisition frequency has inverted-U effect on performance (Laamanen & Keil 2008)
7. Time between deals needed for absorption (Hayward 2002: optimal gap ~1-3 years early on)

**Acquisition discipline:**
- Standard deals: strict EV/EBITDA multiple discipline (buy cheap)
- Strategic exception: high-growth targets with overwhelming competitive
  advantages (Instagram-type, Manus AI-type) evaluated on revenue growth
  + strategic value, not EBITDA multiples.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from taiga_sim.models.simulation import SimulationState

from taiga_sim.models.organization import Company, CompanyType


class MAType(Enum):
    """M&A strategy type."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    ROLL_UP = "roll_up"
    RELATED_DIVERSIFICATION = "related_diversification"
    UNRELATED_DIVERSIFICATION = "unrelated_diversification"


# Research-based parameters per M&A type
# Sources: Chatterjee 1986, Rumelt 1982, Kengelbach 2012, Berger & Ofek 1995
MA_TYPE_PARAMS = {
    #                          base_success synergy_pct  pmi_speed  integration_risk
    MAType.HORIZONTAL:         (0.55,       0.12,        1.0,       0.15),
    MAType.VERTICAL:           (0.50,       0.08,        0.85,      0.20),
    MAType.ROLL_UP:            (0.60,       0.06,        1.20,      0.10),
    MAType.RELATED_DIVERSIFICATION:   (0.45, 0.07,       0.90,      0.18),
    MAType.UNRELATED_DIVERSIFICATION: (0.35, 0.03,       0.70,      0.30),
}


@dataclass
class AcquisitionTarget:
    """A potential acquisition target."""

    name: str
    company_type: CompanyType
    revenue: float
    ebitda: float
    asking_ev_ebitda: float
    headcount: int

    # M&A type classification
    ma_type: MAType = MAType.HORIZONTAL

    # Strategic exception fields
    is_strategic: bool = False
    revenue_growth_rate: float = 0.05
    has_tech_moat: bool = False
    has_distribution_moat: bool = False
    competitive_advantage_tags: list[str] = field(default_factory=list)

    @property
    def asking_price(self) -> float:
        if self.is_strategic and self.ebitda <= 0:
            return self.revenue * self._strategic_revenue_multiple
        return self.ebitda * self.asking_ev_ebitda

    @property
    def _strategic_revenue_multiple(self) -> float:
        base = 3.0
        if self.revenue_growth_rate > 1.0:
            base = 8.0
        elif self.revenue_growth_rate > 0.5:
            base = 5.0
        return base


# Phase-based M&A parameters (calibrated to match requirements targets)
PHASE_MA_PARAMS = {
    # phase: (pipeline_size, max_acquisitions, deal_success_rate_modifier)
    0: (0, 0, 0),
    1: (5, 2, 1.0),    # survival: small bolt-ons
    2: (6, 2, 1.0),    # takeoff: building foundation
    3: (6, 2, 1.0),    # expansion: selective larger deals
    4: (6, 1, 1.0),    # dominance: quality over quantity
    5: (6, 1, 1.0),    # IPO: fewer but transformative
    6: (6, 1, 1.0),    # global: very selective large-scale
}


class MAEngine:
    """Handles M&A pipeline, execution, PMI with organizational learning."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        # Organizational learning state
        self.cumulative_deals: int = 0
        self.deals_by_type: dict[MAType, int] = {t: 0 for t in MAType}
        self.recent_deal_years: list[int] = []  # years of recent deals for frequency tracking
        self.pmi_learning_factor: float = 1.0  # improves with experience

    def _phase_params(self, phase_num: int) -> tuple[int, int, float]:
        return PHASE_MA_PARAMS.get(phase_num, (5, 1, 1.0))

    # -----------------------------------------------------------------------
    # Organizational Learning (Haleblian & Finkelstein 1999, Hayward 2002)
    # -----------------------------------------------------------------------

    def _update_learning(self, ma_type: MAType, year: int) -> None:
        """Update organizational M&A capability after each deal."""
        self.cumulative_deals += 1
        self.deals_by_type[ma_type] += 1
        self.recent_deal_years.append(year)

        # Learning curve: PMI efficiency improves with experience
        # Haleblian & Finkelstein 1999: U-shaped learning curve
        # First few deals: overconfidence risk; then genuine learning kicks in
        n = self.cumulative_deals
        if n <= 2:
            self.pmi_learning_factor = 0.85  # early deals: slight penalty (learning to learn)
        elif n <= 5:
            self.pmi_learning_factor = 1.0 + (n - 2) * 0.05  # rapid learning
        elif n <= 15:
            self.pmi_learning_factor = 1.15 + (n - 5) * 0.02  # steady improvement
        else:
            self.pmi_learning_factor = min(1.50, 1.35 + (n - 15) * 0.005)  # plateau

    def _type_experience_bonus(self, ma_type: MAType) -> float:
        """Extra success rate for experience in a specific M&A type.

        Roll-up benefits most from repetition (Kengelbach 2012).
        """
        n = self.deals_by_type[ma_type]
        if ma_type == MAType.ROLL_UP:
            return min(0.15, n * 0.03)  # roll-up: strong learning effect
        return min(0.10, n * 0.015)  # others: moderate

    def _frequency_penalty(self, year: int) -> float:
        """Penalty for too-frequent acquisitions (Laamanen & Keil 2008).

        Inverted-U: optimal is 1-3 deals/year. >4 deals/year causes
        integration overload and value destruction.
        """
        deals_last_2y = sum(1 for y in self.recent_deal_years if y >= year - 1)
        if deals_last_2y <= 3:
            return 0.0  # optimal range
        elif deals_last_2y <= 6:
            return (deals_last_2y - 3) * 0.03  # mild penalty
        else:
            return min(0.25, (deals_last_2y - 3) * 0.05)  # significant overload

    def _relative_size_risk(self, target_revenue: float, group_revenue: float) -> float:
        """Integration risk from relative deal size (Kitching 1967, Ellis et al. 2011).

        Deals >30% of acquirer's size have significantly higher failure rates.
        Deals <5% are low-risk but may not move the needle.
        """
        if group_revenue <= 0:
            return 0.0
        ratio = target_revenue / group_revenue
        if ratio < 0.05:
            return -0.05  # small bolt-on: slightly easier
        elif ratio < 0.15:
            return 0.0  # sweet spot
        elif ratio < 0.30:
            return 0.05  # manageable but adds risk
        elif ratio < 0.50:
            return 0.12  # significant integration risk
        else:
            return 0.25  # transformational: very high risk

    # -----------------------------------------------------------------------
    # Pipeline Generation
    # -----------------------------------------------------------------------

    def _classify_ma_type(
        self, target_type: CompanyType, state: SimulationState,
    ) -> MAType:
        """Classify the M&A type based on target vs existing portfolio."""
        existing_types = [c.company_type for c in state.holding.companies]
        same_type_count = sum(1 for t in existing_types if t == target_type)

        if same_type_count >= 3:
            # Many companies of same type -> roll-up pattern
            return MAType.ROLL_UP
        elif same_type_count >= 1:
            # Same type exists -> horizontal consolidation
            return MAType.HORIZONTAL
        else:
            # New type for portfolio
            n_types = len(set(existing_types))
            if n_types >= 4:
                return MAType.UNRELATED_DIVERSIFICATION
            elif target_type in (CompanyType.PRODUCT, CompanyType.TERRA):
                return MAType.RELATED_DIVERSIFICATION
            else:
                # Check for vertical relationship (simplified)
                if (target_type == CompanyType.STRATEGY and
                        CompanyType.VENTURE in existing_types):
                    return MAType.VERTICAL
                return MAType.RELATED_DIVERSIFICATION

    def generate_pipeline(self, state: SimulationState) -> list[AcquisitionTarget]:
        """Generate M&A pipeline for the current year based on phase."""
        phase = state.current_phase
        if phase is None:
            return []

        pipeline_size, _, _ = self._phase_params(phase.phase)
        if pipeline_size == 0:
            return []

        count = max(1, pipeline_size + self.rng.randint(-3, 3))

        if phase.phase <= 2:
            targets = self._gen_early_stage(state, count)
        elif phase.phase <= 4:
            targets = self._gen_mid_stage(state, count)
        else:
            targets = self._gen_late_stage(state, count)

        # Classify M&A type for each target
        for t in targets:
            if not t.is_strategic:
                t.ma_type = self._classify_ma_type(t.company_type, state)

        return targets

    def _gen_early_stage(self, state, count) -> list[AcquisitionTarget]:
        targets = []
        for i in range(count):
            revenue = self.rng.uniform(3_0000_0000, 15_0000_0000)
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

    def _gen_mid_stage(self, state, count) -> list[AcquisitionTarget]:
        """Phase 3-4: mid-size diversified targets."""
        targets = []
        types = list(CompanyType)
        for i in range(count):
            is_strategic = self.rng.random() < 0.10
            if is_strategic:
                targets.append(self._gen_strategic_target(state, i, "mid"))
            else:
                revenue = self.rng.uniform(15_0000_0000, 80_0000_0000)
                ebitda_margin = self.rng.uniform(0.10, 0.20)
                targets.append(AcquisitionTarget(
                    name=f"Target_{state.year}_{i+1}",
                    company_type=self.rng.choice(types),
                    revenue=revenue,
                    ebitda=revenue * ebitda_margin,
                    asking_ev_ebitda=self.rng.uniform(3.5, 6.5),
                    headcount=self.rng.randint(50, 500),
                    revenue_growth_rate=self.rng.uniform(0.02, 0.10),
                ))
        return targets

    def _gen_late_stage(self, state, count) -> list[AcquisitionTarget]:
        """Phase 5-6: larger but disciplined targets."""
        targets = []
        types = list(CompanyType)
        for i in range(count):
            is_strategic = self.rng.random() < 0.12
            if is_strategic:
                targets.append(self._gen_strategic_target(state, i, "large"))
            else:
                revenue = self.rng.uniform(50_0000_0000, 500_0000_0000)
                ebitda_margin = self.rng.uniform(0.10, 0.22)
                targets.append(AcquisitionTarget(
                    name=f"Target_{state.year}_{i+1}",
                    company_type=self.rng.choice(types),
                    revenue=revenue,
                    ebitda=revenue * ebitda_margin,
                    asking_ev_ebitda=self.rng.uniform(4.0, 7.5),
                    headcount=self.rng.randint(100, 2000),
                    revenue_growth_rate=self.rng.uniform(0.02, 0.08),
                ))
        return targets

    def _gen_strategic_target(self, state, idx, scale) -> AcquisitionTarget:
        """Instagram / Manus AI type: hypergrowth + moat."""
        if scale == "mid":
            revenue = self.rng.uniform(3_0000_0000, 50_0000_0000)
        else:
            revenue = self.rng.uniform(20_0000_0000, 300_0000_0000)

        growth_rate = self.rng.uniform(0.50, 2.50)
        ebitda_margin = self.rng.uniform(-0.10, 0.10)

        has_tech = self.rng.random() < 0.70
        has_dist = self.rng.random() < 0.60
        tags = []
        if has_tech:
            tags.append("proprietary_technology")
        if has_dist:
            tags.append("distribution_network")
        if growth_rate > 1.0:
            tags.append("hypergrowth")

        types_for_strategic = [
            CompanyType.VENTURE, CompanyType.EXPERIENCE, CompanyType.PRODUCT,
        ]

        return AcquisitionTarget(
            name=f"Strategic_{state.year}_{idx+1}",
            company_type=self.rng.choice(types_for_strategic),
            revenue=revenue,
            ebitda=max(0, revenue * ebitda_margin),
            asking_ev_ebitda=50.0,  # not used; priced on revenue
            headcount=self.rng.randint(20, 500),
            is_strategic=True,
            revenue_growth_rate=growth_rate,
            has_tech_moat=has_tech,
            has_distribution_moat=has_dist,
            competitive_advantage_tags=tags,
            ma_type=MAType.RELATED_DIVERSIFICATION,  # strategic = related by definition
        )

    # -----------------------------------------------------------------------
    # Evaluation
    # -----------------------------------------------------------------------

    def evaluate_target(
        self,
        target: AcquisitionTarget,
        state: SimulationState,
    ) -> bool:
        """Two-track evaluation: standard discipline vs strategic exception."""
        config = state.config.ma

        # Leverage constraint (all deals)
        current_debt = sum(c.acquisition_price * 0.4 for c in state.holding.companies)
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
        """Standard: strict multiple discipline + type-based success rate."""
        # Price discipline (tight ceiling)
        if target.asking_ev_ebitda > config.target_ev_ebitda * 1.1:
            return False

        # Base success rate from M&A type research
        base_success, _, _, integration_risk = MA_TYPE_PARAMS[target.ma_type]

        # Modifiers
        type_bonus = self._type_experience_bonus(target.ma_type)
        freq_penalty = self._frequency_penalty(state.year)

        group_revenue = sum(c.revenue for c in state.holding.companies) * 4
        size_risk = self._relative_size_risk(target.revenue * 4, group_revenue)

        adjusted_success = base_success + type_bonus - freq_penalty - size_risk

        # Phase modifier
        _, _, phase_mod = self._phase_params(
            state.current_phase.phase if state.current_phase else 1
        )
        adjusted_success *= phase_mod

        adjusted_success = max(0.10, min(0.70, adjusted_success))
        return self.rng.random() < adjusted_success

    def _evaluate_strategic(self, target: AcquisitionTarget, state) -> bool:
        """Strategic exception for high-growth/moat targets."""
        if target.revenue_growth_rate < 0.50:
            return False
        if not target.has_tech_moat and not target.has_distribution_moat:
            return False

        price = target.asking_price
        group_ev = state.holding.enterprise_value
        if group_ev > 0 and price > group_ev * 0.15:
            return False

        base_rate = 0.25
        if target.has_tech_moat and target.has_distribution_moat:
            base_rate = 0.40
        if target.revenue_growth_rate > 1.0:
            base_rate += 0.05

        # Learning bonus for strategic deals too
        base_rate += min(0.10, self.cumulative_deals * 0.005)

        return self.rng.random() < min(0.50, base_rate)

    def execute_acquisition(
        self,
        target: AcquisitionTarget,
        state: SimulationState,
    ) -> Company:
        """Execute acquisition and update learning state."""
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
            lifecycle_stage="growth" if target.is_strategic else "maturity",
            revenue_growth_rate=target.revenue_growth_rate,
        )

        state.holding.companies.append(company)

        # Update organizational learning
        self._update_learning(target.ma_type, state.year)

        state.ma_events.append({
            "year": state.year,
            "quarter": state.quarter,
            "company": company.name,
            "price": price,
            "ebitda": target.ebitda,
            "ev_ebitda": target.asking_ev_ebitda,
            "ma_type": target.ma_type.value,
            "is_strategic": target.is_strategic,
            "revenue_growth": target.revenue_growth_rate,
            "moats": target.competitive_advantage_tags,
            "cumulative_deals": self.cumulative_deals,
            "pmi_learning_factor": self.pmi_learning_factor,
        })

        return company

    # -----------------------------------------------------------------------
    # PMI with organizational learning
    # -----------------------------------------------------------------------

    def advance_pmi(
        self,
        company: Company,
        quarters_since_acquisition: int,
        operating_system_maturity: float = 0.0,
        os_margin_improvement: float = 0.065,
    ) -> None:
        """Advance PMI with learning-adjusted improvement rates.

        Learning factor (Haleblian & Finkelstein 1999):
        - More experienced acquirers extract more value from PMI
        - Type-specific experience matters (roll-up best)

        Operating system effect (Danaher DBS):
        - Mature operating system adds +600-700bps margin improvement
        - Applied proportionally to OS maturity during PMI phases 2-4

        Relative size effect (Ellis et al. 2011):
        - Larger relative acquisitions take longer to integrate
        """
        if company.pmi_phase >= 4:
            return

        # Base improvement by phase
        if quarters_since_acquisition <= 2:
            company.pmi_phase = 1
            base_improvement = 0.05 / 2
        elif quarters_since_acquisition <= 6:
            company.pmi_phase = 2
            base_improvement = 0.125 / 4
        elif quarters_since_acquisition <= 12:
            company.pmi_phase = 3
            base_improvement = 0.15 / 6
        else:
            company.pmi_phase = 4
            return

        # Apply organizational learning factor
        improvement = base_improvement * self.pmi_learning_factor

        # Operating system (DBS-like) margin improvement
        # Danaher: +600-700bps on acquisitions, applied during PMI phases 2-4
        # Scales with OS maturity (0 = no effect, 1.0 = full 650bps)
        if operating_system_maturity > 0 and company.pmi_phase >= 2:
            # Distribute the OS improvement across PMI phases 2-4 (~10 quarters)
            quarterly_os_improvement = (
                os_margin_improvement * operating_system_maturity / 10
            )
            improvement += quarterly_os_improvement

        company.ebitda *= (1 + improvement)
        if company.revenue > 0:
            company.operating_margin = company.ebitda / company.revenue

    # -----------------------------------------------------------------------
    # Synergies (type-dependent)
    # -----------------------------------------------------------------------

    def compute_synergies(self, state: SimulationState) -> float:
        """Compute group-level synergies, weighted by M&A type mix.

        Horizontal + Roll-up: highest synergies (Chatterjee 1986)
        Vertical: moderate (supply chain)
        Related Diversification: moderate (shared capabilities)
        Unrelated: lowest (Berger & Ofek 1995)
        """
        n_companies = len(state.holding.companies)
        if n_companies < 2:
            return 0.0

        total_cogs = sum(c.revenue * 0.55 for c in state.holding.companies)

        # Synergy rate based on portfolio composition
        # More same-type companies = higher synergy (horizontal/roll-up effect)
        type_counts = {}
        for c in state.holding.companies:
            type_counts[c.company_type] = type_counts.get(c.company_type, 0) + 1

        # Procurement synergy: scales with concentration
        max_cluster = max(type_counts.values()) if type_counts else 0
        cluster_bonus = min(0.04, max_cluster * 0.008)  # roll-up procurement benefit
        base_procurement_rate = min(0.08, 0.02 + 0.002 * n_companies + cluster_bonus)
        procurement_synergy = total_cogs * base_procurement_rate

        # Shared services
        shared_services = n_companies * 800_0000  # 800万 per company

        # Cross-sell (only within related companies)
        n_types = len(type_counts)
        cross_sell = 0.0
        for t, count in type_counts.items():
            if count >= 2:
                cross_sell += count * (count - 1) * 300_0000  # within-type cross-sell

        # Learning-adjusted: better PMI = better synergy realization
        learning_multiplier = min(1.3, self.pmi_learning_factor * 0.9)

        return (procurement_synergy + shared_services + cross_sell) * learning_multiplier
