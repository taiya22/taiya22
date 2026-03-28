"""Financial data models: P/L, B/S, CF statements."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProfitLoss:
    """Profit & Loss statement for a single period (quarterly)."""

    revenue: float = 0.0
    cogs: float = 0.0  # Cost of Goods Sold

    @property
    def gross_profit(self) -> float:
        return self.revenue - self.cogs

    sga: float = 0.0  # Selling, General & Administrative (excl. personnel)
    personnel_cost: float = 0.0

    @property
    def total_opex(self) -> float:
        return self.sga + self.personnel_cost

    @property
    def operating_income(self) -> float:
        return self.gross_profit - self.total_opex

    depreciation: float = 0.0

    @property
    def ebitda(self) -> float:
        return self.operating_income + self.depreciation

    interest_expense: float = 0.0

    @property
    def pretax_income(self) -> float:
        return self.operating_income - self.interest_expense

    tax_rate: float = 0.30

    @property
    def tax(self) -> float:
        return max(0.0, self.pretax_income * self.tax_rate)

    @property
    def net_income(self) -> float:
        return self.pretax_income - self.tax


@dataclass
class HoldingProfitLoss:
    """P/L for the holding company (Taiga Capital Group)."""

    dividend_income: float = 0.0  # from subsidiaries
    management_fee_income: float = 0.0

    @property
    def total_income(self) -> float:
        return self.dividend_income + self.management_fee_income

    hq_personnel_cost: float = 0.0
    hq_admin_cost: float = 0.0  # office, outsourcing, DD fees
    profit_sharing_contribution: float = 0.0
    keshiki_reserve_contribution: float = 0.0  # 景色積立金
    foundation_contribution: float = 0.0  # Taiga Foundation (FCF 5%)

    @property
    def total_cost(self) -> float:
        return (
            self.hq_personnel_cost
            + self.hq_admin_cost
            + self.profit_sharing_contribution
            + self.keshiki_reserve_contribution
            + self.foundation_contribution
        )

    @property
    def operating_income(self) -> float:
        return self.total_income - self.total_cost

    interest_expense: float = 0.0

    @property
    def pretax_income(self) -> float:
        return self.operating_income - self.interest_expense

    tax_rate: float = 0.30

    @property
    def tax(self) -> float:
        return max(0.0, self.pretax_income * self.tax_rate)

    @property
    def net_income(self) -> float:
        return self.pretax_income - self.tax


@dataclass
class BalanceSheet:
    """Balance sheet at a point in time."""

    # Assets
    cash: float = 0.0
    accounts_receivable: float = 0.0
    inventory: float = 0.0

    @property
    def current_assets(self) -> float:
        return self.cash + self.accounts_receivable + self.inventory

    ppe: float = 0.0  # Property, Plant & Equipment (net)
    goodwill: float = 0.0  # M&A-derived
    keshiki_reserve_asset: float = 0.0  # 景色積立金 (earmarked internal reserve)

    @property
    def fixed_assets(self) -> float:
        return self.ppe + self.goodwill + self.keshiki_reserve_asset

    @property
    def total_assets(self) -> float:
        return self.current_assets + self.fixed_assets

    # Liabilities
    interest_bearing_debt: float = 0.0  # bank loans, LBO-related
    accounts_payable: float = 0.0
    other_current_liabilities: float = 0.0

    @property
    def total_liabilities(self) -> float:
        return self.interest_bearing_debt + self.accounts_payable + self.other_current_liabilities

    # Equity
    class_a_shares_capital: float = 0.0  # Founder (pre-IPO)
    class_b_shares_capital: float = 0.0  # Employees/investors (pre-IPO)
    common_shares_capital: float = 0.0  # Post-IPO
    retained_earnings: float = 0.0

    @property
    def total_equity(self) -> float:
        return (
            self.class_a_shares_capital
            + self.class_b_shares_capital
            + self.common_shares_capital
            + self.retained_earnings
        )

    @property
    def total_liabilities_and_equity(self) -> float:
        return self.total_liabilities + self.total_equity

    @property
    def net_debt(self) -> float:
        return self.interest_bearing_debt - self.cash


@dataclass
class CashFlow:
    """Cash flow statement for a single period."""

    # Operating CF
    net_income: float = 0.0
    depreciation: float = 0.0
    working_capital_change: float = 0.0  # positive = cash inflow

    @property
    def operating_cf(self) -> float:
        return self.net_income + self.depreciation + self.working_capital_change

    # Investing CF
    capex_maintenance: float = 0.0  # negative value
    ma_investment: float = 0.0  # negative value

    @property
    def investing_cf(self) -> float:
        return self.capex_maintenance + self.ma_investment

    # Financing CF
    debt_proceeds: float = 0.0
    debt_repayment: float = 0.0  # negative value
    equity_issuance: float = 0.0
    dividends_paid: float = 0.0  # negative value

    @property
    def financing_cf(self) -> float:
        return self.debt_proceeds + self.debt_repayment + self.equity_issuance + self.dividends_paid

    @property
    def net_cf(self) -> float:
        return self.operating_cf + self.investing_cf + self.financing_cf

    @property
    def fcf(self) -> float:
        """Free Cash Flow = Operating CF - Maintenance Capex."""
        return self.operating_cf - abs(self.capex_maintenance)


@dataclass
class FinancialStatements:
    """Combined financial statements for a single entity and period."""

    year: int = 0
    quarter: int = 1  # 1-4
    pl: ProfitLoss = field(default_factory=ProfitLoss)
    bs: BalanceSheet = field(default_factory=BalanceSheet)
    cf: CashFlow = field(default_factory=CashFlow)

    @property
    def enterprise_value(self) -> float:
        """Simplified EV = Equity Value + Net Debt (placeholder)."""
        return self.bs.total_equity + self.bs.net_debt
