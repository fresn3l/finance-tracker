"""
Spending analysis module for financial transactions.

This module provides comprehensive analysis of spending patterns, including:
    - Monthly summaries with income/expense breakdowns
    - Category-level spending analysis
    - Spending trends and patterns
    - Top categories identification
    - Average spending calculations

The analyzer works with lists of Transaction objects and provides various
aggregation and analysis methods.

Example:
    >>> from finance_tracker.analyzer import SpendingAnalyzer
    >>> 
    >>> analyzer = SpendingAnalyzer(transactions)
    >>> 
    >>> # Get monthly summary
    >>> summary = analyzer.get_monthly_summary(2024, 1)
    >>> print(f"Income: ${summary.total_income}")
    >>> print(f"Expenses: ${summary.total_expenses}")
    >>> print(f"Savings Rate: {summary.savings_rate:.1f}%")
    >>> 
    >>> # Get category breakdown
    >>> breakdown = analyzer.get_category_breakdown()
    >>> for category, amount in breakdown.items():
    ...     print(f"{category}: ${amount}")
    >>> 
    >>> # Get top spending categories
    >>> top = analyzer.get_top_categories(limit=5)
    >>> for pattern in top:
    ...     print(f"{pattern.category}: ${pattern.total_amount}")
"""

from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from finance_tracker.models import (
    CashFlowSummary,
    CategoryDelta,
    ComparisonDelta,
    MonthlySummary,
    MonthOverMonthComparison,
    SpendingForecast,
    SpendingPattern,
    Transaction,
    TransactionType,
)


class SpendingAnalyzer:
    """Analyzer for spending patterns and financial summaries."""

    def __init__(self, transactions: List[Transaction]):
        """
        Initialize spending analyzer.

        Args:
            transactions: List of transactions to analyze
        """
        self.transactions = transactions

    def get_monthly_summary(self, year: int, month: int) -> MonthlySummary:
        """
        Generate monthly summary for a specific month.

        Args:
            year: Year to analyze
            month: Month to analyze (1-12)

        Returns:
            MonthlySummary object
        """
        # Filter transactions for the specified month
        month_transactions = [
            t
            for t in self.transactions
            if t.date.year == year and t.date.month == month
        ]

        total_income = Decimal("0")
        total_expenses = Decimal("0")
        category_breakdown: Dict[str, Decimal] = defaultdict(Decimal)

        for transaction in month_transactions:
            if transaction.is_income:
                total_income += transaction.absolute_amount
            elif transaction.is_expense:
                amount = transaction.absolute_amount
                total_expenses += amount

                # Add to category breakdown if categorized
                if transaction.category:
                    category_name = transaction.category.name
                    category_breakdown[category_name] += amount

        net_amount = total_income - total_expenses

        return MonthlySummary(
            year=year,
            month=month,
            total_income=total_income,
            total_expenses=total_expenses,
            net_amount=net_amount,
            transaction_count=len(month_transactions),
            category_breakdown=dict(category_breakdown),
        )

    def get_all_monthly_summaries(self) -> List[MonthlySummary]:
        """
        Generate monthly summaries for all months with transactions.

        Returns:
            List of MonthlySummary objects, sorted by year and month
        """
        # Get all unique year-month combinations
        months = set()
        for transaction in self.transactions:
            months.add((transaction.date.year, transaction.date.month))

        summaries = [self.get_monthly_summary(year, month) for year, month in sorted(months)]
        return summaries

    def get_category_breakdown(
        self, year: Optional[int] = None, month: Optional[int] = None
    ) -> Dict[str, Decimal]:
        """
        Get spending breakdown by category.

        Args:
            year: Optional year to filter by
            month: Optional month to filter by (requires year)

        Returns:
            Dictionary mapping category names to total spending
        """
        filtered_transactions = self.transactions

        if year is not None:
            filtered_transactions = [
                t for t in filtered_transactions if t.date.year == year
            ]
            if month is not None:
                filtered_transactions = [
                    t for t in filtered_transactions if t.date.month == month
                ]

        category_totals: Dict[str, Decimal] = defaultdict(Decimal)

        for transaction in filtered_transactions:
            if transaction.is_expense and transaction.category:
                category_name = transaction.category.name
                category_totals[category_name] += transaction.absolute_amount

        return dict(category_totals)

    def get_spending_patterns(
        self, category_name: Optional[str] = None
    ) -> List[SpendingPattern]:
        """
        Get spending patterns for categories.

        Args:
            category_name: Optional category name to filter by. If None, returns patterns for all categories.

        Returns:
            List of SpendingPattern objects
        """
        # Group transactions by category
        category_transactions: Dict[str, List[Transaction]] = defaultdict(list)

        for transaction in self.transactions:
            if transaction.is_expense and transaction.category:
                cat_name = transaction.category.name
                if category_name is None or cat_name == category_name:
                    category_transactions[cat_name].append(transaction)

        patterns = []
        total_spending = sum(
            t.absolute_amount
            for t in self.transactions
            if t.is_expense and t.category
        )

        for cat_name, transactions in category_transactions.items():
            amounts = [t.absolute_amount for t in transactions]
            total_amount = sum(amounts)
            transaction_count = len(transactions)

            if transaction_count > 0:
                average = total_amount / transaction_count
                min_amount = min(amounts)
                max_amount = max(amounts)
                percentage = (
                    (total_amount / total_spending * 100) if total_spending > 0 else None
                )

                pattern = SpendingPattern(
                    category=cat_name,
                    total_amount=total_amount,
                    transaction_count=transaction_count,
                    average_transaction=average,
                    min_transaction=min_amount,
                    max_transaction=max_amount,
                    percentage_of_total=percentage,
                )
                patterns.append(pattern)

        return patterns

    def get_top_categories(self, limit: int = 10) -> List[SpendingPattern]:
        """
        Get top spending categories by total amount.

        Args:
            limit: Number of top categories to return

        Returns:
            List of SpendingPattern objects, sorted by total amount (descending)
        """
        patterns = self.get_spending_patterns()
        sorted_patterns = sorted(patterns, key=lambda p: p.total_amount, reverse=True)
        return sorted_patterns[:limit]

    def get_total_income(self, year: Optional[int] = None, month: Optional[int] = None) -> Decimal:
        """
        Calculate total income.

        Args:
            year: Optional year to filter by
            month: Optional month to filter by (requires year)

        Returns:
            Total income as Decimal
        """
        filtered = self._filter_transactions(year, month)
        return sum(
            t.absolute_amount for t in filtered if t.is_income
        )

    def get_total_expenses(
        self, year: Optional[int] = None, month: Optional[int] = None
    ) -> Decimal:
        """
        Calculate total expenses.

        Args:
            year: Optional year to filter by
            month: Optional month to filter by (requires year)

        Returns:
            Total expenses as Decimal
        """
        filtered = self._filter_transactions(year, month)
        return sum(
            t.absolute_amount for t in filtered if t.is_expense
        )

    def get_net_amount(self, year: Optional[int] = None, month: Optional[int] = None) -> Decimal:
        """
        Calculate net amount (income - expenses).

        Args:
            year: Optional year to filter by
            month: Optional month to filter by (requires year)

        Returns:
            Net amount as Decimal
        """
        return self.get_total_income(year, month) - self.get_total_expenses(year, month)

    def get_average_monthly_spending(self, category_name: Optional[str] = None) -> Decimal:
        """
        Calculate average monthly spending.

        Args:
            category_name: Optional category name to filter by

        Returns:
            Average monthly spending as Decimal
        """
        summaries = self.get_all_monthly_summaries()
        if not summaries:
            return Decimal("0")

        if category_name:
            # Calculate average for specific category
            category_totals = [
                summary.category_breakdown.get(category_name, Decimal("0"))
                for summary in summaries
            ]
            total = sum(category_totals)
            return total / len(summaries) if summaries else Decimal("0")
        else:
            # Calculate average total expenses
            total_expenses = sum(s.total_expenses for s in summaries)
            return total_expenses / len(summaries) if summaries else Decimal("0")

    def get_spending_trend(
        self, category_name: str, months: int = 3
    ) -> Optional[str]:
        """
        Determine spending trend for a category.

        Analyzes recent spending patterns to determine if spending in a category
        is increasing, decreasing, or stable. Uses a simple comparison of first
        half vs second half of the time period.

        Args:
            category_name: Category name to analyze
            months: Number of recent months to consider (default: 3)

        Returns:
            Trend direction: "increasing", "decreasing", or "stable"
            Returns None if insufficient data (< 2 months or < 2 data points)

        Algorithm:
            1. Get spending amounts for recent months
            2. Split into first half and second half
            3. Compare totals:
               - >10% increase → "increasing"
               - >10% decrease → "decreasing"
               - Otherwise → "stable"

        Example:
            >>> analyzer.get_spending_trend("Groceries", months=6)
            'increasing'
        """
        summaries = self.get_all_monthly_summaries()
        if len(summaries) < 2:
            return None  # Need at least 2 months of data

        # Get recent months (most recent first due to sorting)
        recent_summaries = summaries[-months:]
        # Extract spending amounts for the category from each month
        amounts = [
            s.category_breakdown.get(category_name, Decimal("0")) for s in recent_summaries
        ]

        if len(amounts) < 2:
            return None  # Need at least 2 data points

        # Split into first half and second half for comparison
        # This compares earlier period vs later period
        midpoint = len(amounts) // 2
        first_half = sum(amounts[:midpoint])
        second_half = sum(amounts[midpoint:])

        # Use 10% threshold to avoid noise from small fluctuations
        # This means a change must be >10% to be considered a trend
        if second_half > first_half * Decimal("1.1"):  # 10% increase threshold
            return "increasing"
        elif second_half < first_half * Decimal("0.9"):  # 10% decrease threshold
            return "decreasing"
        else:
            return "stable"  # Change is within ±10%, considered stable

    def get_month_over_month(
        self, year: int, month: int
    ) -> MonthOverMonthComparison:
        """
        Compare a month to the previous calendar month.

        Returns dollar and percent deltas for income, expenses, net, and
        every category that appears in either month.
        """
        prev_year, prev_month = previous_calendar_month(year, month)
        current = self.get_monthly_summary(year, month)
        previous = self.get_monthly_summary(prev_year, prev_month)

        categories = set(current.category_breakdown) | set(previous.category_breakdown)
        category_deltas = [
            _category_delta(
                name,
                current.category_breakdown.get(name, Decimal("0")),
                previous.category_breakdown.get(name, Decimal("0")),
            )
            for name in categories
        ]
        category_deltas.sort(key=lambda d: abs(d.delta), reverse=True)

        return MonthOverMonthComparison(
            year=year,
            month=month,
            previous_year=prev_year,
            previous_month=prev_month,
            income=_comparison_delta(current.total_income, previous.total_income),
            expenses=_comparison_delta(current.total_expenses, previous.total_expenses),
            net=_comparison_delta(current.net_amount, previous.net_amount),
            savings_rate_current=current.savings_rate,
            savings_rate_previous=previous.savings_rate,
            transaction_count_current=current.transaction_count,
            transaction_count_previous=previous.transaction_count,
            category_deltas=category_deltas,
        )

    def get_latest_month_over_month(self) -> Optional[MonthOverMonthComparison]:
        """MoM comparison for the most recent month that has transactions."""
        summaries = self.get_all_monthly_summaries()
        if not summaries:
            return None
        latest = summaries[-1]
        return self.get_month_over_month(latest.year, latest.month)

    def get_cash_flow(self, year: int, month: int) -> CashFlowSummary:
        """
        Split a month into operating income/expenses vs internal transfers.
        """
        month_transactions = self._filter_transactions(year, month)
        income = Decimal("0")
        expenses = Decimal("0")
        transfers_in = Decimal("0")
        transfers_out = Decimal("0")

        for transaction in month_transactions:
            if transaction.transaction_type == TransactionType.TRANSFER:
                if transaction.amount > 0:
                    transfers_in += transaction.absolute_amount
                else:
                    transfers_out += transaction.absolute_amount
            elif transaction.is_income:
                income += transaction.absolute_amount
            elif transaction.is_expense:
                expenses += transaction.absolute_amount

        net_operating = income - expenses
        return CashFlowSummary(
            year=year,
            month=month,
            income=income,
            expenses=expenses,
            transfers_in=transfers_in,
            transfers_out=transfers_out,
            net_operating=net_operating,
            net_cash=net_operating + transfers_in - transfers_out,
        )

    def forecast_next_month(
        self, months: int = 3, category_name: Optional[str] = None
    ) -> Optional[SpendingForecast]:
        """
        Predict next-month spending with a simple moving average.

        Uses the most recent `months` monthly totals (overall expenses or one
        category). Returns None if there is no history.
        """
        summaries = self.get_all_monthly_summaries()
        if not summaries:
            return None

        recent = summaries[-months:]
        if category_name:
            totals = [
                s.category_breakdown.get(category_name, Decimal("0")) for s in recent
            ]
        else:
            totals = [s.total_expenses for s in recent]

        average = sum(totals) / len(totals)
        return SpendingForecast(
            category=category_name,
            predicted_amount=average,
            months_used=len(recent),
            method="moving_average",
            average_monthly=average,
        )

    def forecast_all_categories(self, months: int = 3) -> List[SpendingForecast]:
        """Moving-average forecast for total expenses and each category."""
        forecasts = []
        overall = self.forecast_next_month(months=months)
        if overall:
            forecasts.append(overall)

        categories = set()
        for summary in self.get_all_monthly_summaries():
            categories.update(summary.category_breakdown.keys())
        for name in sorted(categories):
            forecast = self.forecast_next_month(months=months, category_name=name)
            if forecast:
                forecasts.append(forecast)
        return forecasts

    def _filter_transactions(
        self, year: Optional[int] = None, month: Optional[int] = None
    ) -> List[Transaction]:
        """Filter transactions by year and/or month."""
        filtered = self.transactions
        if year is not None:
            filtered = [t for t in filtered if t.date.year == year]
            if month is not None:
                filtered = [t for t in filtered if t.date.month == month]
        return filtered


def previous_calendar_month(year: int, month: int) -> Tuple[int, int]:
    """Return (year, month) for the prior calendar month."""
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _percent_change(current: Decimal, previous: Decimal) -> Optional[float]:
    """Percent change; None when previous is zero and current is not."""
    if previous == 0:
        return 0.0 if current == 0 else None
    return float((current - previous) / abs(previous) * 100)


def _comparison_delta(current: Decimal, previous: Decimal) -> ComparisonDelta:
    return ComparisonDelta(
        current=current,
        previous=previous,
        delta=current - previous,
        percent_change=_percent_change(current, previous),
    )


def _category_delta(name: str, current: Decimal, previous: Decimal) -> CategoryDelta:
    return CategoryDelta(
        category=name,
        current=current,
        previous=previous,
        delta=current - previous,
        percent_change=_percent_change(current, previous),
    )


def analyze_spending(transactions: List[Transaction]) -> SpendingAnalyzer:
    """
    Convenience function to create a SpendingAnalyzer.

    Args:
        transactions: List of transactions to analyze

    Returns:
        SpendingAnalyzer instance
    """
    return SpendingAnalyzer(transactions)

