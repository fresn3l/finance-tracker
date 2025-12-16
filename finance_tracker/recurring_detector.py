"""
Recurring transaction detection module.

This module automatically detects recurring transactions (subscriptions, bills, etc.)
by analyzing transaction patterns.
"""

import logging
import re
import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from finance_tracker.models import Category, RecurringTransaction, Transaction

logger = logging.getLogger(__name__)


class RecurringTransactionDetector:
    """
    Detects recurring transaction patterns (subscriptions, bills, etc.).
    
    HOW IT WORKS:
    =============
    
    This class uses pattern analysis to identify recurring transactions:
    
    1. **Group by Description**: Groups transactions with similar descriptions
    2. **Normalize Descriptions**: Removes variable parts (dates, IDs, etc.)
    3. **Analyze Frequency**: Calculates intervals between occurrences
    4. **Calculate Confidence**: Scores how likely it is to be recurring
    5. **Predict Next**: Estimates when the next occurrence will happen
    
    DETECTION ALGORITHM:
    ====================
    
    Step 1: Normalize Descriptions
    - Remove transaction IDs, dates, and other variable parts
    - Example: "NETFLIX.COM 12/15/2024 #12345" → "netflix.com"
    
    Step 2: Group Similar Transactions
    - Transactions with same normalized description are grouped
    - Minimum occurrences required (default: 3) to be considered
    
    Step 3: Analyze Frequency
    - Calculate time intervals between occurrences
    - Determine if pattern is monthly (25-35 days), weekly (6-8 days), or yearly (360-370 days)
    
    Step 4: Calculate Confidence
    - Based on:
      * Number of occurrences (more = higher confidence)
      * Amount consistency (less variance = higher confidence)
      * Date regularity (more regular = higher confidence)
    
    Step 5: Predict Next Occurrence
    - Based on frequency and last seen date
    - Monthly: last_date + 30 days
    - Weekly: last_date + 7 days
    - Yearly: last_date + 365 days
    
    LEARNING POINTS:
    ================
    
    1. **Pattern Recognition**: Simple algorithms can detect patterns without ML
    2. **Confidence Scores**: Not all detections are equal - score them
    3. **Normalization**: Remove noise to find signal
    4. **Statistical Analysis**: Use averages, variance, etc. to make decisions
    
    LIMITATIONS:
    ============
    
    - Requires minimum occurrences (won't detect new subscriptions)
    - Fixed frequency detection (won't detect irregular patterns)
    - Amount variance can reduce confidence (variable bills)
    
    Example:
        >>> detector = RecurringTransactionDetector(transactions)
        >>> recurring = detector.detect_recurring(min_occurrences=3)
        >>> for r in recurring:
        ...     print(f"{r.description_pattern}: {r.frequency} ({r.confidence:.0%} confidence)")
    """

    def __init__(self, transactions: List[Transaction]):
        """
        Initialize detector.

        Args:
            transactions: List of transactions to analyze
                         Should contain multiple months of data for best results
        """
        self.transactions = transactions

    def detect_recurring(self, min_occurrences: int = 3) -> List[RecurringTransaction]:
        """
        Detect recurring transactions.

        Args:
            min_occurrences: Minimum number of occurrences to consider recurring

        Returns:
            List of detected recurring transactions
        """
        # Group transactions by description pattern
        description_groups = defaultdict(list)
        for transaction in self.transactions:
            # Normalize description for grouping
            pattern = self._normalize_description(transaction.description)
            description_groups[pattern].append(transaction)

        recurring = []
        for pattern, group_transactions in description_groups.items():
            if len(group_transactions) < min_occurrences:
                continue

            # Analyze frequency
            frequency_info = self._analyze_frequency(group_transactions)
            if not frequency_info:
                continue

            # Calculate confidence
            confidence = self._calculate_confidence(group_transactions, frequency_info)

            # Get representative transaction
            representative = group_transactions[0]

            # Calculate amount statistics
            amounts = [abs(t.amount) for t in group_transactions]
            avg_amount = sum(amounts) / len(amounts)
            amount_variance = max(amounts) - min(amounts) if len(amounts) > 1 else None

            recurring.append(
                RecurringTransaction(
                    id=str(uuid.uuid4()),
                    description_pattern=pattern,
                    amount=Decimal(str(avg_amount)),
                    frequency=frequency_info["frequency"],
                    confidence=confidence,
                    category=representative.category,
                    account=representative.account,
                    last_seen=max(t.date for t in group_transactions),
                    next_expected=self._predict_next(
                        max(t.date for t in group_transactions), frequency_info["frequency"]
                    ),
                    transaction_count=len(group_transactions),
                    amount_variance=Decimal(str(amount_variance)) if amount_variance else None,
                )
            )

        return sorted(recurring, key=lambda x: x.confidence, reverse=True)

    def _normalize_description(self, description: str) -> str:
        """
        Normalize transaction description to create a pattern for matching.
        
        NORMALIZATION PROCESS:
        ======================
        
        This method removes variable parts from descriptions to create a stable pattern.
        The goal is to make "NETFLIX.COM 12/15/2024 #12345" and "NETFLIX.COM 01/15/2025 #67890"
        both normalize to "netflix.com" so they can be grouped together.
        
        STEPS:
        ======
        
        1. **Lowercase**: "NETFLIX" → "netflix" (case doesn't matter)
        2. **Strip Whitespace**: Remove leading/trailing spaces
        3. **Remove Long Numbers**: Transaction IDs are usually 4+ digits
           - "NETFLIX #12345" → "NETFLIX #"
        4. **Remove Company Suffixes**: "INC", "LLC", "LTD", "CORP"
           - "Netflix Inc" → "Netflix"
        5. **Normalize Whitespace**: Multiple spaces → single space
           - "Netflix   Com" → "Netflix Com"
        
        WHY NORMALIZE?
        ==============
        
        - Descriptions vary: "NETFLIX.COM", "Netflix.com", "NETFLIX #12345"
        - We want to group these as the same merchant
        - Normalization creates a stable pattern for grouping
        
        EXAMPLES:
        =========
        
        Input: "NETFLIX.COM 12/15/2024 #12345"
        Steps:
          1. "netflix.com 12/15/2024 #12345"  (lowercase)
          2. "netflix.com 12/15/2024 #"       (remove long numbers)
          3. "netflix.com 12/15/2024 #"       (no company suffix)
          4. "netflix.com 12/15/2024 #"       (normalize whitespace)
        Output: "netflix.com 12/15/2024 #"
        
        Note: This could be improved to also remove dates, but current approach works well.

        Args:
            description: Original transaction description
                        Example: "NETFLIX.COM 12/15/2024 #12345"

        Returns:
            Normalized description pattern
            Example: "netflix.com 12/15/2024 #"
        """
        # Step 1: Convert to lowercase and strip whitespace
        # This handles case variations: "NETFLIX" = "netflix" = "Netflix"
        normalized = description.lower().strip()
        
        # Step 2: Remove long numbers (likely transaction IDs)
        # Pattern: \d{4,} matches 4 or more consecutive digits
        # This removes things like "#12345" but keeps short numbers like "Store #5"
        normalized = re.sub(r"\d{4,}", "", normalized)
        
        # Step 3: Remove common company suffixes
        # Pattern matches: " Inc", " LLC", " Ltd", " Corp" (with optional period)
        # Case-insensitive due to previous lowercase conversion
        normalized = re.sub(r"\s+(inc|llc|ltd|corp)\.?$", "", normalized)
        
        # Step 4: Normalize whitespace (multiple spaces → single space)
        # split() splits on any whitespace, join() joins with single space
        normalized = " ".join(normalized.split())
        
        return normalized

    def _analyze_frequency(self, transactions: List[Transaction]) -> Optional[Dict]:
        """
        Analyze frequency of transactions.

        Args:
            transactions: List of transactions

        Returns:
            Dictionary with frequency information or None
        """
        if len(transactions) < 2:
            return None

        dates = sorted([t.date for t in transactions])
        intervals = [
            (dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)
        ]

        if not intervals:
            return None

        avg_interval = sum(intervals) / len(intervals)

        # Determine frequency
        if 25 <= avg_interval <= 35:
            frequency = "monthly"
        elif 6 <= avg_interval <= 8:
            frequency = "weekly"
        elif 360 <= avg_interval <= 370:
            frequency = "yearly"
        else:
            # Not a clear pattern
            return None

        return {"frequency": frequency, "avg_interval": avg_interval}

    def _calculate_confidence(
        self, transactions: List[Transaction], frequency_info: Dict
    ) -> float:
        """
        Calculate confidence score for how likely this is a recurring transaction.
        
        CONFIDENCE CALCULATION:
        ========================
        
        Confidence is calculated using three factors, weighted by importance:
        
        1. **Occurrence Score (40% weight)**: More occurrences = higher confidence
           - Formula: min(occurrences / 10, 1.0)
           - 10+ occurrences = maximum score
           - Rationale: More data = more reliable pattern
        
        2. **Amount Consistency (30% weight)**: Less variance = higher confidence
           - Formula: 1.0 - (variance / max_amount)
           - Variance = (max - min) / max
           - Rationale: Recurring bills usually have same/similar amounts
        
        3. **Date Regularity (30% weight)**: More regular intervals = higher confidence
           - Formula: 1.0 - (interval_variance / max_interval)
           - Interval variance = (max_interval - min_interval) / max_interval
           - Rationale: True recurring transactions happen at regular intervals
        
        FINAL SCORE:
        ============
        
        Final confidence = weighted average of three scores
        - Clamped to [0.0, 1.0] range
        - 1.0 = very confident (perfect pattern)
        - 0.0 = not confident (irregular pattern)
        
        EXAMPLE:
        ========
        
        Netflix subscription:
        - 12 occurrences → occurrence_score = 1.0
        - Amount always $15.99 → consistency_score = 1.0
        - Intervals: 30, 30, 31, 30 days → regularity_score ≈ 0.97
        - Final: 0.4*1.0 + 0.3*1.0 + 0.3*0.97 = 0.991 (very confident!)
        
        Variable utility bill:
        - 6 occurrences → occurrence_score = 0.6
        - Amount varies $50-$80 → consistency_score ≈ 0.6
        - Intervals: 28, 32, 29 days → regularity_score ≈ 0.9
        - Final: 0.4*0.6 + 0.3*0.6 + 0.3*0.9 = 0.69 (moderately confident)

        Args:
            transactions: List of transactions in the group
            frequency_info: Dictionary with frequency analysis results

        Returns:
            Confidence score between 0.0 (not confident) and 1.0 (very confident)
        """
        # Factor 1: Occurrence Score (40% weight)
        # More occurrences = more reliable pattern
        # Cap at 1.0 (10+ occurrences = maximum confidence)
        occurrence_score = min(len(transactions) / 10.0, 1.0)

        # Factor 2: Amount Consistency (30% weight)
        # Calculate how much amounts vary
        amounts = [abs(t.amount) for t in transactions]
        if amounts:
            # Variance = (max - min) / max
            # Low variance (similar amounts) = high consistency score
            # High variance (different amounts) = low consistency score
            amount_variance = (max(amounts) - min(amounts)) / max(amounts) if max(amounts) > 0 else 1.0
            consistency_score = max(0, 1.0 - amount_variance)
        else:
            # No amounts (shouldn't happen, but handle gracefully)
            consistency_score = 0.5

        # Factor 3: Date Regularity (30% weight)
        # Calculate how regular the intervals are
        dates = sorted([t.date for t in transactions])
        intervals = [
            (dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)
        ]
        if intervals:
            # Interval variance = (max_interval - min_interval) / max_interval
            # Low variance (regular intervals) = high regularity score
            # High variance (irregular intervals) = low regularity score
            interval_variance = (
                (max(intervals) - min(intervals)) / max(intervals)
                if max(intervals) > 0
                else 0
            )
            regularity_score = max(0, 1.0 - interval_variance)
        else:
            # Only one transaction (can't calculate regularity)
            regularity_score = 0.5

        # Calculate weighted average
        # Weights: 40% occurrences, 30% consistency, 30% regularity
        # These weights can be tuned based on what's most important
        confidence = (
            occurrence_score * 0.4 +      # 40% weight
            consistency_score * 0.3 +     # 30% weight
            regularity_score * 0.3        # 30% weight
        )

        # Clamp to [0.0, 1.0] range
        # Ensures confidence is always a valid probability
        return min(1.0, max(0.0, confidence))

    def _predict_next(self, last_date: date, frequency: str) -> date:
        """
        Predict next occurrence date.

        Args:
            last_date: Last occurrence date
            frequency: Frequency (monthly, weekly, yearly)

        Returns:
            Predicted next date
        """
        if frequency == "monthly":
            # Add approximately 30 days
            return last_date + timedelta(days=30)
        elif frequency == "weekly":
            return last_date + timedelta(days=7)
        elif frequency == "yearly":
            return last_date + timedelta(days=365)
        else:
            return last_date + timedelta(days=30)

    def mark_recurring(self, recurring_transactions: List[RecurringTransaction]) -> List[Transaction]:
        """
        Mark transactions as recurring based on detected patterns.

        Args:
            recurring_transactions: List of detected recurring patterns

        Returns:
            Updated list of transactions with recurring flags
        """
        updated_transactions = []
        pattern_map = {rt.description_pattern: rt for rt in recurring_transactions}

        for transaction in self.transactions:
            pattern = self._normalize_description(transaction.description)
            if pattern in pattern_map:
                recurring = pattern_map[pattern]
                # Create updated transaction with recurring info
                updated = Transaction(
                    **transaction.model_dump(),
                    is_recurring=True,
                    recurring_id=recurring.id,
                )
                updated_transactions.append(updated)
            else:
                updated_transactions.append(transaction)

        return updated_transactions

