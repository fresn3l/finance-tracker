"""Tests for transaction editing, including merge without duplicate kwargs."""

from datetime import date
from decimal import Decimal

from finance_tracker.models import Category, Transaction, TransactionType
from finance_tracker.storage import TransactionRepository
from finance_tracker.transaction_editor import TransactionEditor


def _txn(tmp_path, txn_id, amount="-20.00", description="ITEM"):
    transaction = Transaction(
        date=date(2024, 1, 15),
        amount=Decimal(amount),
        description=description,
        transaction_type=TransactionType.DEBIT,
        category=Category(name="Shopping"),
        id=txn_id,
    )
    TransactionRepository(tmp_path).save([transaction])
    return transaction


class TestTransactionEditor:
    """Tests for TransactionEditor."""

    def test_edit_transaction(self, tmp_path):
        _txn(tmp_path, "edit-1")
        editor = TransactionEditor(TransactionRepository(tmp_path))
        updated = editor.edit_transaction(
            "edit-1",
            description="Updated item",
            notes="fixed",
        )
        assert updated is not None
        assert updated.description == "Updated item"
        assert updated.notes == "fixed"

    def test_merge_transactions_does_not_raise(self, tmp_path):
        """Merge used to rebuild Transaction(**dump, amount=...) and crash."""
        _txn(tmp_path, "merge-1", amount="-10.00", description="A")
        _txn(tmp_path, "merge-2", amount="-15.00", description="B")
        editor = TransactionEditor(TransactionRepository(tmp_path))

        merged = editor.merge_transactions(["merge-1", "merge-2"], keep_first=True)

        assert merged is not None
        assert merged.amount == Decimal("-25.00")
        assert "merged" in merged.description
