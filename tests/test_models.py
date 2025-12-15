"""Tests for data models."""

from datetime import date
from decimal import Decimal

import pytest

from finance_tracker.models import (
    Category,
    MonthlySummary,
    SpendingPattern,
    Transaction,
    TransactionType,
)


class TestCategory:
    """Tests for Category model."""

    def test_create_category(self):
        """Test creating a basic category."""
        category = Category(name="Groceries")
        assert category.name == "Groceries"
        assert category.parent is None
        assert category.description is None

    def test_create_category_with_parent(self):
        """Test creating a category with parent."""
        category = Category(name="Fast Food", parent="Food & Dining")
        assert category.name == "Fast Food"
        assert category.parent == "Food & Dining"

    def test_category_immutable(self):
        """Test that categories are immutable."""
        category = Category(name="Groceries")
        with pytest.raises(Exception):  # Pydantic ValidationError
            category.name = "Food"  # type: ignore


class TestTransaction:
    """Tests for Transaction model."""

    def test_create_debit_transaction(self):
        """Test creating a debit transaction."""
        transaction = Transaction(
            date=date(2024, 1, 15),
            amount=Decimal("-50.00"),
            description="Grocery Store",
            transaction_type=TransactionType.DEBIT,
        )
        assert transaction.date == date(2024, 1, 15)
        assert transaction.amount == Decimal("-50.00")
        assert transaction.description == "Grocery Store"
        assert transaction.transaction_type == TransactionType.DEBIT
        assert transaction.is_expense is True
        assert transaction.is_income is False
        assert transaction.absolute_amount == Decimal("50.00")

    def test_create_credit_transaction(self):
        """Test creating a credit transaction."""
        transaction = Transaction(
            date=date(2024, 1, 15),
            amount=Decimal("1000.00"),
            description="Salary",
            transaction_type=TransactionType.CREDIT,
        )
        assert transaction.is_expense is False
        assert transaction.is_income is True
        assert transaction.absolute_amount == Decimal("1000.00")

    def test_transaction_with_category(self):
        """Test creating a transaction with category."""
        category = Category(name="Groceries")
        transaction = Transaction(
            date=date(2024, 1, 15),
            amount=Decimal("-50.00"),
            description="Grocery Store",
            transaction_type=TransactionType.DEBIT,
            category=category,
        )
        assert transaction.category is not None
        assert transaction.category.name == "Groceries"

    def test_transaction_zero_amount_validation(self):
        """Test that zero amount transactions are rejected."""
        with pytest.raises(ValueError, match="cannot be zero"):
            Transaction(
                date=date(2024, 1, 15),
                amount=Decimal("0.00"),
                description="Invalid Transaction",
                transaction_type=TransactionType.DEBIT,
            )


class TestMonthlySummary:
    """Tests for MonthlySummary model."""

    def test_create_monthly_summary(self):
        """Test creating a monthly summary."""
        summary = MonthlySummary(year=2024, month=1)
        assert summary.year == 2024
        assert summary.month == 1
        assert summary.total_income == Decimal("0")
        assert summary.total_expenses == Decimal("0")
        assert summary.net_amount == Decimal("0")
        assert summary.transaction_count == 0
        assert summary.category_breakdown == {}

    def test_monthly_summary_with_data(self):
        """Test monthly summary with actual data."""
        summary = MonthlySummary(
            year=2024,
            month=1,
            total_income=Decimal("3000.00"),
            total_expenses=Decimal("2000.00"),
            net_amount=Decimal("1000.00"),
            transaction_count=25,
            category_breakdown={"Groceries": Decimal("500.00"), "Transportation": Decimal("300.00")},
        )
        assert summary.total_income == Decimal("3000.00")
        assert summary.total_expenses == Decimal("2000.00")
        assert summary.net_amount == Decimal("1000.00")
        assert summary.savings_rate == pytest.approx(33.33, rel=0.01)

    def test_savings_rate_zero_income(self):
        """Test savings rate calculation with zero income."""
        summary = MonthlySummary(
            year=2024, month=1, total_income=Decimal("0"), total_expenses=Decimal("100.00")
        )
        assert summary.savings_rate is None

    def test_month_validation(self):
        """Test that month must be between 1 and 12."""
        # Valid month
        MonthlySummary(year=2024, month=12)

        # Invalid months
        with pytest.raises(Exception):  # Pydantic ValidationError
            MonthlySummary(year=2024, month=0)

        with pytest.raises(Exception):  # Pydantic ValidationError
            MonthlySummary(year=2024, month=13)


class TestSpendingPattern:
    """Tests for SpendingPattern model."""

    def test_create_spending_pattern(self):
        """Test creating a spending pattern."""
        pattern = SpendingPattern(
            category="Groceries",
            total_amount=Decimal("500.00"),
            transaction_count=10,
            average_transaction=Decimal("50.00"),
            min_transaction=Decimal("20.00"),
            max_transaction=Decimal("150.00"),
            percentage_of_total=25.0,
        )
        assert pattern.category == "Groceries"
        assert pattern.total_amount == Decimal("500.00")
        assert pattern.transaction_count == 10
        assert pattern.average_transaction == Decimal("50.00")
        assert pattern.percentage_of_total == 25.0

