# Data Models Documentation

This document describes the data models used in the finance tracker application.

## Overview

The application uses Pydantic models for data validation and type safety. All models are immutable where appropriate and include comprehensive validation.

## Models

### TransactionType

Enumeration of transaction types:
- `DEBIT`: Money going out (expenses)
- `CREDIT`: Money coming in (income)
- `TRANSFER`: Internal transfers between accounts

### Category

Represents a spending category with hierarchical support.

**Fields:**
- `name` (str, required): Category name (e.g., 'Groceries', 'Transportation')
- `parent` (str, optional): Parent category for hierarchical categorization
- `description` (str, optional): Optional category description

**Properties:**
- Immutable (frozen=True)

**Example:**
```python
category = Category(name="Groceries", parent="Food & Dining")
```

### Transaction

Represents a single financial transaction from a bank statement.

**Fields:**
- `date` (date, required): Transaction date
- `amount` (Decimal, required): Transaction amount (positive for credits, negative for debits)
- `description` (str, required): Transaction description/merchant name
- `category` (Category, optional): Assigned category
- `transaction_type` (TransactionType, required): Type of transaction
- `account` (str, optional): Account identifier
- `reference` (str, optional): Transaction reference number
- `balance` (Decimal, optional): Account balance after transaction
- `notes` (str, optional): User-added notes

**Properties:**
- `is_expense`: Returns True if transaction is an expense
- `is_income`: Returns True if transaction is income
- `absolute_amount`: Returns absolute value of transaction amount

**Validation:**
- Amount cannot be zero

**Example:**
```python
transaction = Transaction(
    date=date(2024, 1, 15),
    amount=Decimal("-50.00"),
    description="Grocery Store",
    transaction_type=TransactionType.DEBIT,
    category=Category(name="Groceries")
)
```

### MonthlySummary

Summary of transactions for a specific month.

**Fields:**
- `year` (int, required): Year
- `month` (int, required): Month (1-12)
- `total_income` (Decimal, default=0): Total income for the month
- `total_expenses` (Decimal, default=0): Total expenses for the month
- `net_amount` (Decimal, default=0): Net amount (income - expenses)
- `transaction_count` (int, default=0): Number of transactions
- `category_breakdown` (dict[str, Decimal], default={}): Expenses by category

**Properties:**
- `savings_rate`: Returns savings rate as percentage (None if no income)

**Validation:**
- Month must be between 1 and 12

**Example:**
```python
summary = MonthlySummary(
    year=2024,
    month=1,
    total_income=Decimal("3000.00"),
    total_expenses=Decimal("2000.00"),
    category_breakdown={"Groceries": Decimal("500.00")}
)
```

### SpendingPattern

Represents spending patterns and trends for a category.

**Fields:**
- `category` (str, required): Category name
- `total_amount` (Decimal, required): Total spending in this category
- `transaction_count` (int, required): Number of transactions
- `average_transaction` (Decimal, required): Average transaction amount
- `min_transaction` (Decimal, required): Minimum transaction amount
- `max_transaction` (Decimal, required): Maximum transaction amount
- `percentage_of_total` (float, optional): Percentage of total spending
- `trend` (str, optional): Trend direction (increasing, decreasing, stable)

**Example:**
```python
pattern = SpendingPattern(
    category="Groceries",
    total_amount=Decimal("500.00"),
    transaction_count=10,
    average_transaction=Decimal("50.00"),
    min_transaction=Decimal("20.00"),
    max_transaction=Decimal("150.00"),
    percentage_of_total=25.0
)
```

## Design Decisions

1. **Pydantic Models**: Used for automatic validation, serialization, and type safety
2. **Decimal for Money**: All monetary values use `Decimal` to avoid floating-point precision issues
3. **Immutable Categories**: Categories are frozen to prevent accidental modification
4. **Optional Fields**: Many fields are optional to handle varying CSV formats from different banks
5. **Type Safety**: Full type hints for better IDE support and static analysis

## Usage

All models can be serialized to/from JSON:

```python
# Serialize
json_str = transaction.model_dump_json()

# Deserialize
transaction = Transaction.model_validate_json(json_str)
```

