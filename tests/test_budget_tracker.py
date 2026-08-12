"""Tests for budget tracking."""

from datetime import date
from decimal import Decimal

from finance_tracker.budget_tracker import BudgetRepository, BudgetTracker
from finance_tracker.models import Budget, Category, Transaction, TransactionType


class TestBudgetTracker:
    """Tests for BudgetRepository and BudgetTracker."""

    def test_save_and_status(self, tmp_path):
        repo = BudgetRepository(tmp_path)
        repo.save_budget(
            Budget(
                category_name="Groceries",
                year=2024,
                month=1,
                amount=Decimal("100.00"),
                alert_threshold=Decimal("0.8"),
            )
        )

        transactions = [
            Transaction(
                date=date(2024, 1, 10),
                amount=Decimal("-90.00"),
                description="GROCERY STORE",
                transaction_type=TransactionType.DEBIT,
                category=Category(name="Groceries"),
            )
        ]
        tracker = BudgetTracker(transactions, repo)
        status = tracker.get_budget_status("Groceries", 2024, 1)

        assert status["has_budget"] is True
        assert Decimal(status["spent"]) == Decimal("90.00")
        assert status["should_alert"] is True
        assert status["over_budget"] is False

    def test_over_budget_alert(self, tmp_path):
        repo = BudgetRepository(tmp_path)
        repo.save_budget(
            Budget(
                category_name="Groceries",
                year=2024,
                month=1,
                amount=Decimal("50.00"),
            )
        )
        transactions = [
            Transaction(
                date=date(2024, 1, 10),
                amount=Decimal("-75.00"),
                description="GROCERY STORE",
                transaction_type=TransactionType.DEBIT,
                category=Category(name="Groceries"),
            )
        ]
        alerts = BudgetTracker(transactions, repo).check_alerts(2024, 1)
        assert any("Over budget" in a["message"] for a in alerts)
