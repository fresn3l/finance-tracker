"""
End-to-end workflow for processing CSV files.

This module provides the main workflow orchestrator that combines all components
to process CSV files from start to finish: parsing, categorization, analysis, and storage.

The FinanceTrackerWorkflow class provides a high-level interface that:
    1. Parses CSV files into Transaction objects
    2. Detects and handles duplicate transactions
    3. Automatically categorizes transactions
    4. Saves transactions to persistent storage
    5. Provides analysis capabilities

This is the recommended way to use the finance tracker programmatically.

Example:
    >>> from finance_tracker.workflow import FinanceTrackerWorkflow
    >>> from pathlib import Path
    >>> 
    >>> workflow = FinanceTrackerWorkflow()
    >>> 
    >>> # Process a CSV file
    >>> transactions, stats = workflow.process_csv_file(
    ...     Path("bank_statement.csv"),
    ...     auto_categorize=True,
    ...     check_duplicates=True
    ... )
    >>> 
    >>> print(f"Imported {stats['new_transactions']} transactions")
    >>> print(f"Categorized: {stats.get('categorized', 0)}")
    >>> 
    >>> # Analyze spending
    >>> analyzer = workflow.analyze_spending()
    >>> summary = analyzer.get_monthly_summary(2024, 1)
    >>> 
    >>> # Get uncategorized transactions
    >>> uncategorized = workflow.get_uncategorized_transactions()
"""

import logging
from pathlib import Path
from typing import List, Optional

from finance_tracker.analyzer import SpendingAnalyzer
from finance_tracker.categorizer import TransactionCategorizer, categorize_transactions
from finance_tracker.csv_parser import CSVParser, parse_csv
from finance_tracker.models import Transaction
from finance_tracker.storage import StorageManager

logger = logging.getLogger(__name__)


class FinanceTrackerWorkflow:
    """
    End-to-end workflow orchestrator for processing financial transactions.
    
    WHAT IT DOES:
    =============
    
    This class coordinates the complete workflow of importing and processing CSV files:
    
    1. **Parse CSV**: Convert CSV file to Transaction objects
    2. **Detect Duplicates**: Check against existing transactions
    3. **Categorize**: Automatically assign categories
    4. **Store**: Save transactions to persistent storage
    5. **Analyze**: Provide analysis capabilities
    
    WORKFLOW PATTERN:
    =================
    
    This class implements the Workflow/Orchestrator pattern:
    - Coordinates multiple operations into a single workflow
    - Handles errors at the workflow level
    - Provides a high-level API for common tasks
    - Abstracts complexity from the user
    
    WHY USE A WORKFLOW?
    ===================
    
    - **Simplicity**: One method call does everything
    - **Consistency**: Same steps every time
    - **Error Handling**: Centralized error handling
    - **Logging**: Track progress through the workflow
    - **Testability**: Easy to test the complete flow
    
    EXAMPLE WORKFLOW:
    =================
    
    ```
    CSV File
      ↓
    [Parse] → Transaction objects (uncategorized)
      ↓
    [Check Duplicates] → Filter out duplicates
      ↓
    [Categorize] → Transaction objects (categorized)
      ↓
    [Store] → Saved to disk
      ↓
    [Analyze] → Reports and insights
    ```
    
    LEARNING POINTS:
    ================
    
    1. **Orchestration**: How to coordinate multiple operations
    2. **Error Handling**: Handle errors gracefully at workflow level
    3. **Dependency Injection**: Components are injected, not hardcoded
    4. **Separation of Concerns**: Workflow doesn't do the work, it coordinates
    
    Example:
        >>> workflow = FinanceTrackerWorkflow()
        >>> transactions, stats = workflow.process_csv_file(
        ...     Path("bank_statement.csv"),
        ...     auto_categorize=True
        ... )
        >>> print(f"Imported {stats['new_transactions']} transactions")
    """

    def __init__(self, data_dir: Optional[Path] = None, account: Optional[str] = None):
        """
        Initialize workflow with all necessary components.
        
        COMPONENT INITIALIZATION:
        ==========================
        
        This constructor sets up all the components needed for the workflow:
        
        - **StorageManager**: Handles data persistence
        - **CSVParser**: Parses CSV files into transactions
        - **TransactionCategorizer**: Categorizes transactions
        
        WHY DEPENDENCY INJECTION?
        =========================
        
        Components are created here, but could be injected for testing:
        - Makes testing easier (can inject mock objects)
        - Makes components reusable
        - Follows dependency inversion principle

        Args:
            data_dir: Optional data directory for storage
                     If None, uses default from configuration
            account: Optional account identifier
                     Useful when tracking multiple accounts
        """
        # Initialize storage manager (handles all data persistence)
        self.storage = StorageManager(data_dir)
        
        # Store account identifier for transactions
        self.account = account
        
        # Initialize CSV parser with account identifier
        # This ensures all parsed transactions get the account name
        self.parser = CSVParser(account=account)
        
        # Initialize categorizer (uses default category rules)
        self.categorizer = TransactionCategorizer()

    def process_csv_file(
        self,
        csv_file: Path,
        auto_categorize: bool = True,
        overwrite_categories: bool = False,
        check_duplicates: bool = True,
        skip_duplicates: bool = True,
    ) -> tuple[List[Transaction], dict]:
        """
        Process a CSV file through the complete workflow.
        
        COMPLETE WORKFLOW:
        ==================
        
        This method implements the complete end-to-end workflow:
        
        Step 1: Parse CSV File
        - Detects CSV format automatically
        - Converts rows to Transaction objects
        - Handles format-specific parsing
        
        Step 2: Duplicate Detection (optional)
        - Compares new transactions against stored ones
        - Uses transaction fingerprinting for comparison
        - Filters out duplicates if skip_duplicates=True
        
        Step 3: Categorization (optional)
        - Automatically assigns categories using rules
        - Can overwrite existing categories or preserve them
        - Tracks categorization statistics
        
        Step 4: Storage
        - Saves transactions to persistent storage
        - Only saves new transactions (duplicates already filtered)
        - Updates storage with categorized transactions
        
        Step 5: Statistics
        - Returns statistics about the import
        - Includes counts, categorization rates, etc.
        
        ERROR HANDLING:
        ===============
        
        - Errors are logged but don't stop the workflow
        - Partial results are returned if some steps fail
        - Descriptive error messages help with debugging
        
        Args:
            csv_file: Path to CSV file to process
            auto_categorize: If True, automatically categorize transactions
                           If False, transactions remain uncategorized
            overwrite_categories: If True, overwrite existing categories
                                If False, preserve existing categories
            check_duplicates: If True, check for duplicate transactions
            skip_duplicates: If True, skip duplicate transactions
                           If False, include duplicates (not recommended)

        Returns:
            Tuple containing:
            - List of processed transactions
            - Dictionary with statistics:
              * new_transactions: Number of new transactions added
              * duplicates_found: Number of duplicates found
              * categorized: Number of transactions categorized
              * categorization_rate: Percentage successfully categorized
              
        Example:
            >>> workflow = FinanceTrackerWorkflow()
            >>> transactions, stats = workflow.process_csv_file(
            ...     Path("statement.csv"),
            ...     auto_categorize=True,
            ...     check_duplicates=True
            ... )
            >>> print(f"Imported {stats['new_transactions']} new transactions")
            >>> print(f"Categorized {stats['categorized']} transactions")
        """
        logger.info(f"Processing CSV file: {csv_file}")

        # STEP 1: Parse CSV file
        # This converts the CSV file into Transaction objects
        # The parser automatically detects the format and uses the appropriate strategy
        logger.info("Parsing CSV file...")
        transactions = self.parser.parse(csv_file)
        logger.info(f"Parsed {len(transactions)} transactions")

        # STEP 2: Check for duplicates (if enabled)
        # This prevents importing the same transaction twice
        duplicates = []
        if check_duplicates:
            duplicates = self.storage.transaction_repo.check_duplicates(transactions)
            if duplicates:
                logger.warning(f"Found {len(duplicates)} duplicate transactions")
                if skip_duplicates:
                    # Create a helper function to get transaction ID
                    def get_txn_id(t):
                        parts = [
                            t.date.isoformat(),
                            str(t.amount),
                            t.description.strip().lower(),
                        ]
                        if t.reference:
                            parts.append(t.reference)
                        return "|".join(parts)

                    transaction_ids = {get_txn_id(t) for t in duplicates}
                    transactions = [
                        t for t in transactions if get_txn_id(t) not in transaction_ids
                    ]
                    logger.info(f"Skipped {len(duplicates)} duplicates, processing {len(transactions)} new transactions")

        # Categorize transactions
        if auto_categorize:
            logger.info("Categorizing transactions...")
            transactions, stats = self.categorizer.categorize_transactions(
                transactions, overwrite=overwrite_categories
            )
            logger.info(
                f"Categorized {stats.categorized_count}/{stats.total_transactions} "
                f"transactions ({stats.categorization_rate:.1f}%)"
            )
        else:
            stats = None

        # Save to storage
        logger.info("Saving transactions to storage...")
        self.storage.transaction_repo.save(transactions)
        logger.info(f"Saved {len(transactions)} transactions")

        # Prepare statistics
        result_stats = {
            "total_parsed": len(transactions) + len(duplicates),
            "new_transactions": len(transactions),
            "duplicates_found": len(duplicates),
            "duplicates_skipped": len(duplicates) if skip_duplicates else 0,
        }

        if stats:
            result_stats.update(
                {
                    "categorized": stats.categorized_count,
                    "uncategorized": stats.uncategorized_count,
                    "categorization_rate": stats.categorization_rate,
                }
            )

        return transactions, result_stats

    def analyze_spending(
        self, year: Optional[int] = None, month: Optional[int] = None
    ) -> SpendingAnalyzer:
        """
        Analyze spending from stored transactions.

        Args:
            year: Optional year to filter by
            month: Optional month to filter by (requires year)

        Returns:
            SpendingAnalyzer instance
        """
        transactions = self.storage.transaction_repo.load_all()
        analyzer = SpendingAnalyzer(transactions)
        return analyzer

    def get_uncategorized_transactions(self) -> List[Transaction]:
        """Get all uncategorized transactions from storage."""
        transactions = self.storage.transaction_repo.load_all()
        return self.categorizer.get_uncategorized_transactions(transactions)

    def recategorize_all(self, overwrite: bool = True) -> dict:
        """
        Recategorize all stored transactions.

        Args:
            overwrite: Whether to overwrite existing categories

        Returns:
            Statistics dictionary
        """
        logger.info("Recategorizing all transactions...")
        transactions = self.storage.transaction_repo.load_all()
        categorized, stats = self.categorizer.categorize_transactions(transactions, overwrite=overwrite)

        # Save recategorized transactions
        self.storage.transaction_repo.save(categorized)

        return {
            "total": stats.total_transactions,
            "categorized": stats.categorized_count,
            "uncategorized": stats.uncategorized_count,
            "categorization_rate": stats.categorization_rate,
        }


def process_csv(
    csv_file: Path,
    data_dir: Optional[Path] = None,
    account: Optional[str] = None,
    auto_categorize: bool = True,
) -> tuple[List[Transaction], dict]:
    """
    Convenience function to process a CSV file.

    Args:
        csv_file: Path to CSV file
        data_dir: Optional data directory
        account: Optional account identifier
        auto_categorize: Whether to automatically categorize

    Returns:
        Tuple of (processed transactions, statistics)
    """
    workflow = FinanceTrackerWorkflow(data_dir=data_dir, account=account)
    return workflow.process_csv_file(csv_file, auto_categorize=auto_categorize)

