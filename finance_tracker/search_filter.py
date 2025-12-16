"""
Advanced search and filtering module for transactions.

This module provides powerful search and filtering capabilities for transactions.
It allows users to find specific transactions using multiple criteria.

LEARNING GUIDE:
==============

This module demonstrates:

1. **Filtering Patterns**
   - Multiple filter criteria
   - Combining filters (AND logic)
   - Efficient filtering with list comprehensions

2. **Search Functionality**
   - Full-text search in descriptions
   - Case-insensitive matching
   - Flexible query building

3. **Query Building**
   - Dictionary-based queries
   - Optional parameters
   - Type conversion and validation

4. **Data Extraction**
   - Get unique values (categories, accounts)
   - Useful for populating filter dropdowns

Example:
    >>> searcher = TransactionSearchFilter(transactions)
    >>> results = searcher.search(
    ...     query="grocery",
    ...     category="Groceries",
    ...     date_from=date(2024, 1, 1),
    ...     amount_min=Decimal("10.00")
    ... )
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Callable, Dict, List, Optional

from finance_tracker.models import Transaction

logger = logging.getLogger(__name__)


class TransactionSearchFilter:
    """
    Advanced search and filter for transactions.
    
    WHAT IT DOES:
    =============
    
    This class provides flexible search and filtering capabilities:
    
    1. **Text Search**: Search in descriptions and notes
    2. **Category Filter**: Filter by category name
    3. **Account Filter**: Filter by account
    4. **Date Range**: Filter by date (from/to)
    5. **Amount Range**: Filter by amount (min/max)
    6. **Type Filter**: Filter by transaction type
    7. **Recurring Filter**: Filter by recurring status
    
    HOW IT WORKS:
    =============
    
    The search method applies filters sequentially:
    
    1. Start with all transactions
    2. Apply each filter (if provided)
    3. Each filter narrows down the results
    4. Return filtered list
    
    FILTER LOGIC:
    =============
    
    - All filters use AND logic (must match all criteria)
    - Filters are applied in order
    - Empty/None filters are skipped
    - Case-insensitive text matching
    
    PERFORMANCE:
    ============
    
    - Time complexity: O(n) where n = number of transactions
    - Each filter iterates through transactions
    - For large datasets, consider indexing or database
    
    LEARNING POINTS:
    ================
    
    1. **Filtering Patterns**: How to build flexible filters
    2. **List Comprehensions**: Efficient filtering syntax
    3. **Optional Parameters**: Making filters optional
    4. **Type Handling**: Converting and validating types
    
    Example:
        >>> searcher = TransactionSearchFilter(transactions)
        >>> # Search for grocery transactions over $50 in January
        >>> results = searcher.search(
        ...     query="grocery",
        ...     category="Groceries",
        ...     date_from=date(2024, 1, 1),
        ...     date_to=date(2024, 1, 31),
        ...     amount_min=Decimal("50.00")
        ... )
    """

    def __init__(self, transactions: List[Transaction]):
        """
        Initialize search filter with transactions to search.

        Args:
            transactions: List of transactions to search/filter
                         All search operations work on this dataset
        """
        self.transactions = transactions

    def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        account: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        amount_min: Optional[Decimal] = None,
        amount_max: Optional[Decimal] = None,
        transaction_type: Optional[str] = None,
        is_recurring: Optional[bool] = None,
    ) -> List[Transaction]:
        """
        Search and filter transactions using multiple criteria.
        
        FILTERING PROCESS:
        ==================
        
        This method applies filters sequentially, narrowing down results:
        
        1. Start with all transactions
        2. Apply text search (if provided)
        3. Apply category filter (if provided)
        4. Apply account filter (if provided)
        5. Apply date range filters (if provided)
        6. Apply amount range filters (if provided)
        7. Apply type filter (if provided)
        8. Apply recurring filter (if provided)
        9. Return filtered results
        
        FILTER LOGIC:
        =============
        
        - **AND Logic**: All provided filters must match (transaction must satisfy all)
        - **Case Insensitive**: Text searches are case-insensitive
        - **Inclusive Ranges**: Date/amount ranges are inclusive (>= and <=)
        - **Absolute Amounts**: Amount filters use absolute values (handles both + and -)
        
        PERFORMANCE NOTES:
        =================
        
        - Each filter iterates through current results
        - Filters are applied in order (most selective first = better performance)
        - For large datasets, consider indexing or database queries
        
        EXAMPLE:
        ========
        
        Find all grocery transactions over $50 in January 2024:
        
        >>> results = searcher.search(
        ...     query="grocery",           # Text search
        ...     category="Groceries",       # Category filter
        ...     date_from=date(2024, 1, 1), # Start date
        ...     date_to=date(2024, 1, 31),  # End date
        ...     amount_min=Decimal("50.00") # Minimum amount
        ... )

        Args:
            query: Text to search for in description and notes
                  Case-insensitive substring matching
            category: Category name to filter by (exact match, case-insensitive)
            account: Account name to filter by (exact match)
            date_from: Start date for date range (inclusive)
                      Only transactions on or after this date
            date_to: End date for date range (inclusive)
                    Only transactions on or before this date
            amount_min: Minimum transaction amount (uses absolute value)
                       Example: 50.00 matches both +$50 and -$50
            amount_max: Maximum transaction amount (uses absolute value)
            transaction_type: Transaction type to filter by
                             Values: "debit", "credit", "transfer" (case-insensitive)
            is_recurring: Filter by recurring status
                         True = only recurring, False = only non-recurring, None = all

        Returns:
            List of transactions matching all provided criteria
            Empty list if no transactions match
        """
        # Start with all transactions
        # Each filter will narrow down this list
        results = self.transactions

        # FILTER 1: Text Search
        # Searches in both description and notes fields
        # Case-insensitive substring matching
        if query:
            query_lower = query.lower()  # Normalize query to lowercase
            results = [
                t
                for t in results
                # Check if query appears in description (case-insensitive)
                if query_lower in t.description.lower()
                # OR in notes (if notes exist)
                or (t.notes and query_lower in t.notes.lower())
            ]

        # FILTER 2: Category Filter
        # Exact match on category name (case-insensitive)
        if category:
            results = [
                t
                for t in results
                # Transaction must have a category
                if t.category
                # And category name must match (case-insensitive)
                and t.category.name.lower() == category.lower()
            ]

        # FILTER 3: Account Filter
        # Exact match on account name
        if account:
            results = [
                t
                for t in results
                # Transaction must have an account
                if t.account
                # And account must match exactly
                and t.account == account
            ]

        # FILTER 4: Date Range (From)
        # Only transactions on or after this date
        if date_from:
            results = [t for t in results if t.date >= date_from]
        
        # FILTER 5: Date Range (To)
        # Only transactions on or before this date
        if date_to:
            results = [t for t in results if t.date <= date_to]

        # FILTER 6: Amount Range (Minimum)
        # Uses absolute value to handle both positive and negative amounts
        # Example: amount_min=50 matches both +$50 and -$50 transactions
        if amount_min is not None:
            results = [
                t
                for t in results
                # Compare absolute values
                if abs(t.amount) >= abs(amount_min)
            ]
        
        # FILTER 7: Amount Range (Maximum)
        # Uses absolute value for comparison
        if amount_max is not None:
            results = [
                t
                for t in results
                # Compare absolute values
                if abs(t.amount) <= abs(amount_max)
            ]

        # FILTER 8: Transaction Type
        # Filter by transaction type (debit, credit, transfer)
        if transaction_type:
            results = [
                t
                for t in results
                # Compare type values (case-insensitive)
                if t.transaction_type.value.lower() == transaction_type.lower()
            ]

        # FILTER 9: Recurring Status
        # Filter by whether transaction is marked as recurring
        if is_recurring is not None:
            results = [
                t
                for t in results
                # Exact match on recurring status
                if t.is_recurring == is_recurring
            ]

        # Return filtered results
        return results

    def advanced_query(self, query_dict: Dict) -> List[Transaction]:
        """
        Execute advanced query from dictionary.

        Args:
            query_dict: Dictionary with query parameters

        Returns:
            Filtered transactions
        """
        return self.search(
            query=query_dict.get("query"),
            category=query_dict.get("category"),
            account=query_dict.get("account"),
            date_from=query_dict.get("date_from"),
            date_to=query_dict.get("date_to"),
            amount_min=query_dict.get("amount_min"),
            amount_max=query_dict.get("amount_max"),
            transaction_type=query_dict.get("transaction_type"),
            is_recurring=query_dict.get("is_recurring"),
        )

    def get_categories(self) -> List[str]:
        """
        Get list of all unique categories.

        Returns:
            List of category names
        """
        categories = set()
        for transaction in self.transactions:
            if transaction.category:
                categories.add(transaction.category.name)
        return sorted(list(categories))

    def get_accounts(self) -> List[str]:
        """
        Get list of all unique accounts.

        Returns:
            List of account names
        """
        accounts = set()
        for transaction in self.transactions:
            if transaction.account:
                accounts.add(transaction.account)
        return sorted(list(accounts))

