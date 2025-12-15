"""Tests for storage module."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from finance_tracker.models import Category, Transaction, TransactionType
from finance_tracker.storage import (
    CategoryRepository,
    StorageManager,
    TransactionRepository,
)


class TestTransactionRepository:
    """Tests for TransactionRepository."""

    def test_save_and_load(self, tmp_path):
        """Test saving and loading transactions."""
        repo = TransactionRepository(tmp_path)

        transactions = [
            Transaction(
                date=date(2024, 1, 15),
                amount=Decimal("-50.00"),
                description="Test Transaction",
                transaction_type=TransactionType.DEBIT,
                category=Category(name="Groceries", parent="Food & Dining"),
            )
        ]

        repo.save(transactions)
        loaded = repo.load_all()

        assert len(loaded) == 1
        assert loaded[0].description == "Test Transaction"
        assert loaded[0].category is not None
        assert loaded[0].category.name == "Groceries"

    def test_find_duplicates(self, tmp_path):
        """Test finding duplicate transactions."""
        repo = TransactionRepository(tmp_path)

        transaction = Transaction(
            date=date(2024, 1, 15),
            amount=Decimal("-50.00"),
            description="Test Transaction",
            transaction_type=TransactionType.DEBIT,
        )

        transactions = [transaction, transaction]  # Duplicate
        duplicates = repo.find_duplicates(transactions)

        assert len(duplicates) == 1

    def test_check_duplicates_against_stored(self, tmp_path):
        """Test checking duplicates against stored transactions."""
        repo = TransactionRepository(tmp_path)

        transaction = Transaction(
            date=date(2024, 1, 15),
            amount=Decimal("-50.00"),
            description="Test Transaction",
            transaction_type=TransactionType.DEBIT,
        )

        # Save transaction
        repo.save([transaction])

        # Check for duplicates
        duplicates = repo.check_duplicates([transaction])
        assert len(duplicates) == 1

    def test_save_avoids_duplicates(self, tmp_path):
        """Test that save avoids adding duplicates."""
        repo = TransactionRepository(tmp_path)

        transaction = Transaction(
            date=date(2024, 1, 15),
            amount=Decimal("-50.00"),
            description="Test Transaction",
            transaction_type=TransactionType.DEBIT,
        )

        # Save twice
        repo.save([transaction])
        repo.save([transaction])

        loaded = repo.load_all()
        assert len(loaded) == 1  # Should only have one


class TestCategoryRepository:
    """Tests for CategoryRepository."""

    def test_save_and_load_categories(self, tmp_path):
        """Test saving and loading categories."""
        repo = CategoryRepository(tmp_path)

        categories = [
            Category(name="Custom Category", parent="Custom Parent", description="Test")
        ]

        repo.save_custom_categories(categories)
        loaded = repo.load_custom_categories()

        assert len(loaded) == 1
        assert loaded[0].name == "Custom Category"
        assert loaded[0].parent == "Custom Parent"


class TestStorageManager:
    """Tests for StorageManager."""

    def test_export_json(self, tmp_path):
        """Test exporting transactions to JSON."""
        manager = StorageManager(tmp_path)

        transactions = [
            Transaction(
                date=date(2024, 1, 15),
                amount=Decimal("-50.00"),
                description="Test Transaction",
                transaction_type=TransactionType.DEBIT,
            )
        ]

        manager.transaction_repo.save(transactions)
        output_file = tmp_path / "export.json"
        manager.export_transactions_json(output_file)

        assert output_file.exists()

    def test_export_csv(self, tmp_path):
        """Test exporting transactions to CSV."""
        manager = StorageManager(tmp_path)

        transactions = [
            Transaction(
                date=date(2024, 1, 15),
                amount=Decimal("-50.00"),
                description="Test Transaction",
                transaction_type=TransactionType.DEBIT,
            )
        ]

        manager.transaction_repo.save(transactions)
        output_file = tmp_path / "export.csv"
        manager.export_transactions_csv(output_file)

        assert output_file.exists()

