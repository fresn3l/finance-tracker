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
