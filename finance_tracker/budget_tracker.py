"""
Budget tracking module for finance tracker.

This module provides budget management functionality including:
- Setting and tracking monthly budgets per category
- Budget vs. spending analysis
- Budget alerts
- Budget templates for quick setup
"""

import json
import logging
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional

from finance_tracker.analyzer import SpendingAnalyzer
from finance_tracker.models import Budget, BudgetTemplate, Transaction
from finance_tracker.storage import JSONEncoder

logger = logging.getLogger(__name__)


class BudgetRepository:
    """Repository for managing budget storage."""

    def __init__(self, data_dir: Path):
        """
        Initialize budget repository.

        Args:
            data_dir: Directory where budget data is stored
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.budgets_file = self.data_dir / "budgets.json"
        self.templates_file = self.data_dir / "budget_templates.json"

    def save_budget(self, budget: Budget) -> None:
        """
        Save a budget.

        Args:
            budget: Budget to save
        """
        budgets = self.load_all_budgets()
        # Remove existing budget for same category/month/year
        budgets = [
            b
            for b in budgets
            if not (
                b.category_name == budget.category_name
                and b.year == budget.year
                and b.month == budget.month
            )
        ]
        budgets.append(budget)
        self._save_all_budgets(budgets)

    def load_all_budgets(self) -> List[Budget]:
        """
        Load all budgets.

        Returns:
            List of all budgets
        """
        if not self.budgets_file.exists():
            return []

        try:
            with open(self.budgets_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            budgets = []
            for budget_data in data.get("budgets", []):
                budgets.append(
                    Budget(
                        category_name=budget_data["category_name"],
                        year=budget_data["year"],
                        month=budget_data["month"],
                        amount=Decimal(budget_data["amount"]),
                        alert_threshold=Decimal(budget_data.get("alert_threshold", "0.8")),
                        notes=budget_data.get("notes"),
                    )
                )

            return budgets
        except Exception as e:
            logger.error(f"Error loading budgets: {e}")
            return []

    def get_budget(self, category_name: str, year: int, month: int) -> Optional[Budget]:
        """
        Get budget for a specific category and month.

        Args:
            category_name: Category name
            year: Year
            month: Month (1-12)

        Returns:
            Budget if found, None otherwise
        """
        budgets = self.load_all_budgets()
        for budget in budgets:
            if (
                budget.category_name == category_name
                and budget.year == year
                and budget.month == month
            ):
                return budget
        return None

    def delete_budget(self, category_name: str, year: int, month: int) -> bool:
        """
        Delete a budget.

        Args:
            category_name: Category name
            year: Year
            month: Month

        Returns:
            True if deleted, False if not found
        """
        budgets = self.load_all_budgets()
        original_count = len(budgets)
        budgets = [
            b
            for b in budgets
            if not (
                b.category_name == category_name
                and b.year == year
                and b.month == month
            )
        ]

        if len(budgets) < original_count:
            self._save_all_budgets(budgets)
            return True
        return False

    def _save_all_budgets(self, budgets: List[Budget]) -> None:
        """Save all budgets to file."""
        data = {
            "budgets": [
                {
                    "category_name": b.category_name,
                    "year": b.year,
                    "month": b.month,
                    "amount": str(b.amount),
                    "alert_threshold": str(b.alert_threshold),
                    "notes": b.notes,
                }
                for b in budgets
            ]
        }
        with open(self.budgets_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, cls=JSONEncoder)

    def save_template(self, template: BudgetTemplate) -> None:
        """
        Save a budget template.

        Args:
            template: Template to save
        """
        templates = self.load_templates()
        # Remove existing template with same name
        templates = [t for t in templates if t.name != template.name]
        templates.append(template)
        self._save_templates(templates)

    def load_templates(self) -> List[BudgetTemplate]:
        """
        Load all budget templates.

        Returns:
            List of templates
        """
        if not self.templates_file.exists():
            return []

        try:
            with open(self.templates_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            templates = []
            for template_data in data.get("templates", []):
                templates.append(
                    BudgetTemplate(
                        name=template_data["name"],
                        category_budgets={
                            k: Decimal(v)
                            for k, v in template_data["category_budgets"].items()
                        },
                        description=template_data.get("description"),
                    )
                )

            return templates
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
            return []

    def _save_templates(self, templates: List[BudgetTemplate]) -> None:
        """Save all templates to file."""
        data = {
            "templates": [
                {
                    "name": t.name,
                    "category_budgets": {k: str(v) for k, v in t.category_budgets.items()},
                    "description": t.description,
                }
                for t in templates
            ]
        }
        with open(self.templates_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, cls=JSONEncoder)


class BudgetTracker:
    """
    Budget tracking and analysis engine.
    
    WHAT IT DOES:
    =============
    
    This class provides budget management and tracking functionality:
    
    1. **Budget Status**: Compare spending vs. budget for categories
    2. **Budget Alerts**: Identify when budgets are approaching or exceeded
    3. **Progress Tracking**: Calculate percentage spent, remaining amount
    4. **Multi-Category**: Track budgets for multiple categories simultaneously
    
    HOW IT WORKS:
    =============
    
    The tracker combines budget data with transaction data:
    
    1. **Load Budget**: Get budget for a category/month from repository
    2. **Calculate Spending**: Sum actual spending from transactions
    3. **Compare**: Calculate difference, percentage, status
    4. **Generate Alerts**: Identify when thresholds are reached
    
    BUDGET STATUS CALCULATION:
    ==========================
    
    For each budget:
    - Spent = sum of transactions in that category for the month
    - Remaining = Budget - Spent
    - Percentage = (Spent / Budget) * 100
    - Alert Threshold = Budget * alert_threshold (default 80%)
    - Should Alert = Spent >= Alert Threshold
    - Over Budget = Spent > Budget
    
    LEARNING POINTS:
    ================
    
    1. **Data Aggregation**: Sum transactions by category and month
    2. **Comparison Logic**: Compare actual vs. planned spending
    3. **Threshold Detection**: Identify when alerts should trigger
    4. **Status Reporting**: Provide clear status information
    
    Example:
        >>> tracker = BudgetTracker(transactions, budget_repo)
        >>> status = tracker.get_budget_status("Groceries", 2024, 1)
        >>> print(f"Spent: ${status['spent']} of ${status['budget']}")
        >>> print(f"Remaining: ${status['remaining']}")
        >>> if status['should_alert']:
        ...     print("⚠️ Budget alert!")
    """

    def __init__(
        self, transactions: List[Transaction], budget_repo: BudgetRepository
    ):
        """
        Initialize budget tracker with transactions and budget repository.

        Args:
            transactions: List of transactions to analyze
                         Used to calculate actual spending
            budget_repo: Budget repository
                        Used to load budget data
        """
        self.transactions = transactions
        self.budget_repo = budget_repo
        
        # Use SpendingAnalyzer for category breakdown calculations
        # This reuses existing analysis logic rather than duplicating it
        self.analyzer = SpendingAnalyzer(transactions)

    def get_budget_status(
        self, category_name: str, year: int, month: int
    ) -> Dict:
        """
        Get budget status for a specific category and month.
        
        BUDGET STATUS CALCULATION:
        ==========================
        
        This method calculates the current status of a budget by comparing
        the budgeted amount with actual spending:
        
        1. **Load Budget**: Get budget for category/month
        2. **Calculate Spending**: Sum actual transactions in that category
        3. **Calculate Metrics**:
           - Percentage spent: (spent / budget) * 100
           - Remaining: budget - spent
           - Alert threshold: budget * alert_threshold (e.g., 80%)
        4. **Determine Status**:
           - Should alert: spent >= alert threshold
           - Over budget: spent > budget
        
        STATUS INDICATORS:
        ==================
        
        - **has_budget**: Whether a budget exists for this category/month
        - **percentage_spent**: How much of the budget has been used (0-100%)
        - **remaining**: How much budget is left (can be negative if over budget)
        - **should_alert**: Whether to show an alert (spent >= threshold)
        - **over_budget**: Whether spending exceeds the budget
        
        EXAMPLE:
        ========
        
        Budget: $500 for Groceries in January
        Spent: $400
        
        Result:
        - percentage_spent: 80%
        - remaining: $100
        - should_alert: True (if threshold is 80%)
        - over_budget: False
        
        If spent: $550
        - percentage_spent: 110%
        - remaining: -$50 (negative = over budget)
        - should_alert: True
        - over_budget: True

        Args:
            category_name: Name of the category to check
            year: Year to check (e.g., 2024)
            month: Month to check (1-12)

        Returns:
            Dictionary with budget status:
            - has_budget: bool - Whether budget exists
            - budget: str - Budget amount (if exists)
            - spent: str - Actual spending (if exists)
            - remaining: str - Remaining budget (if exists)
            - percentage_spent: float - Percentage of budget used (if exists)
            - alert_threshold: str - Alert threshold amount (if exists)
            - should_alert: bool - Whether to alert (if exists)
            - over_budget: bool - Whether over budget (if exists)
        """
        # Step 1: Load budget from repository
        # Returns None if no budget exists for this category/month
        budget = self.budget_repo.get_budget(category_name, year, month)
        if not budget:
            # No budget set - return simple status
            return {"has_budget": False}

        # Step 2: Calculate actual spending for this category/month
        # Uses SpendingAnalyzer to get category breakdown
        # This reuses existing analysis logic
        breakdown = self.analyzer.get_category_breakdown(year=year, month=month)
        
        # Get spending for this category (default to 0 if no transactions)
        spent = breakdown.get(category_name, Decimal("0"))

        # Step 3: Calculate percentage spent
        # Formula: (spent / budget) * 100
        # Handle division by zero (shouldn't happen, but be safe)
        percentage_spent = float((spent / budget.amount) * 100) if budget.amount > 0 else 0
        
        # Step 4: Calculate remaining budget
        # Can be negative if over budget
        remaining = budget.amount - spent
        
        # Step 5: Calculate alert threshold amount
        # alert_threshold is a decimal (e.g., 0.8 = 80%)
        alert_threshold_amount = budget.amount * budget.alert_threshold

        # Step 6: Return comprehensive status
        return {
            "has_budget": True,
            "budget": str(budget.amount),  # Convert Decimal to string for JSON
            "spent": str(spent),
            "remaining": str(remaining),
            "percentage_spent": percentage_spent,  # Float for percentage
            "alert_threshold": str(alert_threshold_amount),
            "should_alert": spent >= alert_threshold_amount,  # Boolean
            "over_budget": spent > budget.amount,  # Boolean
        }

    def get_all_budget_statuses(self, year: int, month: int) -> List[Dict]:
        """
        Get budget status for all categories with budgets.

        Args:
            year: Year
            month: Month

        Returns:
            List of budget status dictionaries
        """
        budgets = self.budget_repo.load_all_budgets()
        month_budgets = [b for b in budgets if b.year == year and b.month == month]

        statuses = []
        for budget in month_budgets:
            status = self.get_budget_status(budget.category_name, year, month)
            status["category_name"] = budget.category_name
            statuses.append(status)

        return statuses

    def check_alerts(self, year: int, month: int) -> List[Dict]:
        """
        Check for budget alerts.

        Args:
            year: Year
            month: Month

        Returns:
            List of alerts
        """
        statuses = self.get_all_budget_statuses(year, month)
        alerts = []

        for status in statuses:
            if status.get("should_alert"):
                alerts.append(
                    {
                        "category": status["category_name"],
                        "message": f"Budget alert: {status['percentage_spent']:.1f}% of budget spent",
                        "spent": status["spent"],
                        "budget": status["budget"],
                    }
                )
            if status.get("over_budget"):
                alerts.append(
                    {
                        "category": status["category_name"],
                        "message": f"Over budget by ${abs(Decimal(status['remaining']))}",
                        "spent": status["spent"],
                        "budget": status["budget"],
                    }
                )

        return alerts

