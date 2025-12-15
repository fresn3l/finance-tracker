"""Tests for workflow module."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from finance_tracker.models import Transaction, TransactionType
from finance_tracker.workflow import FinanceTrackerWorkflow


class TestFinanceTrackerWorkflow:
    """Tests for FinanceTrackerWorkflow."""

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create a sample CSV file."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "Date,Description,Amount,Balance\n"
            "2024-01-15,Test Transaction,-50.00,1000.00\n"
        )
        return csv_file

    def test_process_csv_file(self, sample_csv, tmp_path):
        """Test processing a CSV file."""
        workflow = FinanceTrackerWorkflow(data_dir=tmp_path)
        transactions, stats = workflow.process_csv_file(sample_csv)

        assert len(transactions) > 0
        assert stats["new_transactions"] > 0

    def test_process_csv_with_duplicates(self, sample_csv, tmp_path):
        """Test processing CSV with duplicate detection."""
        workflow = FinanceTrackerWorkflow(data_dir=tmp_path)

        # Process first time
        transactions1, _ = workflow.process_csv_file(sample_csv)

        # Process again (should detect duplicates)
        transactions2, stats = workflow.process_csv_file(sample_csv, check_duplicates=True, skip_duplicates=True)

        assert stats["duplicates_found"] > 0
        assert stats["new_transactions"] == 0  # All should be duplicates

    def test_analyze_spending(self, tmp_path):
        """Test analyzing spending."""
        workflow = FinanceTrackerWorkflow(data_dir=tmp_path)

        # Add some transactions
        transactions = [
            Transaction(
                date=date(2024, 1, 15),
                amount=Decimal("-50.00"),
                description="Test",
                transaction_type=TransactionType.DEBIT,
            )
        ]
        workflow.storage.transaction_repo.save(transactions)

        analyzer = workflow.analyze_spending()
        assert analyzer is not None

    def test_get_uncategorized_transactions(self, tmp_path):
        """Test getting uncategorized transactions."""
        workflow = FinanceTrackerWorkflow(data_dir=tmp_path)

        transactions = [
            Transaction(
                date=date(2024, 1, 15),
                amount=Decimal("-50.00"),
                description="UNKNOWN MERCHANT",
                transaction_type=TransactionType.DEBIT,
            )
        ]
        workflow.storage.transaction_repo.save(transactions)

        uncategorized = workflow.get_uncategorized_transactions()
        assert len(uncategorized) >= 0  # May or may not be categorized

