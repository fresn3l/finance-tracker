"""Data storage layer for transactions and categories."""

import json
import logging
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Set

from finance_tracker.models import Category, Transaction

logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling Decimal and date objects."""

    def default(self, obj):
        """Convert Decimal and date to JSON-serializable types."""
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


class TransactionRepository:
    """Repository for managing transaction storage."""

    def __init__(self, data_dir: Path):
        """
        Initialize transaction repository.

        Args:
            data_dir: Directory where transaction data is stored
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.transactions_file = self.data_dir / "transactions.json"

    def save(self, transactions: List[Transaction]) -> None:
        """
        Save transactions to storage.

        Args:
            transactions: List of transactions to save
        """
        try:
            # Load existing transactions
            existing = self.load_all()
            existing_ids = {self._transaction_id(t) for t in existing}

            # Add new transactions (avoid duplicates)
            new_transactions = []
            for transaction in transactions:
                txn_id = self.transaction_id(transaction)
                if txn_id not in existing_ids:
                    new_transactions.append(transaction)
                    existing_ids.add(txn_id)

            all_transactions = existing + new_transactions

            # Serialize to JSON
            data = {
                "transactions": [
                    self._serialize_transaction(t) for t in all_transactions
                ]
            }

            # Write to file
            with open(self.transactions_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, cls=JSONEncoder)

            logger.info(f"Saved {len(new_transactions)} new transactions (total: {len(all_transactions)})")

        except Exception as e:
            logger.error(f"Error saving transactions: {e}")
            raise

    def load_all(self) -> List[Transaction]:
        """
        Load all transactions from storage.

        Returns:
            List of Transaction objects
        """
        if not self.transactions_file.exists():
            return []

        try:
            with open(self.transactions_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            transactions = []
            for txn_data in data.get("transactions", []):
                try:
                    transaction = self._deserialize_transaction(txn_data)
                    transactions.append(transaction)
                except Exception as e:
                    logger.warning(f"Error deserializing transaction: {e}")
                    continue

            logger.info(f"Loaded {len(transactions)} transactions")
            return transactions

        except Exception as e:
            logger.error(f"Error loading transactions: {e}")
            raise

    def find_duplicates(self, transactions: List[Transaction]) -> List[Transaction]:
        """
        Find duplicate transactions in the provided list.

        Args:
            transactions: List of transactions to check

        Returns:
            List of duplicate transactions
        """
        seen: Set[str] = set()
        duplicates = []

        for transaction in transactions:
            txn_id = self.transaction_id(transaction)
            if txn_id in seen:
                duplicates.append(transaction)
            else:
                seen.add(txn_id)

        return duplicates

    def check_duplicates(self, transactions: List[Transaction]) -> List[Transaction]:
        """
        Check for duplicates against stored transactions.

        Args:
            transactions: List of transactions to check

        Returns:
            List of transactions that are duplicates of stored transactions
        """
        stored = self.load_all()
        stored_ids = {self.transaction_id(t) for t in stored}

        duplicates = [
            t for t in transactions if self.transaction_id(t) in stored_ids
        ]

        return duplicates

    def transaction_id(self, transaction: Transaction) -> str:
        """
        Generate a unique identifier for a transaction.

        Args:
            transaction: Transaction to identify

        Returns:
            Unique identifier string
        """
        # Use date, amount, description, and reference to create unique ID
        parts = [
            transaction.date.isoformat(),
            str(transaction.amount),
            transaction.description.strip().lower(),
        ]
        if transaction.reference:
            parts.append(transaction.reference)
        return "|".join(parts)

    def _transaction_id(self, transaction: Transaction) -> str:
        """Private alias for backward compatibility."""
        return self.transaction_id(transaction)

    def _serialize_transaction(self, transaction: Transaction) -> Dict:
        """Serialize a transaction to dictionary."""
        data = {
            "date": transaction.date.isoformat(),
            "amount": str(transaction.amount),
            "description": transaction.description,
            "transaction_type": transaction.transaction_type.value,
        }

        if transaction.category:
            data["category"] = {
                "name": transaction.category.name,
                "parent": transaction.category.parent,
                "description": transaction.category.description,
            }

        if transaction.account:
            data["account"] = transaction.account

        if transaction.reference:
            data["reference"] = transaction.reference

        if transaction.balance is not None:
            data["balance"] = str(transaction.balance)

        if transaction.notes:
            data["notes"] = transaction.notes

        return data

    def _deserialize_transaction(self, data: Dict) -> Transaction:
        """Deserialize a transaction from dictionary."""
        from finance_tracker.models import TransactionType

        category = None
        if "category" in data:
            cat_data = data["category"]
            category = Category(
                name=cat_data["name"],
                parent=cat_data.get("parent"),
                description=cat_data.get("description"),
            )

        return Transaction(
            date=date.fromisoformat(data["date"]),
            amount=Decimal(data["amount"]),
            description=data["description"],
            transaction_type=TransactionType(data["transaction_type"]),
            category=category,
            account=data.get("account"),
            reference=data.get("reference"),
            balance=Decimal(data["balance"]) if data.get("balance") else None,
            notes=data.get("notes"),
        )


class CategoryRepository:
    """Repository for managing category storage."""

    def __init__(self, data_dir: Path):
        """
        Initialize category repository.

        Args:
            data_dir: Directory where category data is stored
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.categories_file = self.data_dir / "categories.json"

    def save_custom_categories(self, categories: List[Category]) -> None:
        """
        Save custom categories to storage.

        Args:
            categories: List of custom categories to save
        """
        try:
            # Load existing categories
            existing = self.load_custom_categories()
            existing_names = {c.name for c in existing}

            # Add new categories
            new_categories = [
                c for c in categories if c.name not in existing_names
            ]

            all_categories = existing + new_categories

            # Serialize to JSON
            data = {
                "categories": [
                    {
                        "name": c.name,
                        "parent": c.parent,
                        "description": c.description,
                    }
                    for c in all_categories
                ]
            }

            # Write to file
            with open(self.categories_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(new_categories)} new categories (total: {len(all_categories)})")

        except Exception as e:
            logger.error(f"Error saving categories: {e}")
            raise

    def load_custom_categories(self) -> List[Category]:
        """
        Load custom categories from storage.

        Returns:
            List of Category objects
        """
        if not self.categories_file.exists():
            return []

        try:
            with open(self.categories_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            categories = []
            for cat_data in data.get("categories", []):
                category = Category(
                    name=cat_data["name"],
                    parent=cat_data.get("parent"),
                    description=cat_data.get("description"),
                )
                categories.append(category)

            logger.info(f"Loaded {len(categories)} custom categories")
            return categories

        except Exception as e:
            logger.error(f"Error loading categories: {e}")
            raise


class StorageManager:
    """Manager for all storage operations."""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize storage manager.

        Args:
            data_dir: Optional data directory. Defaults to ~/.finance-tracker
        """
        if data_dir is None:
            data_dir = Path.home() / ".finance-tracker"

        self.data_dir = Path(data_dir)
        self.transaction_repo = TransactionRepository(self.data_dir)
        self.category_repo = CategoryRepository(self.data_dir)

    def export_transactions_json(self, output_file: Path) -> None:
        """
        Export transactions to JSON file.

        Args:
            output_file: Path to output JSON file
        """
        transactions = self.transaction_repo.load_all()
        data = {
            "transactions": [
                self.transaction_repo._serialize_transaction(t) for t in transactions
            ]
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, cls=JSONEncoder)

        logger.info(f"Exported {len(transactions)} transactions to {output_file}")

    def export_transactions_csv(self, output_file: Path) -> None:
        """
        Export transactions to CSV file.

        Args:
            output_file: Path to output CSV file
        """
        import csv

        transactions = self.transaction_repo.load_all()

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "Date",
                    "Description",
                    "Amount",
                    "Category",
                    "Parent Category",
                    "Type",
                    "Account",
                    "Reference",
                    "Balance",
                    "Notes",
                ],
            )
            writer.writeheader()

            for transaction in transactions:
                row = {
                    "Date": transaction.date.isoformat(),
                    "Description": transaction.description,
                    "Amount": str(transaction.amount),
                    "Category": transaction.category.name if transaction.category else "",
                    "Parent Category": transaction.category.parent if transaction.category else "",
                    "Type": transaction.transaction_type.value,
                    "Account": transaction.account or "",
                    "Reference": transaction.reference or "",
                    "Balance": str(transaction.balance) if transaction.balance else "",
                    "Notes": transaction.notes or "",
                }
                writer.writerow(row)

        logger.info(f"Exported {len(transactions)} transactions to {output_file}")

