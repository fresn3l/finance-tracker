"""Tests for transaction categorizer module."""

from datetime import date
from decimal import Decimal

import pytest

from finance_tracker.categorizer import (
    CategorizationStats,
    TransactionCategorizer,
    categorize_transactions,
)
from finance_tracker.models import Category, Transaction, TransactionType


class TestCategorizationStats:
    """Tests for CategorizationStats class."""

    def test_empty_stats(self):
        """Test empty stats initialization."""
        stats = CategorizationStats()
        assert stats.total_transactions == 0
        assert stats.categorized_count == 0
        assert stats.uncategorized_count == 0
        assert stats.categorization_rate == 0.0

    def test_categorization_rate(self):
        """Test categorization rate calculation."""
        stats = CategorizationStats()
        stats.total_transactions = 10
        stats.categorized_count = 7
        stats.uncategorized_count = 3

        assert stats.categorization_rate == 70.0

    def test_categorization_rate_zero_total(self):
        """Test categorization rate with zero total."""
        stats = CategorizationStats()
        assert stats.categorization_rate == 0.0


class TestTransactionCategorizer:
    """Tests for TransactionCategorizer class."""

    @pytest.fixture
    def categorizer(self):
        """Create a TransactionCategorizer instance."""
        return TransactionCategorizer()

    @pytest.fixture
    def sample_transactions(self):
        """Create sample transactions."""
        return [
            Transaction(
                date=date(2024, 1, 2),
                amount=Decimal("3000.00"),
                description="Salary Deposit",
                transaction_type=TransactionType.CREDIT,
            ),
            Transaction(
                date=date(2024, 1, 3),
                amount=Decimal("-45.67"),
                description="GROCERY STORE #1234",
                transaction_type=TransactionType.DEBIT,
            ),
            Transaction(
                date=date(2024, 1, 5),
                amount=Decimal("-89.99"),
                description="AMAZON.COM PURCHASE",
                transaction_type=TransactionType.DEBIT,
            ),
            Transaction(
                date=date(2024, 1, 7),
                amount=Decimal("-35.50"),
                description="GAS STATION SHELL",
                transaction_type=TransactionType.DEBIT,
            ),
            Transaction(
                date=date(2024, 1, 10),
                amount=Decimal("-5.50"),
                description="COFFEE SHOP STARBUCKS",
                transaction_type=TransactionType.DEBIT,
            ),
            Transaction(
                date=date(2024, 1, 15),
                amount=Decimal("-45.00"),
                description="UNKNOWN MERCHANT XYZ",
                transaction_type=TransactionType.DEBIT,
            ),
        ]

    def test_categorize_single_transaction(self, categorizer):
        """Test categorizing a single transaction."""
        transaction = Transaction(
            date=date(2024, 1, 3),
            amount=Decimal("-45.67"),
            description="GROCERY STORE #1234",
            transaction_type=TransactionType.DEBIT,
        )

        categorized = categorizer.categorize_transaction(transaction)
        assert categorized.category is not None
        assert categorized.category.name == "Groceries"
        assert categorized.category.parent == "Food & Dining"

    def test_categorize_transactions(self, categorizer, sample_transactions):
        """Test categorizing multiple transactions."""
        categorized, stats = categorizer.categorize_transactions(sample_transactions)

        assert len(categorized) == len(sample_transactions)
        assert stats.total_transactions == 6
        assert stats.categorized_count > 0
        assert stats.uncategorized_count >= 0

        # Check that some transactions were categorized
        categorized_list = [t for t in categorized if t.category is not None]
        assert len(categorized_list) > 0

    def test_categorize_transactions_stats(self, categorizer, sample_transactions):
        """Test categorization statistics."""
        _, stats = categorizer.categorize_transactions(sample_transactions)

        assert stats.total_transactions == 6
        assert stats.categorized_count + stats.uncategorized_count == 6
        assert stats.categorization_rate >= 0
        assert stats.categorization_rate <= 100

    def test_categorize_already_categorized(self, categorizer):
        """Test that already categorized transactions are skipped."""
        transaction = Transaction(
            date=date(2024, 1, 3),
            amount=Decimal("-45.67"),
            description="GROCERY STORE #1234",
            transaction_type=TransactionType.DEBIT,
            category=Category(name="Custom Category"),
        )

        categorized = categorizer.categorize_transaction(transaction, overwrite=False)
        assert categorized.category is not None
        assert categorized.category.name == "Custom Category"  # Should keep original

    def test_categorize_overwrite(self, categorizer):
        """Test overwriting existing category."""
        transaction = Transaction(
            date=date(2024, 1, 3),
            amount=Decimal("-45.67"),
            description="GROCERY STORE #1234",
            transaction_type=TransactionType.DEBIT,
            category=Category(name="Custom Category"),
        )

        categorized = categorizer.categorize_transaction(transaction, overwrite=True)
        assert categorized.category is not None
        assert categorized.category.name == "Groceries"  # Should be overwritten

    def test_categorize_by_category_name(self, categorizer, sample_transactions):
        """Test manually categorizing by category name."""
        categorized = categorizer.categorize_by_category_name(
            sample_transactions, "Custom Category", "Custom Parent"
        )

        assert len(categorized) == len(sample_transactions)
        assert all(t.category is not None for t in categorized)
        assert all(t.category.name == "Custom Category" for t in categorized)
        assert all(t.category.parent == "Custom Parent" for t in categorized)

    def test_get_uncategorized_transactions(self, categorizer, sample_transactions):
        """Test getting uncategorized transactions."""
        # Categorize some transactions
        categorized, _ = categorizer.categorize_transactions(sample_transactions)

        uncategorized = categorizer.get_uncategorized_transactions(categorized)
        assert isinstance(uncategorized, list)
        assert all(t.category is None for t in uncategorized)

    def test_get_categorized_transactions(self, categorizer, sample_transactions):
        """Test getting categorized transactions."""
        # Categorize some transactions
        categorized, _ = categorizer.categorize_transactions(sample_transactions)

        categorized_list = categorizer.get_categorized_transactions(categorized)
        assert isinstance(categorized_list, list)
        assert all(t.category is not None for t in categorized_list)

    def test_get_transactions_by_category(self, categorizer, sample_transactions):
        """Test filtering transactions by category."""
        # Categorize transactions
        categorized, _ = categorizer.categorize_transactions(sample_transactions)

        # Get groceries transactions
        groceries = categorizer.get_transactions_by_category(categorized, "Groceries")
        assert isinstance(groceries, list)
        assert all(t.category.name == "Groceries" for t in groceries)

    def test_convenience_function(self, sample_transactions):
        """Test categorize_transactions convenience function."""
        categorized, stats = categorize_transactions(sample_transactions)

        assert len(categorized) == len(sample_transactions)
        assert stats.total_transactions == 6
        assert isinstance(stats, CategorizationStats)

    def test_categorize_income_transactions(self, categorizer):
        """Test categorizing income transactions."""
        transaction = Transaction(
            date=date(2024, 1, 2),
            amount=Decimal("3000.00"),
            description="Salary Deposit",
            transaction_type=TransactionType.CREDIT,
        )

        categorized = categorizer.categorize_transaction(transaction)
        assert categorized.category is not None
        assert categorized.category.name == "Salary"
        assert categorized.category.parent == "Income"

    def test_categorize_unknown_transaction(self, categorizer):
        """Test categorizing unknown transaction."""
        transaction = Transaction(
            date=date(2024, 1, 15),
            amount=Decimal("-45.00"),
            description="UNKNOWN MERCHANT XYZ123",
            transaction_type=TransactionType.DEBIT,
        )

        categorized = categorizer.categorize_transaction(transaction)
        assert categorized.category is None  # Should remain uncategorized

    def test_stats_newly_categorized(self, categorizer, sample_transactions):
        """Test stats for newly categorized transactions."""
        _, stats = categorizer.categorize_transactions(sample_transactions)

        assert stats.newly_categorized_count >= 0
        assert stats.newly_categorized_count <= stats.categorized_count

