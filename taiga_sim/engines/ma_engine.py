"""M&A engine: acquisition pipeline, PMI, synergy modeling."""

from __future__ import annotations

import random
from dataclasses import dataclass
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

    @property
    def asking_price(self) -> float:
        return self.ebitda * self.asking_ev_ebitda


class MAEngine:
    """Handles M&A pipeline, execution, and PMI."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def generate_pipeline(self, state: SimulationState) -> list[AcquisitionTarget]:
        """Generate M&A pipeline for the current year based on phase."""
        phase = state.current_phase
        if phase is None:
            return []

        if phase.phase <= 2:
            # Phase 1-2: small manufacturing, succession deals
            count = self.rng.randint(1, 3)
            targets = []
            for i in range(count):
                revenue = self.rng.uniform(5_0000_0000, 20_0000_0000)
                ebitda_margin = self.rng.uniform(0.08, 0.18)
                targets.append(AcquisitionTarget(
                    name=f"Target_{state.year}_{i+1}",
                    company_type=CompanyType.PRODUCT,
                    revenue=revenue,
                    ebitda=revenue * ebitda_margin,
                    asking_ev_ebitda=self.rng.uniform(3.0, 5.0),
                    headcount=self.rng.randint(20, 100),
                ))
            return targets

        elif phase.phase <= 4:
            # Phase 3-4: larger, diversified
            count = self.rng.randint(1, 3)
            targets = []
            types = list(CompanyType)
            for i in range(count):
                revenue = self.rng.uniform(50_0000_0000, 500_0000_0000)
                ebitda_margin = self.rng.uniform(0.10, 0.20)
                targets.append(AcquisitionTarget(
                    name=f"Target_{state.year}_{i+1}",
                    company_type=self.rng.choice(types),
                    revenue=revenue,
                    ebitda=revenue * ebitda_margin,
                    asking_ev_ebitda=self.rng.uniform(4.0, 7.0),
                    headcount=self.rng.randint(100, 1000),
                ))
            return targets

        else:
            # Phase 5-6: global scale
            count = self.rng.randint(1, 2)
            targets = []
            types = list(CompanyType)
            for i in range(count):
                revenue = self.rng.uniform(500_0000_0000, 5000_0000_0000)
                ebitda_margin = self.rng.uniform(0.12, 0.22)
                targets.append(AcquisitionTarget(
                    name=f"Target_{state.year}_{i+1}",
                    company_type=self.rng.choice(types),
                    revenue=revenue,
                    ebitda=revenue * ebitda_margin,
                    asking_ev_ebitda=self.rng.uniform(5.0, 8.0),
                    headcount=self.rng.randint(500, 5000),
                ))
            return targets

    def evaluate_target(
        self,
        target: AcquisitionTarget,
        state: SimulationState,
    ) -> bool:
        """Decide whether to proceed with acquisition."""
        config = state.config.ma

        # Check leverage constraint
        current_debt = sum(
            c.acquisition_price * 0.5 for c in state.holding.companies  # rough estimate
        )
        current_ebitda = sum(c.ebitda for c in state.holding.companies) * 4
        if current_ebitda > 0:
            current_leverage = current_debt / current_ebitda
            if current_leverage >= config.group_max_leverage:
                return False

        # Check price discipline
        if target.asking_ev_ebitda > config.target_ev_ebitda * 1.2:
            return False

        # Probabilistic success (DD, negotiation)
        success_rate = 0.40  # ~40% of evaluated deals close
        return self.rng.random() < success_rate

    def execute_acquisition(
        self,
        target: AcquisitionTarget,
        state: SimulationState,
    ) -> Company:
        """Execute an acquisition and add to portfolio."""
        company = Company(
            id=f"co_{state.year}_{len(state.holding.companies)+1}",
            name=target.name,
            company_type=target.company_type,
            acquired_year=state.year,
            acquisition_price=target.asking_price,
            acquisition_ebitda=target.ebitda,
            revenue=target.revenue,
            ebitda=target.ebitda,
            operating_margin=target.ebitda / target.revenue if target.revenue > 0 else 0,
            headcount=target.headcount,
            pmi_phase=1,
        )

        state.holding.companies.append(company)
        state.ma_events.append({
            "year": state.year,
            "quarter": state.quarter,
            "company": company.name,
            "price": target.asking_price,
            "ebitda": target.ebitda,
            "ev_ebitda": target.asking_ev_ebitda,
        })

        return company

    def advance_pmi(self, company: Company, quarters_since_acquisition: int) -> None:
        """Advance PMI and apply EBITDA improvements."""
        if company.pmi_phase >= 4:
            return

        if quarters_since_acquisition <= 2:
            # Phase 1: 0-6 months - +5% EBITDA improvement
            company.pmi_phase = 1
            improvement = 0.05 / 2  # spread over 2 quarters
        elif quarters_since_acquisition <= 6:
            # Phase 2: 6-18 months - +10-15%
            company.pmi_phase = 2
            improvement = 0.125 / 4  # spread over 4 quarters
        elif quarters_since_acquisition <= 12:
            # Phase 3: 18-36 months - +10-20%
            company.pmi_phase = 3
            improvement = 0.15 / 6  # spread over 6 quarters
        else:
            company.pmi_phase = 4
            return

        company.ebitda *= (1 + improvement)
        if company.revenue > 0:
            company.operating_margin = company.ebitda / company.revenue

    def compute_synergies(self, state: SimulationState) -> float:
        """Compute group-level synergies."""
        n_companies = len(state.holding.companies)
        if n_companies < 2:
            return 0.0

        # Procurement synergy: 3-8% of total group purchasing
        total_cogs = sum(c.revenue * 0.55 for c in state.holding.companies)
        procurement_saving_rate = min(0.08, 0.03 + 0.005 * n_companies)
        procurement_synergy = total_cogs * procurement_saving_rate

        # Shared services: reduces admin cost
        shared_services_saving = n_companies * 5000_000  # 500万 per company

        return procurement_synergy + shared_services_saving
