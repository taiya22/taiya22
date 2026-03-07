"""Organization models: members, units, companies, holding company."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class UnitType(Enum):
    """The three special units (特殊部隊)."""

    CREATION = "creation"  # 事業創造ユニット
    TURNAROUND = "turnaround"  # 事業再生ユニット
    OPERATING = "operating"  # 経営管理ユニット


class CompanyType(Enum):
    """Five company types in the portfolio."""

    PRODUCT = "product"  # Product Company (農業・ロボティクス・製造業)
    EXPERIENCE = "experience"  # Experience Studio (エンタメ・食・宇宙)
    STRATEGY = "strategy"  # Strategy and Investment (PE投資)
    VENTURE = "venture"  # Venture Studio (事業開発・VC)
    TERRA = "terra"  # Terra Estate (不動産・インフラ・森林)


class MemberGrade(Enum):
    """Member grade for talent placement."""

    S = "S"  # Outsider - Creation/Turnaround units
    A = "A"  # Top tier - HR/IR departments
    B = "B"  # Strong performer
    C = "C"  # Standard


class EvaluationCoefficient(Enum):
    """Individual evaluation coefficient (個人評価係数)."""

    EXCEPTIONAL = 1.5  # 卓越 (10-15%)
    EXCELLENT = 1.2  # 優秀 (20-25%)
    STANDARD = 1.0  # 基準 (40-50%)
    NEEDS_WORK = 0.8  # 課題あり (10-15%)
    IMPROVE = 0.5  # 要改善 (<5%)


@dataclass
class OwnershipScore:
    """Ownership Score: 5 components, each 0-20, total 0-100."""

    financial_literacy: float = 10.0  # 数字を見ている
    decision_ownership: float = 10.0  # 自分で決めている
    holistic_perspective: float = 10.0  # 全体を見ている
    strategic_vision: float = 10.0  # 未来を描いている
    skin_in_the_game: float = 10.0  # リスクを共にしている

    @property
    def total(self) -> float:
        return (
            self.financial_literacy
            + self.decision_ownership
            + self.holistic_perspective
            + self.strategic_vision
            + self.skin_in_the_game
        )

    def clamp(self) -> OwnershipScore:
        """Ensure all components are within [0, 20]."""
        return OwnershipScore(
            financial_literacy=max(0.0, min(20.0, self.financial_literacy)),
            decision_ownership=max(0.0, min(20.0, self.decision_ownership)),
            holistic_perspective=max(0.0, min(20.0, self.holistic_perspective)),
            strategic_vision=max(0.0, min(20.0, self.strategic_vision)),
            skin_in_the_game=max(0.0, min(20.0, self.skin_in_the_game)),
        )


@dataclass
class EvaluationScores:
    """4-axis evaluation scores (人事評価 4軸)."""

    scene_creation: float = 0.0  # 景色創造 (40%)
    perspective_offering: float = 0.0  # 視点の提供 (25%)
    ownership: float = 0.0  # オーナーシップ (20%)
    behind_the_scene: float = 0.0  # 裏方貢献 (15%)

    @property
    def weighted_score(self) -> float:
        return (
            self.scene_creation * 0.40
            + self.perspective_offering * 0.25
            + self.ownership * 0.20
            + self.behind_the_scene * 0.15
        )


@dataclass
class Member:
    """A member of Taiga Capital Group."""

    id: str = ""
    name: str = ""
    age: int = 25
    join_year: int = 0
    grade: MemberGrade = MemberGrade.B
    unit: Optional[UnitType] = None
    assigned_company: Optional[str] = None  # company id
    is_founder: bool = False

    # Compensation
    base_salary: float = 0.0  # annual
    self_investment: float = 0.0  # Layer 3: cumulative B-class shares held
    evaluation_coefficient: float = 1.0  # 0.5 - 1.5

    # Scores
    ownership_score: OwnershipScore = field(default_factory=OwnershipScore)
    evaluation: EvaluationScores = field(default_factory=EvaluationScores)

    # Vesting
    unvested_profit_share: list[float] = field(default_factory=list)  # 3-year vest

    @property
    def tenure_years(self) -> int:
        """Calculated during simulation based on current year."""
        return 0  # placeholder; set by engine

    def is_eligible_for_elite_unit(self, current_year: int) -> bool:
        """Check 30-year rule for Creation/Turnaround unit eligibility."""
        if self.age <= 30:
            return True
        # Exceptions for 30+ (simplified check)
        return self.grade == MemberGrade.S


@dataclass
class Unit:
    """One of the three special units."""

    unit_type: UnitType
    members: list[str] = field(default_factory=list)  # member ids


@dataclass
class Company:
    """An operating company within the group."""

    id: str = ""
    name: str = ""
    company_type: CompanyType = CompanyType.PRODUCT
    acquired_year: int = 0
    acquisition_price: float = 0.0
    acquisition_ebitda: float = 0.0

    # Current financials
    revenue: float = 0.0
    ebitda: float = 0.0
    operating_margin: float = 0.10
    roic: float = 0.10
    headcount: int = 0

    # KPI
    ltv_growth_rate: float = 0.0
    competitive_advantage_score: float = 12.5  # out of 25
    fcf: float = 0.0
    reinvestment_ratio: float = 0.50

    # Traffic light
    signal: str = "green"  # green / yellow / red
    yellow_since_year: Optional[int] = None
    red_since_year: Optional[int] = None
    consecutive_wacc_miss_years: int = 0

    # PMI tracking
    pmi_phase: int = 0  # 0=pre-PMI, 1=0-6mo, 2=6-18mo, 3=18-36mo, 4=completed

    # Product lifecycle
    lifecycle_stage: str = "maturity"  # introduction / growth / maturity / decline
    lifecycle_age: int = 0  # years since acquisition (or lifecycle reset)
    revenue_growth_rate: float = 0.05  # current annual organic growth rate


@dataclass
class HoldingCompany:
    """Taiga Capital Group holding company state."""

    companies: list[Company] = field(default_factory=list)
    units: list[Unit] = field(default_factory=lambda: [
        Unit(unit_type=UnitType.CREATION),
        Unit(unit_type=UnitType.TURNAROUND),
        Unit(unit_type=UnitType.OPERATING),
    ])
    members: list[Member] = field(default_factory=list)

    # Capital structure
    class_a_shares: float = 0.0  # founder voting shares
    class_b_shares: float = 0.0  # employee/investor shares
    founder_ownership_pct: float = 0.90  # 90% at founding
    stable_shareholder_pct: float = 0.0

    # Reserves
    keshiki_reserve: float = 0.0  # 景色積立金
    profit_sharing_pool: float = 0.0
    enterprise_value: float = 50_0000_0000  # 50億円 initial post-money
    historical_high_ev: float = 50_0000_0000

    # Foundation
    foundation_cumulative: float = 0.0
    foundation_active: bool = False  # activates Phase 3+

    # Phase tracking
    current_phase: int = 0  # 0-6
    is_public: bool = False
    listing_market: str = "tse_prime"  # tse_prime / nyse / dual
