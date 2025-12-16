# Finance Tracker API Documentation

Complete API reference for the finance tracker package.

## Package Overview

```python
import finance_tracker
```

## Models

### TransactionType

Enumeration of transaction types.

```python
from finance_tracker import TransactionType

TransactionType.DEBIT    # Money going out
TransactionType.CREDIT   # Money coming in
TransactionType.TRANSFER # Internal transfer
```

### Category

Represents a spending category.

```python
from finance_tracker import Category

category = Category(
    name="Groceries",
    parent="Food & Dining",
    description="Grocery store purchases"
)
```

**Fields**:
- `name` (str): Category name
- `parent` (str, optional): Parent category
- `description` (str, optional): Category description

### Transaction

Represents a financial transaction.

```python
from finance_tracker import Transaction, TransactionType
from datetime import date
from decimal import Decimal

transaction = Transaction(
    date=date(2024, 1, 15),
    amount=Decimal("-50.00"),
    description="Grocery Store",
    transaction_type=TransactionType.DEBIT,
    category=Category(name="Groceries")
)
```

**Fields**:
- `date` (datetime.date): Transaction date
- `amount` (Decimal): Amount (negative for debits, positive for credits)
- `description` (str): Transaction description
- `category` (Category, optional): Assigned category
- `transaction_type` (TransactionType): Type of transaction
- `account` (str, optional): Account identifier
- `reference` (str, optional): Transaction reference
- `balance` (Decimal, optional): Account balance
- `notes` (str, optional): User notes

**Properties**:
- `is_expense`: Returns True if transaction is an expense
- `is_income`: Returns True if transaction is income
- `absolute_amount`: Returns absolute value of amount

### MonthlySummary

Monthly spending summary.

```python
from finance_tracker import MonthlySummary

summary = MonthlySummary(
    year=2024,
    month=1,
    total_income=Decimal("3000.00"),
    total_expenses=Decimal("2000.00"),
    category_breakdown={"Groceries": Decimal("500.00")}
)
```

**Properties**:
- `savings_rate`: Savings rate as percentage (None if no income)

### SpendingPattern

Spending pattern for a category.

```python
from finance_tracker import SpendingPattern

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

## CSV Parsing

### CSVParser

```python
from finance_tracker import CSVParser
from pathlib import Path

parser = CSVParser(account="CHECKING-123")
transactions = parser.parse(Path("bank_statement.csv"))
```

**Methods**:
- `detect_format(file_path) -> CSVFormat`: Detect CSV format
- `parse(file_path) -> List[Transaction]`: Parse CSV file

### Convenience Function

```python
from finance_tracker import parse_csv

transactions = parse_csv(Path("bank_statement.csv"), account="CHECKING-123")
```

## Categorization

### CategoryMapper

```python
from finance_tracker.category_mapper import CategoryMapper

mapper = CategoryMapper()
category = mapper.categorize("GROCERY STORE #1234")
# Returns Category(name="Groceries", parent="Food & Dining")
```

**Methods**:
- `categorize(description) -> Optional[Category]`: Categorize a description
- `add_custom_rule(pattern, category_name, parent)`: Add custom rule
- `get_all_categories() -> Dict[str, List[str]]`: Get all categories

### TransactionCategorizer

```python
from finance_tracker import TransactionCategorizer

categorizer = TransactionCategorizer()
categorized, stats = categorizer.categorize_transactions(transactions)
```

**Methods**:
- `categorize_transaction(transaction, overwrite=False) -> Transaction`
- `categorize_transactions(transactions, overwrite=False) -> Tuple[List[Transaction], CategorizationStats]`
- `get_uncategorized_transactions(transactions) -> List[Transaction]`
- `get_transactions_by_category(transactions, category_name) -> List[Transaction]`

### Convenience Function

```python
from finance_tracker import categorize_transactions

categorized, stats = categorize_transactions(transactions)
```

## Analysis

### SpendingAnalyzer

```python
from finance_tracker import SpendingAnalyzer

analyzer = SpendingAnalyzer(transactions)
summary = analyzer.get_monthly_summary(2024, 1)
```

**Methods**:
- `get_monthly_summary(year, month) -> MonthlySummary`
- `get_all_monthly_summaries() -> List[MonthlySummary]`
- `get_category_breakdown(year=None, month=None) -> Dict[str, Decimal]`
- `get_spending_patterns(category_name=None) -> List[SpendingPattern]`
- `get_top_categories(limit=10) -> List[SpendingPattern]`
- `get_total_income(year=None, month=None) -> Decimal`
- `get_total_expenses(year=None, month=None) -> Decimal`
- `get_net_amount(year=None, month=None) -> Decimal`
- `get_average_monthly_spending(category_name=None) -> Decimal`
- `get_spending_trend(category_name, months=3) -> Optional[str]`

### Convenience Function

```python
from finance_tracker import analyze_spending

analyzer = analyze_spending(transactions)
```

## Storage

### StorageManager

```python
from finance_tracker import StorageManager
from pathlib import Path

storage = StorageManager(data_dir=Path.home() / ".finance-tracker")
```

**Methods**:
- `export_transactions_json(output_file)`: Export to JSON
- `export_transactions_csv(output_file)`: Export to CSV

### TransactionRepository

```python
from finance_tracker.storage import TransactionRepository

repo = TransactionRepository(data_dir)
repo.save(transactions)
transactions = repo.load_all()
duplicates = repo.check_duplicates(new_transactions)
```

### CategoryRepository

```python
from finance_tracker.storage import CategoryRepository

repo = CategoryRepository(data_dir)
repo.save_custom_categories(categories)
categories = repo.load_custom_categories()
```

## Workflow

### FinanceTrackerWorkflow

Main workflow orchestrator.

```python
from finance_tracker import FinanceTrackerWorkflow

workflow = FinanceTrackerWorkflow(data_dir=Path.home() / ".finance-tracker")
transactions, stats = workflow.process_csv_file(
    csv_file=Path("bank_statement.csv"),
    auto_categorize=True,
    check_duplicates=True
)
```

**Methods**:
- `process_csv_file(csv_file, auto_categorize=True, ...) -> Tuple[List[Transaction], Dict]`
- `analyze_spending(year=None, month=None) -> SpendingAnalyzer`
- `get_uncategorized_transactions() -> List[Transaction]`
- `recategorize_all(overwrite=True) -> Dict`

### Convenience Function

```python
from finance_tracker import process_csv

transactions, stats = process_csv(Path("bank_statement.csv"))
```

## Configuration

### Config

```python
from finance_tracker.config import get_config

config = get_config()
data_dir = config.get("data.directory")
log_level = config.get("logging.level")
```

**Methods**:
- `get(key, default=None)`: Get configuration value
- `set(key, value)`: Set configuration value
- `load()`: Load from file
- `save()`: Save to file

## Logging

### setup_logging

```python
from finance_tracker.logging_config import setup_logging

setup_logging(level="INFO", log_file=Path("app.log"), verbose=False)
```

## CLI

The CLI is accessed via the `finance-tracker` command:

```bash
finance-tracker import-csv file.csv
finance-tracker summary --year 2024 --month 1
finance-tracker categories
finance-tracker export output.json --format json
```

## Web App

The web app is accessed via the `finance-tracker-web` command:

```bash
finance-tracker-web
```

Or programmatically:

```python
from finance_tracker.web_app import start_web_app

start_web_app(port=8080, size=(1200, 800))
```

## Error Handling

All modules raise specific exceptions:

```python
from finance_tracker.csv_parser import (
    CSVParserError,
    UnsupportedFormatError,
    InvalidDataError
)

try:
    transactions = parser.parse(file_path)
except UnsupportedFormatError as e:
    print(f"Format not supported: {e}")
except InvalidDataError as e:
    print(f"Invalid data: {e}")
```

