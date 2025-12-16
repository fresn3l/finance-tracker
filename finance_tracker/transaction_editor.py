"""
Transaction editing and management module.

This module provides functionality to edit, delete, split, and merge transactions.
It acts as a service layer that coordinates transaction modifications with the storage layer.

LEARNING GUIDE:
==============

This module demonstrates several important concepts:

1. **Service Layer Pattern**
   - Separates business logic from storage logic
   - Provides high-level operations (edit, split, merge)
   - Coordinates with repository for persistence

2. **Transaction Management**
   - Edit: Update transaction fields
   - Delete: Remove transactions
   - Split: Divide one transaction into multiple
   - Merge: Combine multiple transactions into one
   - Bulk: Apply changes to multiple transactions

3. **Data Validation**
   - Validates business rules (e.g., split amounts must sum correctly)
   - Ensures data integrity before saving
   - Provides helpful error messages

4. **Idempotency**
   - Operations can be safely retried
   - Checks for existence before operations
   - Returns success/failure status

Example:
    >>> from finance_tracker.storage import TransactionRepository
    >>> from finance_tracker.transaction_editor import TransactionEditor
    >>> 
    >>> repo = TransactionRepository(data_dir)
    >>> editor = TransactionEditor(repo)
    >>> 
    >>> # Edit a transaction
    >>> updated = editor.edit_transaction(
    ...     transaction_id="123",
    ...     description="Updated Description",
    ...     category=Category(name="Groceries")
    ... )
"""

import logging
import uuid
from decimal import Decimal
from typing import Dict, List, Optional

from finance_tracker.models import Category, SplitTransaction, Transaction

logger = logging.getLogger(__name__)


class TransactionEditor:
    """
    Service for editing and managing transactions.
    
    WHAT IT DOES:
    =============
    
    This class provides high-level operations for transaction management:
    
    1. **Edit**: Update transaction fields (description, amount, date, category, notes)
    2. **Delete**: Remove single or multiple transactions
    3. **Split**: Divide one transaction into multiple transactions (different categories)
    4. **Merge**: Combine multiple transactions into one
    5. **Bulk Edit**: Apply changes to multiple transactions at once
    
    DESIGN PATTERNS:
    ================
    
    - **Service Layer**: Business logic separate from storage
    - **Repository Pattern**: Uses repository for persistence
    - **Validation**: Validates business rules before operations
    
    LEARNING POINTS:
    ================
    
    1. **Separation of Concerns**: Editor handles business logic, repo handles storage
    2. **Validation**: Check business rules before persisting
    3. **Error Handling**: Provide helpful error messages
    4. **Atomic Operations**: Each method does one thing completely
    
    Example:
        >>> editor = TransactionEditor(repo)
        >>> # Edit transaction
        >>> editor.edit_transaction("txn-123", description="New Description")
        >>> # Split transaction
        >>> splits = [
        ...     SplitTransaction(amount=Decimal("30"), category=Category(name="Groceries")),
        ...     SplitTransaction(amount=Decimal("20"), category=Category(name="Gas"))
        ... ]
        >>> editor.split_transaction("txn-123", splits)
    """

    def __init__(self, transaction_repo):
        """
        Initialize transaction editor with a repository.

        Args:
            transaction_repo: TransactionRepository instance
                             This handles all persistence operations
                             The editor focuses on business logic
        """
        self.repo = transaction_repo

    def edit_transaction(
        self,
        transaction_id: str,
        description: Optional[str] = None,
        amount: Optional[Decimal] = None,
        date: Optional = None,
        category: Optional[Category] = None,
        notes: Optional[str] = None,
    ) -> Optional[Transaction]:
        """
        Edit a transaction.

        Args:
            transaction_id: Transaction ID
            description: New description (optional)
            amount: New amount (optional)
            date: New date (optional)
            category: New category (optional)
            notes: New notes (optional)

        Returns:
            Updated transaction or None if not found
        """
        transaction = self.repo.get_by_id(transaction_id)
        if not transaction:
            return None

        # Create updated transaction
        updated_data = transaction.model_dump()
        if description is not None:
            updated_data["description"] = description
        if amount is not None:
            updated_data["amount"] = amount
        if date is not None:
            updated_data["date"] = date
        if category is not None:
            updated_data["category"] = category
        if notes is not None:
            updated_data["notes"] = notes

        updated = Transaction(**updated_data)
        self.repo.update(updated)
        return updated

    def delete_transaction(self, transaction_id: str) -> bool:
        """
        Delete a transaction.

        Args:
            transaction_id: Transaction ID

        Returns:
            True if deleted
        """
        return self.repo.delete(transaction_id)

    def delete_multiple(self, transaction_ids: List[str]) -> int:
        """
        Delete multiple transactions.

        Args:
            transaction_ids: List of transaction IDs

        Returns:
            Number of transactions deleted
        """
        return self.repo.delete_multiple(transaction_ids)

    def split_transaction(
        self, transaction_id: str, splits: List[SplitTransaction]
    ) -> List[Transaction]:
        """
        Split a transaction into multiple transactions across different categories.
        
        WHAT IS SPLITTING?
        ==================
        
        Splitting allows you to divide one transaction into multiple transactions,
        each with a different category. This is useful when a single purchase
        spans multiple categories.
        
        EXAMPLE:
        ========
        
        Original transaction:
        - Amount: $50.00
        - Description: "Walmart"
        - Category: "Shopping"
        
        Split into:
        1. $30.00 → "Groceries" category
        2. $20.00 → "Household Items" category
        
        HOW IT WORKS:
        =============
        
        1. **Load Original**: Get the transaction to split
        2. **Validate**: Ensure split amounts sum to original amount
        3. **Create Splits**: Create new transactions for each split
        4. **Preserve Metadata**: Copy date, account, reference from original
        5. **Link Splits**: Set parent_transaction_id to link splits to original
        6. **Save**: Store the new split transactions
        
        VALIDATION:
        ===========
        
        - Original transaction must exist
        - Split amounts must sum exactly to original amount
        - Tolerance: ±$0.01 (handles rounding errors)
        
        WHY KEEP ORIGINAL?
        ==================
        
        The original transaction is kept (not deleted) because:
        - Provides audit trail
        - Can be useful for reference
        - User can delete manually if desired
        
        LEARNING POINTS:
        ===============
        
        1. **Data Validation**: Always validate before operations
        2. **Business Rules**: Enforce rules (amounts must sum correctly)
        3. **Data Relationships**: Use parent_transaction_id to link related data
        4. **Error Messages**: Provide helpful error messages

        Args:
            transaction_id: ID of the transaction to split
            splits: List of SplitTransaction objects defining the splits
                   Each split has: amount, category, optional description

        Returns:
            List of new Transaction objects (the split transactions)

        Raises:
            ValueError: If transaction not found or split amounts don't sum correctly
            
        Example:
            >>> splits = [
            ...     SplitTransaction(
            ...         amount=Decimal("30.00"),
            ...         category=Category(name="Groceries")
            ...     ),
            ...     SplitTransaction(
            ...         amount=Decimal("20.00"),
            ...         category=Category(name="Household")
            ...     )
            ... ]
            >>> split_transactions = editor.split_transaction("txn-123", splits)
            >>> # Original $50 transaction is now split into $30 + $20
        """
        # Step 1: Load the original transaction
        original = self.repo.get_by_id(transaction_id)
        if not original:
            raise ValueError(f"Transaction {transaction_id} not found")

        # Step 2: Validate that split amounts sum to original amount
        # This is a critical business rule: you can't split $50 into $30 + $30
        total_split = sum(s.amount for s in splits)
        
        # Use absolute value comparison (handles both positive and negative amounts)
        # Allow small tolerance (±$0.01) for rounding errors
        if abs(total_split - abs(original.amount)) > Decimal("0.01"):
            raise ValueError(
                f"Split amounts ({total_split}) must equal original amount ({abs(original.amount)})"
            )

        # Step 3: Create split transactions
        split_transactions = []
        for split in splits:
            # Determine amount sign based on original transaction
            # If original was negative (expense), splits should be negative too
            # If original was positive (income), splits should be positive too
            amount = (
                -abs(split.amount) if original.amount < 0 else abs(split.amount)
            )

            # Create new transaction for this split
            # Preserve metadata from original (date, account, reference)
            # Add split-specific information (category, description)
            split_txn = Transaction(
                date=original.date,  # Same date as original
                amount=amount,  # Split amount (with correct sign)
                description=f"{original.description} - {split.description or split.category.name}",
                category=split.category,  # Different category for each split
                transaction_type=original.transaction_type,  # Same type
                account=original.account,  # Same account
                reference=original.reference,  # Same reference
                notes=split.description,  # Split-specific notes
                id=str(uuid.uuid4()),  # New unique ID
                parent_transaction_id=transaction_id,  # Link to original
            )
            split_transactions.append(split_txn)

        # Step 4: Save split transactions to storage
        self.repo.save(split_transactions)

        # Note: Original transaction is kept (not deleted)
        # This provides an audit trail and allows users to see what was split
        # Users can manually delete the original if desired

        return split_transactions

    def merge_transactions(
        self, transaction_ids: List[str], keep_first: bool = True
    ) -> Optional[Transaction]:
        """
        Merge multiple transactions into one.

        Args:
            transaction_ids: List of transaction IDs to merge
            keep_first: If True, keep first transaction's details; otherwise combine

        Returns:
            Merged transaction or None
        """
        if len(transaction_ids) < 2:
            raise ValueError("Need at least 2 transactions to merge")

        transactions = []
        for txn_id in transaction_ids:
            txn = self.repo.get_by_id(txn_id)
            if not txn:
                raise ValueError(f"Transaction {txn_id} not found")
            transactions.append(txn)

        if keep_first:
            # Use first transaction as base
            merged = transactions[0]
            # Sum amounts
            total_amount = sum(t.amount for t in transactions)
            merged = Transaction(
                **merged.model_dump(),
                amount=total_amount,
                description=f"{merged.description} (merged)",
            )
        else:
            # Combine all details
            total_amount = sum(t.amount for t in transactions)
            descriptions = [t.description for t in transactions]
            merged = Transaction(
                date=transactions[0].date,
                amount=total_amount,
                description=", ".join(descriptions),
                category=transactions[0].category,
                transaction_type=transactions[0].transaction_type,
                account=transactions[0].account,
                notes=f"Merged {len(transactions)} transactions",
                id=str(uuid.uuid4()),
            )

        # Save merged transaction
        self.repo.save([merged])

        # Delete original transactions
        self.repo.delete_multiple(transaction_ids)

        return merged

    def bulk_edit(
        self,
        transaction_ids: List[str],
        category: Optional[Category] = None,
        notes: Optional[str] = None,
    ) -> int:
        """
        Bulk edit multiple transactions.

        Args:
            transaction_ids: List of transaction IDs
            category: Category to assign (optional)
            notes: Notes to add (optional)

        Returns:
            Number of transactions updated
        """
        updated_count = 0
        for txn_id in transaction_ids:
            transaction = self.repo.get_by_id(txn_id)
            if not transaction:
                continue

            updated_data = transaction.model_dump()
            if category is not None:
                updated_data["category"] = category
            if notes is not None:
                existing_notes = updated_data.get("notes", "")
                updated_data["notes"] = (
                    f"{existing_notes}\n{notes}" if existing_notes else notes
                )

            updated = Transaction(**updated_data)
            if self.repo.update(updated):
                updated_count += 1

        return updated_count

