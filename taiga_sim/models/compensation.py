"""Compensation models: True Ownership Program 3-layer structure."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CompensationLayer1:
    """Layer 1: Base compensation (安定層)."""

    base_salary: float = 0.0  # 同業他社の70-80%
    bonus_pool_rate: float = 0.20  # グループ調整後営業利益 × 15-20%
    bonus_pool_total: float = 0.0  # calculated
    individual_coefficient: float = 1.0  # 0.5 - 1.5
    bonus: float = 0.0  # calculated

    @property
    def total_layer1(self) -> float:
        return self.base_salary + self.bonus


@dataclass
class CompensationLayer2:
    """Layer 2: Profit sharing (ファンドキャリー相当)."""

    ev_increase: float = 0.0  # enterprise value increase from prior high
    sharing_rate: float = 0.12  # 企業価値増加分 × 10-15%
    pool_total: float = 0.0  # calculated
    individual_share: float = 0.0  # based on tier allocation

    # Vesting: 3 years (33% / 33% / 34%)
    year1_vested: float = 0.0
    year2_vested: float = 0.0
    year3_vested: float = 0.0

    # Reinvestment option: up to 50% to Layer 3
    reinvestment_to_layer3: float = 0.0

    @property
    def current_year_cash(self) -> float:
        return self.year1_vested - self.reinvestment_to_layer3

    @property
    def tax_rate(self) -> float:
        return 0.20  # capital gains via LPS


@dataclass
class CompensationLayer3:
    """Layer 3: Self-investment / co-invest (コインベスト相当)."""

    cumulative_investment: float = 0.0  # total B-class shares purchased
    current_valuation: float = 0.0  # current market value of holdings
    annual_dividend: float = 0.0  # based on group cash yield
    max_annual_investment_pct: float = 0.50  # 年間報酬総額の50%

    @property
    def unrealized_gain(self) -> float:
        return self.current_valuation - self.cumulative_investment

    @property
    def tax_rate(self) -> float:
        return 0.20  # capital gains

    def buyback_value(self, tenure_years: int) -> float:
        """Buyback value on departure."""
        if tenure_years < 3:
            return self.current_valuation * 0.90
        return self.current_valuation


@dataclass
class TotalCompensation:
    """Total compensation for one member in one year."""

    member_id: str = ""
    year: int = 0
    layer1: CompensationLayer1 = None  # type: ignore[assignment]
    layer2: CompensationLayer2 = None  # type: ignore[assignment]
    layer3: CompensationLayer3 = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.layer1 is None:
            self.layer1 = CompensationLayer1()
        if self.layer2 is None:
            self.layer2 = CompensationLayer2()
        if self.layer3 is None:
            self.layer3 = CompensationLayer3()

    @property
    def total_cash(self) -> float:
        """Total cash compensation (pre-tax)."""
        return (
            self.layer1.total_layer1
            + self.layer2.current_year_cash
            + self.layer3.annual_dividend
        )

    @property
    def total_economic_value(self) -> float:
        """Total economic value including unrealized gains."""
        return self.total_cash + self.layer3.unrealized_gain
