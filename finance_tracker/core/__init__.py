"""
Core domain models and data structures.

This package contains the fundamental data models that represent the core business
entities in the finance tracker application. These models use Pydantic for validation
and type safety, ensuring data integrity throughout the application.

The models defined here are:
- TransactionType: Enumeration of transaction types (debit, credit, transfer)
- Category: Spending categories with hierarchical support
- Transaction: Individual financial transactions with all metadata
- MonthlySummary: Aggregated monthly statistics
- SpendingPattern: Category-level spending analysis
- Budget: Monthly budget for a category
- BudgetTemplate: Template for quick budget setup
- RecurringTransaction: Detected recurring transaction patterns
- SplitTransaction: Split transaction information

All models use Decimal for monetary values to avoid floating-point precision errors,
which is critical for financial calculations.

Example:
    >>> from finance_tracker.core.models import Transaction, TransactionType, Category
    >>> from datetime import date
    >>> from decimal import Decimal
    >>> 
    >>> # Create a category
    >>> category = Category(name="Groceries", parent="Food & Dining")
    >>> 
    >>> # Create a transaction
    >>> transaction = Transaction(
    ...     date=date(2024, 1, 15),
    ...     amount=Decimal("-50.00"),
    ...     description="Grocery Store",
    ...     transaction_type=TransactionType.DEBIT,
    ...     category=category
    ... )
    >>> 
    >>> # Check if it's an expense
    >>> print(transaction.is_expense)  # True
"""

from finance_tracker.models import (
    Budget,
    BudgetTemplate,
    Category,
    MonthlySummary,
    RecurringTransaction,
    SpendingPattern,
    SplitTransaction,
    Transaction,
    TransactionType,
)

__all__ = [
    "TransactionType",
    "Category",
    "Transaction",
    "MonthlySummary",
    "SpendingPattern",
    "Budget",
    "BudgetTemplate",
    "RecurringTransaction",
    "SplitTransaction",
]

