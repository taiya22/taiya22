"""Simulation configuration and state models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from taiga_sim.models.organization import HoldingCompany


@dataclass
class MacroEnvironment:
    """Macro-economic environment parameters."""

    gdp_growth_rate: float = 0.015  # 1.5%
    interest_rate: float = 0.02  # 2.0%
    shock_probability: float = 0.05  # 5% per year
    shock_ev_decline: float = -0.30  # -30%
    inflation_rate: float = 0.02

    # State
    is_shock_active: bool = False
    shock_remaining_quarters: int = 0


@dataclass
class MAConfig:
    """M&A engine configuration."""

    annual_acquisitions: int = 1  # 1-2 deals/year
    target_ev_ebitda: float = 4.0  # 3.0-8.0x
    pmi_ebitda_improvement: float = 0.30  # +30% over 3 years
    max_leverage: float = 3.0  # Net Debt/EBITDA per deal
    group_max_leverage: float = 2.5  # Group-level


@dataclass
class CompensationConfig:
    """Compensation system configuration."""

    base_salary_ratio: float = 0.75  # 同業他社の75%
    bonus_pool_rate: float = 0.20  # 営業利益 × 20%
    profit_sharing_rate: float = 0.12  # 企業価値増加 × 12%
    foundation_fcf_rate: float = 0.05  # FCF × 5%
    keshiki_reserve_rate: float = 0.075  # 利益 × 5-10%


@dataclass
class HRConfig:
    """Human resources configuration."""

    annual_turnover_rate: float = 0.05  # 5%
    hiring_cost_per_person: float = 300_0000  # 300万円
    founder_salary_phase1: float = 180_0000  # 年180万円


@dataclass
class PhaseDefinition:
    """Definition of a simulation phase."""

    phase: int
    name: str
    start_year: int
    end_year: int
    description: str
    revenue_target: float = 0.0
    ebitda_target: float = 0.0
    ev_target: float = 0.0


# Default phase definitions from the requirements
DEFAULT_PHASES = [
    PhaseDefinition(0, "調達", 0, 0, "5億円調達, Post-money 50億円",
                    ev_target=50_0000_0000),
    PhaseDefinition(1, "サバイバル", 1, 3, "事業承継M&Aで2-3社買収",
                    revenue_target=30_0000_0000, ebitda_target=5_0000_0000),
    PhaseDefinition(2, "離陸", 4, 6, "売上30-70億, 利益分配開始",
                    revenue_target=70_0000_0000, ebitda_target=20_0000_0000),
    PhaseDefinition(3, "拡大", 7, 10, "VCセカンダリー, 大型LBO",
                    revenue_target=1000_0000_0000, ebitda_target=150_0000_0000),
    PhaseDefinition(4, "支配", 11, 15, "売上2000億, 財団本格化",
                    revenue_target=2000_0000_0000, ebitda_target=400_0000_0000),
    PhaseDefinition(5, "上場", 16, 20, "IPO, 時価総額1兆円",
                    revenue_target=5000_0000_0000, ebitda_target=1000_0000_0000,
                    ev_target=1_0000_0000_0000),
    PhaseDefinition(6, "グローバル", 21, 30, "時価総額30兆円目標",
                    revenue_target=30000_0000_0000, ebitda_target=6000_0000_0000,
                    ev_target=30_0000_0000_0000),
]


@dataclass
class SimulationConfig:
    """Master configuration for the entire simulation."""

    total_years: int = 30
    quarters_per_year: int = 4
    seed_funding: float = 5_0000_0000  # 5億円
    initial_equity_dilution: float = 0.10  # 10% to investors

    macro: MacroEnvironment = field(default_factory=MacroEnvironment)
    ma: MAConfig = field(default_factory=MAConfig)
    compensation: CompensationConfig = field(default_factory=CompensationConfig)
    hr: HRConfig = field(default_factory=HRConfig)
    phases: list[PhaseDefinition] = field(default_factory=lambda: list(DEFAULT_PHASES))

    # IPO / control
    ipo_target_year: int = 20
    ipo_founder_ownership: float = 0.40
    ipo_stable_shareholder_pct: float = 0.15
    listing_market: str = "tse_prime"

    # Portfolio target mix (revenue %) by year 30
    portfolio_target: dict[str, float] = field(default_factory=lambda: {
        "product": 0.25,
        "experience": 0.15,
        "strategy": 0.15,
        "venture": 0.15,
        "terra": 0.30,
    })

    # Crisis resilience
    portfolio_resilience_layer: float = 0.70  # 耐性層
    portfolio_adaptation_layer: float = 0.20  # 適応層
    portfolio_opportunity_layer: float = 0.10  # 機会層


@dataclass
class SimulationState:
    """Complete state of the simulation at a point in time."""

    year: int = 0
    quarter: int = 1
    holding: HoldingCompany = field(default_factory=HoldingCompany)
    config: SimulationConfig = field(default_factory=SimulationConfig)
    macro: MacroEnvironment = field(default_factory=MacroEnvironment)

    # Tracking
    annual_ev_history: list[float] = field(default_factory=list)
    annual_revenue_history: list[float] = field(default_factory=list)
    annual_ebitda_history: list[float] = field(default_factory=list)
    annual_fcf_history: list[float] = field(default_factory=list)
    crisis_events: list[dict] = field(default_factory=list)
    ma_events: list[dict] = field(default_factory=list)

    @property
    def current_phase(self) -> Optional[PhaseDefinition]:
        for phase in self.config.phases:
            if phase.start_year <= self.year <= phase.end_year:
                return phase
        return None
