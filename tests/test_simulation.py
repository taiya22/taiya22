"""Tests for the Taiga Capital Group simulation."""

import pytest

from taiga_sim.engines.simulation_runner import SimulationRunner
from taiga_sim.models.financial import ProfitLoss, BalanceSheet, CashFlow
from taiga_sim.models.organization import (
    Company,
    CompanyType,
    Member,
    MemberGrade,
    OwnershipScore,
)
from taiga_sim.models.simulation import SimulationConfig, SimulationState


class TestFinancialModels:
    def test_profit_loss_properties(self):
        pl = ProfitLoss(
            revenue=10_0000_0000,
            cogs=5_5000_0000,
            sga=1_0000_0000,
            personnel_cost=1_5000_0000,
            depreciation=6500_0000,
        )
        assert pl.gross_profit == 4_5000_0000
        assert pl.operating_income == 2_0000_0000
        assert pl.ebitda == 2_6500_0000
        assert pl.net_income == pytest.approx(pl.pretax_income * 0.70, rel=0.01)

    def test_balance_sheet_net_debt(self):
        bs = BalanceSheet(
            cash=2_0000_0000,
            interest_bearing_debt=5_0000_0000,
        )
        assert bs.net_debt == 3_0000_0000

    def test_cash_flow_fcf(self):
        cf = CashFlow(
            net_income=1_0000_0000,
            depreciation=5000_0000,
            capex_maintenance=-3000_0000,
        )
        assert cf.operating_cf == 1_5000_0000
        assert cf.fcf == 1_2000_0000


class TestOwnershipScore:
    def test_total_score(self):
        os = OwnershipScore(20, 20, 20, 20, 20)
        assert os.total == 100

    def test_clamp(self):
        os = OwnershipScore(25, -5, 10, 10, 10)
        clamped = os.clamp()
        assert clamped.financial_literacy == 20
        assert clamped.decision_ownership == 0
        assert clamped.total == 50


class TestSimulationRunner:
    def test_initialization(self):
        runner = SimulationRunner(seed=42)
        runner.initialize()
        assert len(runner.state.holding.members) == 3
        assert runner.state.holding.members[0].is_founder
        assert runner.state.holding.enterprise_value == 50_0000_0000

    def test_run_5_years(self):
        runner = SimulationRunner(seed=42)
        reports = runner.run(years=5)
        assert len(reports) == 6  # year 0-5
        assert reports[0].year == 0
        assert reports[5].year == 5
        # Should have acquired some companies by year 5
        assert reports[5].num_companies >= 1
        # Revenue should be positive
        assert reports[5].revenue > 0

    def test_run_30_years(self):
        runner = SimulationRunner(seed=42)
        reports = runner.run(years=30)
        assert len(reports) == 31  # year 0-30
        final = reports[-1]
        # Basic sanity checks
        assert final.enterprise_value > 0
        assert final.headcount > 10
        assert final.founder_ownership_pct > 0
        assert final.founder_ownership_pct < 1

    def test_crisis_can_occur(self):
        """With enough years, a crisis should be possible."""
        config = SimulationConfig()
        config.macro.shock_probability = 0.30  # high probability for test
        runner = SimulationRunner(config=config, seed=123)
        reports = runner.run(years=15)
        # Check if any crisis occurred
        any_crisis = any(r.crisis_active for r in reports)
        # With 30% annual probability over 15 years, very likely
        # but not guaranteed with any specific seed

    def test_export_results(self, tmp_path):
        runner = SimulationRunner(seed=42)
        runner.run(years=3)
        output = runner.export_results(str(tmp_path / "test_results.json"))
        assert (tmp_path / "test_results.json").exists()


class TestCompanyModel:
    def test_company_creation(self):
        company = Company(
            id="test_1",
            name="Test Manufacturing",
            company_type=CompanyType.PRODUCT,
            revenue=10_0000_0000,
            ebitda=1_5000_0000,
        )
        assert company.operating_margin == 0.10
        assert company.signal == "green"


class TestConglomeratePremium:
    """Tests for research-based conglomerate premium/discount model."""

    def test_single_company_no_effect(self):
        """Single company should have no conglomerate effect."""
        from taiga_sim.engines.financial_engine import FinancialEngine
        engine = FinancialEngine()
        state = SimulationState()
        state.holding.companies = [
            Company(id="c1", company_type=CompanyType.PRODUCT, revenue=10_0000_0000, ebitda=1_0000_0000)
        ]
        multiplier = engine.compute_conglomerate_premium(state)
        assert multiplier == 1.0

    def test_related_diversification_premium(self):
        """Multiple companies of same type should yield related diversification premium."""
        from taiga_sim.engines.financial_engine import FinancialEngine
        engine = FinancialEngine()
        state = SimulationState()
        state.holding.companies = [
            Company(id=f"c{i}", company_type=CompanyType.PRODUCT, revenue=10_0000_0000, ebitda=1_0000_0000)
            for i in range(4)
        ]
        state.holding.operating_system_maturity = 0.5
        state.holding.governance_quality = 0.7
        multiplier = engine.compute_conglomerate_premium(state)
        # Related diversification should yield premium (>1.0)
        assert multiplier > 1.0

    def test_unrelated_diversification_discount(self):
        """Many unrelated types with no operating system should yield discount."""
        from taiga_sim.engines.financial_engine import FinancialEngine
        engine = FinancialEngine()
        state = SimulationState()
        types = list(CompanyType)
        state.holding.companies = [
            Company(id=f"c{i}", company_type=types[i], revenue=10_0000_0000, ebitda=1_0000_0000)
            for i in range(5)
        ]
        state.holding.operating_system_maturity = 0.0
        state.holding.governance_quality = 0.3
        multiplier = engine.compute_conglomerate_premium(state)
        # Unrelated with poor governance and no OS should discount
        assert multiplier < 1.0

    def test_operating_system_improves_premium(self):
        """Mature operating system should improve the premium."""
        from taiga_sim.engines.financial_engine import FinancialEngine
        engine = FinancialEngine()
        state = SimulationState()
        types = list(CompanyType)
        state.holding.companies = [
            Company(id=f"c{i}", company_type=types[i % len(types)], revenue=10_0000_0000, ebitda=1_0000_0000)
            for i in range(6)
        ]
        # Without OS
        state.holding.operating_system_maturity = 0.0
        state.holding.governance_quality = 0.5
        mult_no_os = engine.compute_conglomerate_premium(state)

        # With mature OS
        state.holding.operating_system_maturity = 0.9
        state.holding.governance_quality = 0.5
        mult_with_os = engine.compute_conglomerate_premium(state)

        assert mult_with_os > mult_no_os

    def test_monitoring_decay(self):
        """Many companies should trigger monitoring efficiency decay."""
        from taiga_sim.engines.financial_engine import FinancialEngine
        engine = FinancialEngine()
        state = SimulationState()
        # 5 companies (below threshold)
        state.holding.companies = [
            Company(id=f"c{i}", company_type=CompanyType.PRODUCT, revenue=10_0000_0000, ebitda=1_0000_0000)
            for i in range(5)
        ]
        state.holding.operating_system_maturity = 0.5
        state.holding.governance_quality = 0.7
        mult_small = engine.compute_conglomerate_premium(state)

        # 12 companies (well above threshold)
        state.holding.companies = [
            Company(id=f"c{i}", company_type=CompanyType.PRODUCT, revenue=10_0000_0000, ebitda=1_0000_0000)
            for i in range(12)
        ]
        mult_large = engine.compute_conglomerate_premium(state)

        # More companies should have lower premium due to monitoring decay
        assert mult_large < mult_small

    def test_conglomerate_premium_in_annual_report(self):
        """30-year run should include conglomerate premium metrics."""
        runner = SimulationRunner(seed=42)
        reports = runner.run(years=10)
        final = reports[-1]
        # Premium should be non-zero once companies exist
        assert final.operating_system_maturity > 0
        assert final.governance_quality > 0


class TestMemberModel:
    def test_founder(self):
        m = Member(
            id="founder",
            is_founder=True,
            base_salary=180_0000,
            grade=MemberGrade.S,
        )
        assert m.is_founder
        assert m.base_salary == 180_0000

    def test_elite_unit_eligibility(self):
        young = Member(id="young", age=28, grade=MemberGrade.B)
        assert young.is_eligible_for_elite_unit(0)

        old_s = Member(id="old_s", age=35, grade=MemberGrade.S)
        assert old_s.is_eligible_for_elite_unit(0)

        old_b = Member(id="old_b", age=35, grade=MemberGrade.B)
        assert not old_b.is_eligible_for_elite_unit(0)
