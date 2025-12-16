# Finance Tracker Learning Guide

This guide is designed to help you understand how the finance tracker codebase works, with a focus on learning software engineering principles and Python best practices.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Concepts](#core-concepts)
3. [Module-by-Module Breakdown](#module-by-module-breakdown)
4. [Design Patterns Used](#design-patterns-used)
5. [Key Algorithms Explained](#key-algorithms-explained)
6. [Common Patterns and Practices](#common-patterns-and-practices)

## Architecture Overview

The finance tracker follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────┐
│         User Interfaces             │
│  (CLI, Web App)                     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Workflow/Orchestration          │
│  (Coordinates all operations)        │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────┐         ┌──────▼────┐
│  Core  │         │  Analysis │
│ Models │         │  Engine   │
└───┬────┘         └──────┬────┘
    │                     │
┌───▼─────────────────────▼────┐
│      Storage Layer            │
│  (Persistence)                │
└───────────────────────────────┘
```

### Why This Architecture?

1. **Separation of Concerns**: Each layer has a single responsibility
2. **Testability**: Each layer can be tested independently
3. **Maintainability**: Changes in one layer don't affect others
4. **Extensibility**: Easy to add new features without breaking existing code

## Core Concepts

### 1. Domain Models (Pydantic)

**Location**: `finance_tracker/models.py`

**What it is**: Domain models represent the core business entities (Transaction, Category, Budget, etc.)

**Why Pydantic?**
- Automatic validation ensures data integrity
- Type hints provide IDE support
- Built-in serialization to JSON
- Field validation enforces business rules

**Key Learning**: Models are independent of storage or UI - they represent pure business logic.

### 2. Repository Pattern

**Location**: `finance_tracker/storage.py`

**What it is**: A repository abstracts data access, hiding the details of how data is stored.

**Why use it?**
- Easy to switch from JSON to database later
- Business logic doesn't depend on storage details
- Makes testing easier (can use in-memory storage for tests)

**Example**:
```python
# Business logic doesn't know if data is in JSON or database
repo = TransactionRepository(data_dir)
transactions = repo.load_all()  # Same interface regardless of storage
```

### 3. Strategy Pattern

**Location**: `finance_tracker/csv_parser.py`

**What it is**: Different parsing strategies for different CSV formats.

**Why use it?**
- Each format has its own parsing logic
- Easy to add new formats without changing existing code
- Format detection selects the right strategy automatically

### 4. Workflow Orchestration

**Location**: `finance_tracker/workflow.py`

**What it is**: Coordinates multiple operations into a single workflow.

**Why use it?**
- Simplifies complex operations (parse → categorize → analyze → store)
- Provides a high-level API for common tasks
- Handles error recovery and logging

## Module-by-Module Breakdown

### Models (`models.py`)

**Purpose**: Define the core data structures

**Key Concepts**:
- **Pydantic Models**: Automatic validation and serialization
- **Decimal for Money**: Prevents floating-point errors
- **Immutable Categories**: Prevents accidental changes
- **Computed Properties**: Business logic close to data

**Learning Points**:
- Why `Decimal` instead of `float`? (Precision!)
- Why immutable categories? (Data integrity!)
- How validators work (automatic validation on creation)

### CSV Parser (`csv_parser.py`)

**Purpose**: Parse bank statement CSV files

**Key Concepts**:
- **Format Detection**: Automatically identify CSV format
- **Multiple Parsers**: Different strategy for each format
- **Error Handling**: Row-level errors, continue parsing

**Learning Points**:
- How to handle multiple file formats
- Error handling strategies (fail gracefully)
- Date/amount parsing (handle various formats)

### Category Mapper (`category_mapper.py`)

**Purpose**: Map transaction descriptions to categories using patterns

**Key Concepts**:
- **Regex Patterns**: Match transaction descriptions
- **Rule-based System**: Easy to add new rules
- **Hierarchical Categories**: Parent/child relationships

**Learning Points**:
- Pattern matching with regex
- Rule-based systems
- How to make categorization extensible

### Categorizer (`categorizer.py`)

**Purpose**: Apply categorization to transactions

**Key Concepts**:
- **Batch Processing**: Process multiple transactions efficiently
- **Statistics Tracking**: Track categorization success
- **Filtering**: Find uncategorized or specific transactions

**Learning Points**:
- Batch operations
- Statistics and metrics
- Filtering and querying

### Analyzer (`analyzer.py`)

**Purpose**: Analyze spending patterns and generate insights

**Key Concepts**:
- **Aggregation**: Sum, average, min, max calculations
- **Time-based Analysis**: Monthly summaries, trends
- **Category Breakdowns**: Spending by category

**Learning Points**:
- Data aggregation techniques
- Time-series analysis
- Statistical calculations

### Storage (`storage.py`)

**Purpose**: Persist data to disk

**Key Concepts**:
- **Repository Pattern**: Abstract data access
- **JSON Storage**: Simple file-based storage
- **Duplicate Detection**: Prevent duplicate transactions
- **Serialization**: Convert models to/from JSON

**Learning Points**:
- Repository pattern implementation
- Serialization/deserialization
- Duplicate detection algorithms

### Workflow (`workflow.py`)

**Purpose**: Orchestrate end-to-end operations

**Key Concepts**:
- **Workflow Pattern**: Coordinate multiple steps
- **Error Handling**: Handle errors at workflow level
- **Logging**: Track workflow progress

**Learning Points**:
- How to coordinate complex operations
- Error handling strategies
- Logging best practices

## Design Patterns Used

### 1. Repository Pattern
**Where**: `storage.py`
**Why**: Abstracts data access, makes it easy to change storage backend

### 2. Strategy Pattern
**Where**: `csv_parser.py`
**Why**: Different parsing strategies for different formats

### 3. Factory Pattern
**Where**: `category_mapper.py` (get_default_mapper)
**Why**: Creates configured objects with sensible defaults

### 4. Facade Pattern
**Where**: `workflow.py`
**Why**: Provides simple interface to complex operations

## Key Algorithms Explained

### Duplicate Detection

**Location**: `storage.py` → `transaction_id()`

**How it works**:
1. Creates a "fingerprint" from key transaction attributes
2. Uses date, amount, description, and reference
3. Compares fingerprints to detect duplicates

**Why this approach**:
- Fast comparison (string comparison)
- Handles minor variations in description
- Uses multiple attributes for accuracy

### Recurring Transaction Detection

**Location**: `recurring_detector.py`

**How it works**:
1. Groups transactions by normalized description
2. Analyzes date intervals between occurrences
3. Calculates confidence based on:
   - Number of occurrences
   - Amount consistency
   - Date regularity

**Why this approach**:
- Pattern-based (no machine learning needed)
- Confidence scores help filter false positives
- Handles variable amounts

### Budget Tracking

**Location**: `budget_tracker.py`

**How it works**:
1. Stores budgets per category per month
2. Calculates actual spending from transactions
3. Compares spending to budget
4. Generates alerts when thresholds are reached

**Why this approach**:
- Simple and effective
- Easy to understand and maintain
- Flexible (supports templates, alerts, etc.)

## Common Patterns and Practices

### 1. Type Hints Everywhere

**Why**: 
- IDE support (autocomplete, error detection)
- Documentation (types are self-documenting)
- Catch errors before runtime

**Example**:
```python
def parse(self, file_path: Path) -> List[Transaction]:
    # Return type is clear
    # Parameter type is clear
```

### 2. Error Handling

**Pattern**: Specific exceptions for different error types

**Why**:
- Callers can handle errors appropriately
- Error messages are descriptive
- Makes debugging easier

**Example**:
```python
class CSVParserError(Exception): pass
class UnsupportedFormatError(CSVParserError): pass
class InvalidDataError(CSVParserError): pass
```

### 3. Logging

**Pattern**: Use logging module, not print statements

**Why**:
- Can control log levels
- Can log to files
- Production-ready

**Example**:
```python
logger.info(f"Parsed {len(transactions)} transactions")
logger.error(f"Error parsing CSV: {e}", exc_info=True)
```

### 4. Configuration Management

**Pattern**: YAML-based configuration with defaults

**Why**:
- User-friendly (YAML is readable)
- Flexible (can override defaults)
- Centralized (all settings in one place)

### 5. Decimal for Money

**Pattern**: Always use Decimal for monetary values

**Why**:
- Floating-point has precision issues
- Financial calculations need exact precision
- Decimal provides fixed-point arithmetic

**Example**:
```python
# BAD: Floating-point
amount = 50.00  # Might be 49.999999999

# GOOD: Decimal
amount = Decimal("50.00")  # Exact precision
```

## How to Extend the Codebase

### Adding a New CSV Format

1. Add format to `CSVFormat` enum
2. Add detection logic in `detect_format()`
3. Add parsing method `_parse_new_format()`
4. Add case in `parse()` method

### Adding a New Category Rule

1. Add rule in `CategoryMapper._load_default_rules()`
2. Use regex pattern to match descriptions
3. Specify category name and parent

### Adding a New Analysis

1. Add method to `SpendingAnalyzer`
2. Filter transactions as needed
3. Perform calculations
4. Return results

## Testing Strategy

The codebase uses pytest for testing. Key principles:

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test workflows end-to-end
3. **Test Data**: Use sample CSV files for realistic testing

## Best Practices Demonstrated

1. **Single Responsibility**: Each class/function does one thing
2. **DRY (Don't Repeat Yourself)**: Reusable functions
3. **Error Handling**: Graceful degradation
4. **Type Safety**: Type hints everywhere
5. **Documentation**: Docstrings explain what and why
6. **Logging**: Proper logging for debugging
7. **Configuration**: Externalized configuration

## Next Steps for Learning

1. **Read the code**: Start with models.py, then csv_parser.py
2. **Run the tests**: See how things are tested
3. **Add a feature**: Try adding a new category rule
4. **Modify behavior**: Change how categorization works
5. **Read the docs**: Check ARCHITECTURE.md for more details

## Questions to Consider

As you read the code, think about:

1. Why was this design choice made?
2. How would I extend this?
3. What would break if I changed X?
4. How is error handling done?
5. What patterns are being used?

This will help you understand not just what the code does, but why it's structured this way.

