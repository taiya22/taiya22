"""Simulation configuration and state models."""

from __future__ import annotations

from dataclasses import dataclass, field

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

    # Phase-based: overridden by MAEngine.PHASE_MA_PARAMS
    annual_acquisitions: int = 2  # default; actual is phase-dependent
    target_ev_ebitda: float = 4.5  # standard discipline ceiling
    pmi_ebitda_improvement: float = 0.30  # +30% over 3 years
    max_leverage: float = 3.0  # Net Debt/EBITDA per deal
    group_max_leverage: float = 2.5  # Group-level
    # Strategic exception: allow revenue-based valuation for high-growth targets
    strategic_growth_threshold: float = 0.50  # 50%+ revenue growth
    strategic_max_pct_of_ev: float = 0.15  # max 15% of group EV per deal


@dataclass
class CompensationConfig:
    """Compensation system configuration."""

    base_salary_ratio: float = 0.75  # 同業他社の75%
    bonus_pool_rate: float = 0.20  # 営業利益 x 20%
    profit_sharing_rate: float = 0.12  # 企業価値増加 x 12%
    foundation_fcf_rate: float = 0.05  # FCF x 5%
    keshiki_reserve_rate: float = 0.075  # 利益 x 5-10%


@dataclass
class ConglomeratePremiumConfig:
    """Conglomerate premium/discount parameters based on academic research.

    Sources:
    - Berger & Ofek (1995): -13% to -15% unrelated diversification discount
    - Villalonga (2004): related diversification yields premium
    - Research Affiliates (2026): tech conglomerates avg +70% premium
    - Stein (1997): monitoring efficiency decays with # divisions
    - Danaher: operating system yields +600-700bps margin improvement
    - Khanna & Palepu (2000): emerging market premium
    - Schommer et al. (2019): diversification effect becomes more positive over time
    """

    # Base discount for unrelated diversification (Berger & Ofek 1995)
    unrelated_discount: float = -0.14  # -14% midpoint of -13% to -15%
    # Premium for related diversification (Villalonga 2004)
    related_premium: float = 0.10  # +10%
    # Max tech/platform conglomerate premium (Research Affiliates 2026)
    platform_premium_max: float = 0.40  # up to +40% (conservative vs 70% avg)

    # PMI capability parameters (Danaher DBS-like)
    pmi_margin_improvement: float = 0.065  # +650bps per acquisition
    pmi_capability_years: int = 5  # years to develop full PMI capability
    acquisition_multiple_arbitrage: float = 0.45  # effective multiple halving

    # Monitoring efficiency decay (Stein 1997)
    monitoring_decay_threshold: int = 6  # # of companies before decay starts
    monitoring_decay_rate: float = 0.02  # per company above threshold

    # Governance quality multiplier range
    governance_bonus_max: float = 0.10  # strong governance eliminates discount
    governance_penalty_max: float = -0.10  # weak governance amplifies discount

    # Optimal diversification: inverted U-shape (Arte & Larimo 2022)
    optimal_segment_count: int = 3  # peak of inverted-U
    diversification_curve_width: float = 2.5  # width of the bell

    # Japanese market context
    japan_institutional_discount: float = -0.05  # weaker institutions = less discount
    # Keiretsu stability benefit: lower earnings volatility
    stability_volatility_reduction: float = 0.15  # 15% lower earnings volatility


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
    PhaseDefinition(0, "調達", 0, 0, "5億円調達, Post-money 50億円", ev_target=50_0000_0000),
    PhaseDefinition(
        1,
        "サバイバル",
        1,
        3,
        "事業承継M&Aで2-3社買収",
        revenue_target=30_0000_0000,
        ebitda_target=5_0000_0000,
    ),
    PhaseDefinition(
        2,
        "離陸",
        4,
        6,
        "売上30-70億, 利益分配開始",
        revenue_target=70_0000_0000,
        ebitda_target=20_0000_0000,
    ),
    PhaseDefinition(
        3,
        "拡大",
        7,
        10,
        "VCセカンダリー, 大型LBO",
        revenue_target=1000_0000_0000,
        ebitda_target=150_0000_0000,
    ),
    PhaseDefinition(
        4,
        "支配",
        11,
        15,
        "売上2000億, 財団本格化",
        revenue_target=2000_0000_0000,
        ebitda_target=400_0000_0000,
    ),
    PhaseDefinition(
        5,
        "上場",
        16,
        20,
        "IPO, 時価総額1兆円",
        revenue_target=5000_0000_0000,
        ebitda_target=1000_0000_0000,
        ev_target=1_0000_0000_0000,
    ),
    PhaseDefinition(
        6,
        "グローバル",
        21,
        30,
        "時価総額30兆円目標",
        revenue_target=30000_0000_0000,
        ebitda_target=6000_0000_0000,
        ev_target=30_0000_0000_0000,
    ),
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
    conglomerate: ConglomeratePremiumConfig = field(default_factory=ConglomeratePremiumConfig)
    phases: list[PhaseDefinition] = field(default_factory=lambda: list(DEFAULT_PHASES))

    # IPO / control
    ipo_target_year: int = 20
    ipo_founder_ownership: float = 0.40
    ipo_stable_shareholder_pct: float = 0.15
    listing_market: str = "tse_prime"

    # Portfolio target mix (revenue %) by year 30
    portfolio_target: dict[str, float] = field(
        default_factory=lambda: {
            "product": 0.25,
            "experience": 0.15,
            "strategy": 0.15,
            "venture": 0.15,
            "terra": 0.30,
        }
    )

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
    def current_phase(self) -> PhaseDefinition | None:
        for phase in self.config.phases:
            if phase.start_year <= self.year <= phase.end_year:
                return phase
        return None
