"""Tests for web app helpers that the UI depends on."""

from datetime import date
from decimal import Decimal

from finance_tracker import web_app
from finance_tracker.models import Category, Transaction, TransactionType
from finance_tracker.storage import TransactionRepository


class TestGetTransactions:
    """get_transactions must return IDs so the UI can edit/delete rows."""

    def test_get_transactions_includes_id_and_recurring_flag(self, tmp_path):
        web_app.workflow = None
        web_app.init_workflow(tmp_path)

        TransactionRepository(tmp_path).save(
            [
                Transaction(
                    date=date(2024, 1, 15),
                    amount=Decimal("-50.00"),
                    description="GROCERY STORE",
                    transaction_type=TransactionType.DEBIT,
                    category=Category(name="Groceries"),
                    notes="weekly shop",
                    id="txn-ui-1",
                    is_recurring=True,
                )
            ]
        )

        result = web_app.get_transactions(page=1, per_page=50)

        assert len(result) == 1
        txn = result[0]
        assert txn["id"] == "txn-ui-1"
        assert txn["description"] == "GROCERY STORE"
        assert txn["is_recurring"] is True
        assert txn["notes"] == "weekly shop"
        assert txn["category"]["name"] == "Groceries"


class TestMonthOverMonthEndpoint:
    def test_get_month_over_month_and_cash_flow(self, tmp_path):
        web_app.workflow = None
        web_app.init_workflow(tmp_path)
        TransactionRepository(tmp_path).save(
            [
                Transaction(
                    date=date(2024, 1, 5),
                    amount=Decimal("-40.00"),
                    description="GROCERY",
                    transaction_type=TransactionType.DEBIT,
                    category=Category(name="Groceries"),
                    id="jan",
                ),
                Transaction(
                    date=date(2024, 2, 5),
                    amount=Decimal("-50.00"),
                    description="GROCERY",
                    transaction_type=TransactionType.DEBIT,
                    category=Category(name="Groceries"),
                    id="feb",
                ),
            ]
        )

        mom = web_app.get_month_over_month(2024, 2)
        assert mom["year"] == 2024
        assert mom["month"] == 2
        assert mom["previous_month"] == 1
        assert mom["expenses"]["current"] == "50.00"
        assert mom["expenses"]["previous"] == "40.00"
        assert any(c["category"] == "Groceries" for c in mom["category_deltas"])

        cash = web_app.get_cash_flow(2024, 2)
        assert cash["expenses"] == "50.00"
        assert cash["net_operating"] == "-50.00"

        forecasts = web_app.get_forecasts()
        assert forecasts
        assert forecasts[0]["category"] is None

        report = web_app.generate_report(2024, 2, notify=False)
        assert report["success"] is True
        assert "html" in report["files"]

