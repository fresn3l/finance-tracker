"""
Core domain models for the finance tracker application.

This module defines the fundamental data structures that represent financial transactions,
categories, budgets, and analysis results. These models serve as the foundation for all
operations in the application.

LEARNING NOTES:
==============

1. Why Pydantic?
   - Pydantic provides automatic data validation
   - Type hints ensure IDE support and catch errors early
   - Serialization/deserialization to JSON is built-in
   - Field validation ensures data integrity

2. Why Decimal instead of float?
   - Floating-point numbers have precision issues (0.1 + 0.2 != 0.3)
   - Financial calculations require exact precision
   - Decimal provides fixed-point arithmetic perfect for money

3. Model Design Principles:
   - Immutable categories prevent accidental changes
   - Optional fields allow flexibility (not all transactions have categories)
   - Properties provide computed values (is_expense, savings_rate)
   - Validators ensure data consistency (amount cannot be zero)

4. Transaction ID System:
   - Transactions get unique IDs when created
   - IDs enable editing, deletion, and splitting
   - IDs are UUIDs for guaranteed uniqueness

Example Usage:
    >>> from finance_tracker.core.models import Transaction, TransactionType, Category
    >>> from datetime import date
    >>> from decimal import Decimal
    >>> 
    >>> # Create a category (immutable once created)
    >>> groceries = Category(name="Groceries", parent="Food & Dining")
    >>> 
    >>> # Create a transaction
    >>> txn = Transaction(
    ...     date=date(2024, 1, 15),
    ...     amount=Decimal("-50.00"),  # Negative = expense
    ...     description="Whole Foods Market",
    ...     transaction_type=TransactionType.DEBIT,
    ...     category=groceries
    ... )
    >>> 
    >>> # Use computed properties
    >>> print(txn.is_expense)  # True
    >>> print(txn.absolute_amount)  # Decimal('50.00')
"""

# Re-export from the main models module for backward compatibility
# This allows the code to be reorganized without breaking existing imports
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

