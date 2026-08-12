"""Tests for recurring transaction detection."""

from datetime import date
from decimal import Decimal

from finance_tracker.models import Transaction, TransactionType
from finance_tracker.recurring_detector import RecurringTransactionDetector


def _monthly_subscription(months=4):
    """Build a monthly Netflix-style series."""
    return [
        Transaction(
            date=date(2024, month, 5),
            amount=Decimal("-15.99"),
            description="NETFLIX.COM",
            transaction_type=TransactionType.DEBIT,
            id=f"netflix-{month}",
        )
        for month in range(1, months + 1)
    ]


class TestRecurringTransactionDetector:
    """Tests for RecurringTransactionDetector."""

    def test_detect_monthly_pattern(self):
        """Monthly repeats should be detected as recurring."""
        detector = RecurringTransactionDetector(_monthly_subscription())
        found = detector.detect_recurring(min_occurrences=3)

        assert len(found) == 1
        assert found[0].frequency == "monthly"
        assert found[0].transaction_count == 4
        assert found[0].confidence > 0

    def test_mark_recurring_sets_flags_without_duplicate_kwargs(self):
        """mark_recurring must not raise TypeError from duplicate kwargs."""
        transactions = _monthly_subscription()
        one_off = Transaction(
            date=date(2024, 1, 10),
            amount=Decimal("-12.00"),
            description="COFFEE SHOP",
            transaction_type=TransactionType.DEBIT,
            id="coffee-1",
        )
        all_txns = transactions + [one_off]
        detector = RecurringTransactionDetector(all_txns)
        found = detector.detect_recurring(min_occurrences=3)

        updated = detector.mark_recurring(found)

        marked = [t for t in updated if t.is_recurring]
        unmarked = [t for t in updated if not t.is_recurring]
        assert len(marked) == 4
        assert all(t.recurring_id is not None for t in marked)
        assert len(unmarked) == 1
        assert unmarked[0].description == "COFFEE SHOP"

    def test_mark_recurring_preserves_existing_fields(self):
        """Updated transactions keep original identity and amount."""
        transactions = _monthly_subscription()
        detector = RecurringTransactionDetector(transactions)
        found = detector.detect_recurring(min_occurrences=3)
        updated = detector.mark_recurring(found)

        assert updated[0].id == "netflix-1"
        assert updated[0].amount == Decimal("-15.99")
        assert updated[0].is_recurring is True
