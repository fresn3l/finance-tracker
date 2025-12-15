# CSV Parser Documentation

This document describes the CSV parser module for processing bank statement files.

## Overview

The CSV parser automatically detects and parses multiple bank statement CSV formats, converting them into `Transaction` objects for use throughout the application.

## Supported Formats

### 1. Standard Format
**Headers:** `Date, Description, Amount, Balance`

**Example:**
```csv
Date,Description,Amount,Balance
2024-01-02,Salary Deposit,3000.00,5000.00
2024-01-03,GROCERY STORE #1234,-45.67,4954.33
```

**Characteristics:**
- Positive amounts = credits (income)
- Negative amounts = debits (expenses)
- Balance column is optional

### 2. Alternative Format
**Headers:** `Transaction Date, Post Date, Description, Category, Type, Amount`

**Example:**
```csv
Transaction Date,Post Date,Description,Category,Type,Amount
2024-01-15,2024-01-15,GROCERY STORE WHOLE FOODS,Food,debit,125.50
```

**Characteristics:**
- Includes pre-categorized transactions
- Explicit transaction type (debit/credit/transfer)
- Uses Transaction Date (falls back to Post Date)

### 3. Debit/Credit Format
**Headers:** `Date, Description, Debit, Credit, Balance`

**Example:**
```csv
Date,Description,Debit,Credit,Balance
2024-01-10,Salary Payment,,2000.00,2000.00
2024-01-11,Grocery Store Purchase,85.50,,1914.50
```

**Characteristics:**
- Separate columns for debits and credits
- Empty values in opposite column
- Common format for many bank exports

## Usage

### Basic Usage

```python
from pathlib import Path
from finance_tracker.csv_parser import parse_csv

# Parse a CSV file
transactions = parse_csv(Path("bank_statement.csv"))

for transaction in transactions:
    print(f"{transaction.date}: {transaction.description} - ${transaction.amount}")
```

### With Account Identifier

```python
from finance_tracker.csv_parser import CSVParser

parser = CSVParser(account="CHECKING-123")
transactions = parser.parse(Path("bank_statement.csv"))

# All transactions will have account="CHECKING-123"
```

### Format Detection

```python
from finance_tracker.csv_parser import CSVParser, CSVFormat

parser = CSVParser()
format_type = parser.detect_format(Path("bank_statement.csv"))

if format_type == CSVFormat.STANDARD:
    print("Standard format detected")
elif format_type == CSVFormat.ALTERNATIVE:
    print("Alternative format detected")
elif format_type == CSVFormat.DEBIT_CREDIT:
    print("Debit/Credit format detected")
```

## Features

### Automatic Format Detection
The parser automatically detects the CSV format by examining the headers. No manual configuration needed.

### Flexible Date Parsing
Supports multiple date formats:
- ISO format: `YYYY-MM-DD` (e.g., `2024-01-15`)
- US format: `MM/DD/YYYY` (e.g., `01/15/2024`)
- European format: `DD/MM/YYYY` (e.g., `15/01/2024`)

### Flexible Amount Parsing
Handles various amount formats:
- With commas: `1,234.56`
- With dollar signs: `$123.45`
- Negative amounts: `-50.00`
- Positive amounts: `100.00`

### Data Validation
- Validates all required fields are present
- Skips empty rows
- Skips zero-amount transactions
- Raises descriptive errors for invalid data

### Error Handling
The parser provides specific exception types:

- `CSVParserError`: Base exception for all parser errors
- `UnsupportedFormatError`: Raised when CSV format is not supported
- `InvalidDataError`: Raised when CSV data is invalid or malformed

## API Reference

### `CSVParser`

Main parser class for CSV files.

#### Methods

**`__init__(account: Optional[str] = None)`**
- Initialize parser with optional account identifier

**`detect_format(file_path: Path) -> CSVFormat`**
- Detect the format of a CSV file
- Returns: `CSVFormat` enum value

**`parse(file_path: Path) -> List[Transaction]`**
- Parse a CSV file and return list of transactions
- Returns: List of `Transaction` objects
- Raises: `UnsupportedFormatError`, `InvalidDataError`, `CSVParserError`

### `parse_csv(file_path: Path, account: Optional[str] = None) -> List[Transaction]`

Convenience function to parse a CSV file.

**Parameters:**
- `file_path`: Path to CSV file
- `account`: Optional account identifier

**Returns:**
- List of `Transaction` objects

## Error Handling Examples

```python
from finance_tracker.csv_parser import (
    CSVParser,
    UnsupportedFormatError,
    InvalidDataError,
    CSVParserError
)

parser = CSVParser()

try:
    transactions = parser.parse(Path("bank_statement.csv"))
except UnsupportedFormatError as e:
    print(f"Format not supported: {e}")
except InvalidDataError as e:
    print(f"Invalid data: {e}")
except CSVParserError as e:
    print(f"Parser error: {e}")
```

## Implementation Details

### Format Detection Logic

1. Checks for "Transaction Date" and "Type" headers → Alternative format
2. Checks for "Debit" and "Credit" headers → Debit/Credit format
3. Checks for "Date", "Amount", and "Description" headers → Standard format
4. Otherwise → Unknown format

### Transaction Type Inference

- **Standard Format**: Inferred from amount sign (positive = credit, negative = debit)
- **Alternative Format**: Uses explicit "Type" column if available, otherwise infers from amount
- **Debit/Credit Format**: Uses explicit Debit/Credit columns

### Category Handling

- Categories are only parsed from Alternative format (if "Category" column exists)
- Categories are created as `Category` objects with the name from CSV
- Other formats will have `category=None` (can be assigned later)

## Testing

Comprehensive test suite covers:
- Format detection for all supported formats
- Parsing all three formats
- Error handling (invalid dates, amounts, formats)
- Edge cases (empty rows, zero amounts, missing fields)
- Date and amount parsing variations

Run tests with:
```bash
pytest tests/test_csv_parser.py -v
```

