"""Tests for spending analyzer module."""

from datetime import date
from decimal import Decimal

import pytest

from finance_tracker.analyzer import (
    SpendingAnalyzer,
    analyze_spending,
    previous_calendar_month,
)
from finance_tracker.models import Category, Transaction, TransactionType


class TestSpendingAnalyzer:
    """Tests for SpendingAnalyzer class."""

    @pytest.fixture
    def sample_transactions(self):
        """Create sample transactions for testing."""
        return [
            # January 2024 - Income
            Transaction(
                date=date(2024, 1, 2),
                amount=Decimal("3000.00"),
                description="Salary Deposit",
                transaction_type=TransactionType.CREDIT,
                category=Category(name="Salary", parent="Income"),
            ),
            # January 2024 - Expenses
            Transaction(
                date=date(2024, 1, 3),
                amount=Decimal("-45.67"),
                description="GROCERY STORE",
                transaction_type=TransactionType.DEBIT,
                category=Category(name="Groceries", parent="Food & Dining"),
            ),
            Transaction(
                date=date(2024, 1, 5),
                amount=Decimal("-89.99"),
                description="AMAZON",
                transaction_type=TransactionType.DEBIT,
                category=Category(name="General Shopping", parent="Shopping"),
            ),
            Transaction(
                date=date(2024, 1, 7),
                amount=Decimal("-35.50"),
                description="GAS STATION",
                transaction_type=TransactionType.DEBIT,
                category=Category(name="Gas & Fuel", parent="Transportation"),
            ),
            Transaction(
                date=date(2024, 1, 10),
                amount=Decimal("-5.50"),
                description="COFFEE SHOP",
                transaction_type=TransactionType.DEBIT,
                category=Category(name="Coffee Shops", parent="Food & Dining"),
            ),
            Transaction(
                date=date(2024, 1, 15),
                amount=Decimal("-45.00"),
                description="RESTAURANT",
                transaction_type=TransactionType.DEBIT,
                category=Category(name="Restaurants", parent="Food & Dining"),
            ),
            # February 2024 - Income
            Transaction(
                date=date(2024, 2, 1),
                amount=Decimal("3000.00"),
                description="Salary Deposit",
                transaction_type=TransactionType.CREDIT,
                category=Category(name="Salary", parent="Income"),
            ),
            # February 2024 - Expenses
            Transaction(
                date=date(2024, 2, 2),
                amount=Decimal("-52.30"),
                description="GROCERY STORE",
                transaction_type=TransactionType.DEBIT,
                category=Category(name="Groceries", parent="Food & Dining"),
            ),
            Transaction(
                date=date(2024, 2, 5),
                amount=Decimal("-125.00"),
                description="AMAZON",
                transaction_type=TransactionType.DEBIT,
                category=Category(name="General Shopping", parent="Shopping"),
            ),
        ]

    def test_get_monthly_summary(self, sample_transactions):
        """Test generating monthly summary."""
        analyzer = SpendingAnalyzer(sample_transactions)
        summary = analyzer.get_monthly_summary(2024, 1)

        assert summary.year == 2024
        assert summary.month == 1
        assert summary.total_income == Decimal("3000.00")
        assert summary.total_expenses > Decimal("0")
        assert summary.net_amount == summary.total_income - summary.total_expenses
        assert summary.transaction_count == 6

    def test_monthly_summary_category_breakdown(self, sample_transactions):
        """Test category breakdown in monthly summary."""
        analyzer = SpendingAnalyzer(sample_transactions)
        summary = analyzer.get_monthly_summary(2024, 1)

        assert "Groceries" in summary.category_breakdown
        assert summary.category_breakdown["Groceries"] == Decimal("45.67")
        assert "General Shopping" in summary.category_breakdown

    def test_get_all_monthly_summaries(self, sample_transactions):
        """Test getting all monthly summaries."""
        analyzer = SpendingAnalyzer(sample_transactions)
        summaries = analyzer.get_all_monthly_summaries()

        assert len(summaries) == 2  # January and February
        assert summaries[0].month == 1
        assert summaries[1].month == 2

    def test_get_category_breakdown(self, sample_transactions):
        """Test getting category breakdown."""
        analyzer = SpendingAnalyzer(sample_transactions)
        breakdown = analyzer.get_category_breakdown()

        assert "Groceries" in breakdown
        assert breakdown["Groceries"] > Decimal("0")
        assert "General Shopping" in breakdown

    def test_get_category_breakdown_filtered(self, sample_transactions):
        """Test getting category breakdown for specific month."""
        analyzer = SpendingAnalyzer(sample_transactions)
        breakdown = analyzer.get_category_breakdown(2024, 1)

        assert "Groceries" in breakdown
        assert breakdown["Groceries"] == Decimal("45.67")

    def test_get_spending_patterns(self, sample_transactions):
        """Test getting spending patterns."""
        analyzer = SpendingAnalyzer(sample_transactions)
        patterns = analyzer.get_spending_patterns()

        assert len(patterns) > 0
        groceries_pattern = next((p for p in patterns if p.category == "Groceries"), None)
        assert groceries_pattern is not None
        assert groceries_pattern.total_amount > Decimal("0")
        assert groceries_pattern.transaction_count > 0
        assert groceries_pattern.average_transaction > Decimal("0")

    def test_get_spending_patterns_specific_category(self, sample_transactions):
        """Test getting spending patterns for specific category."""
        analyzer = SpendingAnalyzer(sample_transactions)
        patterns = analyzer.get_spending_patterns("Groceries")

        assert len(patterns) == 1
        assert patterns[0].category == "Groceries"

    def test_get_top_categories(self, sample_transactions):
        """Test getting top spending categories."""
        analyzer = SpendingAnalyzer(sample_transactions)
        top = analyzer.get_top_categories(limit=5)

        assert len(top) <= 5
        # Should be sorted by total amount descending
        if len(top) > 1:
            assert top[0].total_amount >= top[1].total_amount

    def test_get_total_income(self, sample_transactions):
        """Test calculating total income."""
        analyzer = SpendingAnalyzer(sample_transactions)
        total = analyzer.get_total_income()

        assert total == Decimal("6000.00")  # 2 months * 3000

    def test_get_total_income_filtered(self, sample_transactions):
        """Test calculating total income for specific month."""
        analyzer = SpendingAnalyzer(sample_transactions)
        total = analyzer.get_total_income(2024, 1)

        assert total == Decimal("3000.00")

    def test_get_total_expenses(self, sample_transactions):
        """Test calculating total expenses."""
        analyzer = SpendingAnalyzer(sample_transactions)
        total = analyzer.get_total_expenses()

        assert total > Decimal("0")

    def test_get_net_amount(self, sample_transactions):
        """Test calculating net amount."""
        analyzer = SpendingAnalyzer(sample_transactions)
        net = analyzer.get_net_amount()

        income = analyzer.get_total_income()
        expenses = analyzer.get_total_expenses()
        assert net == income - expenses

    def test_get_average_monthly_spending(self, sample_transactions):
        """Test calculating average monthly spending."""
        analyzer = SpendingAnalyzer(sample_transactions)
        avg = analyzer.get_average_monthly_spending()

        assert avg > Decimal("0")

    def test_get_average_monthly_spending_category(self, sample_transactions):
        """Test calculating average monthly spending for category."""
        analyzer = SpendingAnalyzer(sample_transactions)
        avg = analyzer.get_average_monthly_spending("Groceries")

        assert avg > Decimal("0")

    def test_get_spending_trend(self, sample_transactions):
        """Test getting spending trend."""
        analyzer = SpendingAnalyzer(sample_transactions)
        trend = analyzer.get_spending_trend("Groceries")

        # Should return a trend or None if insufficient data
        assert trend in ["increasing", "decreasing", "stable", None]

    def test_savings_rate(self, sample_transactions):
        """Test savings rate calculation in monthly summary."""
        analyzer = SpendingAnalyzer(sample_transactions)
        summary = analyzer.get_monthly_summary(2024, 1)

        assert summary.savings_rate is not None
        assert summary.savings_rate > 0  # Should have positive savings

    def test_convenience_function(self, sample_transactions):
        """Test analyze_spending convenience function."""
        analyzer = analyze_spending(sample_transactions)
        assert isinstance(analyzer, SpendingAnalyzer)

    def test_empty_transactions(self):
        """Test analyzer with empty transaction list."""
        analyzer = SpendingAnalyzer([])
        summaries = analyzer.get_all_monthly_summaries()
        assert summaries == []

        breakdown = analyzer.get_category_breakdown()
        assert breakdown == {}

        patterns = analyzer.get_spending_patterns()
        assert patterns == []

    def test_spending_pattern_percentage(self, sample_transactions):
        """Test that spending patterns include percentage of total."""
        analyzer = SpendingAnalyzer(sample_transactions)
        patterns = analyzer.get_spending_patterns()

        for pattern in patterns:
            if pattern.percentage_of_total is not None:
                assert 0 <= pattern.percentage_of_total <= 100

    def test_previous_calendar_month(self):
        assert previous_calendar_month(2024, 2) == (2024, 1)
        assert previous_calendar_month(2024, 1) == (2023, 12)

    def test_month_over_month_totals_and_categories(self, sample_transactions):
        analyzer = SpendingAnalyzer(sample_transactions)
        mom = analyzer.get_month_over_month(2024, 2)

        assert mom.year == 2024
        assert mom.month == 2
        assert mom.previous_year == 2024
        assert mom.previous_month == 1
        assert mom.income.current == Decimal("3000.00")
        assert mom.income.previous == Decimal("3000.00")
        assert mom.income.delta == Decimal("0")
        assert mom.income.percent_change == 0.0
        assert mom.expenses.current == Decimal("177.30")
        assert mom.expenses.previous == Decimal("221.66")
        assert mom.expenses.delta == Decimal("-44.36")
        assert mom.expenses.percent_change is not None
        assert mom.expenses.percent_change < 0

        groceries = next(d for d in mom.category_deltas if d.category == "Groceries")
        assert groceries.current == Decimal("52.30")
        assert groceries.previous == Decimal("45.67")
        assert groceries.delta == Decimal("6.63")

        coffee = next(d for d in mom.category_deltas if d.category == "Coffee Shops")
        assert coffee.current == Decimal("0")
        assert coffee.previous == Decimal("5.50")

    def test_latest_month_over_month(self, sample_transactions):
        analyzer = SpendingAnalyzer(sample_transactions)
        mom = analyzer.get_latest_month_over_month()
        assert mom is not None
        assert (mom.year, mom.month) == (2024, 2)

    def test_latest_month_over_month_empty(self):
        assert SpendingAnalyzer([]).get_latest_month_over_month() is None

    def test_percent_change_when_previous_is_zero(self):
        analyzer = SpendingAnalyzer(
            [
                Transaction(
                    date=date(2024, 2, 1),
                    amount=Decimal("-10.00"),
                    description="NEW MERCHANT",
                    transaction_type=TransactionType.DEBIT,
                    category=Category(name="New Category"),
                )
            ]
        )
        mom = analyzer.get_month_over_month(2024, 2)
        item = next(d for d in mom.category_deltas if d.category == "New Category")
        assert item.previous == Decimal("0")
        assert item.percent_change is None

    def test_cash_flow_excludes_transfers_from_operating(self, sample_transactions):
        txns = list(sample_transactions) + [
            Transaction(
                date=date(2024, 1, 20),
                amount=Decimal("-500.00"),
                description="TRANSFER TO SAVINGS",
                transaction_type=TransactionType.TRANSFER,
            ),
            Transaction(
                date=date(2024, 1, 21),
                amount=Decimal("200.00"),
                description="TRANSFER FROM CHECKING",
                transaction_type=TransactionType.TRANSFER,
            ),
        ]
        cash = SpendingAnalyzer(txns).get_cash_flow(2024, 1)
        assert cash.income == Decimal("3000.00")
        assert cash.expenses == Decimal("221.66")
        assert cash.transfers_out == Decimal("500.00")
        assert cash.transfers_in == Decimal("200.00")
        assert cash.net_operating == Decimal("2778.34")
        assert cash.net_cash == Decimal("2478.34")

    def test_forecast_moving_average(self, sample_transactions):
        analyzer = SpendingAnalyzer(sample_transactions)
        overall = analyzer.forecast_next_month(months=3)
        assert overall is not None
        assert overall.category is None
        assert overall.months_used == 2
        jan = analyzer.get_monthly_summary(2024, 1).total_expenses
        feb = analyzer.get_monthly_summary(2024, 2).total_expenses
        assert overall.predicted_amount == (jan + feb) / 2

        groceries = analyzer.forecast_next_month(months=3, category_name="Groceries")
        assert groceries is not None
        assert groceries.predicted_amount == (Decimal("45.67") + Decimal("52.30")) / 2

        all_forecasts = analyzer.forecast_all_categories()
        assert all_forecasts[0].category is None
        names = {f.category for f in all_forecasts}
        assert "Groceries" in names

