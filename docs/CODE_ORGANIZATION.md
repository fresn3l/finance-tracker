# Code Organization Guide

This document explains how the finance tracker codebase is organized and why it's structured this way.

## Directory Structure

```
finance_tracker/
├── __init__.py              # Package initialization and public API
├── models.py                 # Core domain models (Transaction, Category, etc.)
├── csv_parser.py            # CSV file parsing and format detection
├── category_mapper.py       # Category mapping rules and pattern matching
├── categorizer.py           # Transaction categorization engine
├── analyzer.py              # Spending analysis and reporting
├── storage.py               # Data persistence (JSON-based)
├── workflow.py              # End-to-end workflow orchestration
├── transaction_editor.py    # Transaction editing operations
├── budget_tracker.py        # Budget tracking and management
├── recurring_detector.py    # Recurring transaction detection
├── search_filter.py         # Advanced search and filtering
├── category_rules_manager.py # Category rules management
├── config.py                # Configuration management
├── logging_config.py        # Logging setup
├── cli.py                   # Command-line interface
└── web_app.py               # Web application (Eel-based)
```

## Module Responsibilities

### Core Domain (`models.py`)

**Purpose**: Define the fundamental data structures

**What it contains**:
- Transaction, Category, Budget models
- Enums (TransactionType)
- Validation logic
- Computed properties

**Why separate**: Models are the foundation - everything else depends on them

**Dependencies**: None (pure data structures)

### Data Input (`csv_parser.py`)

**Purpose**: Parse bank statement CSV files

**What it contains**:
- Format detection
- Multiple parsing strategies
- Date/amount parsing utilities

**Why separate**: Input handling is a distinct concern

**Dependencies**: `models.py`

### Categorization (`category_mapper.py`, `categorizer.py`)

**Purpose**: Automatically categorize transactions

**What it contains**:
- Category mapping rules
- Pattern matching logic
- Categorization statistics

**Why separate**: Categorization is a complex, independent feature

**Dependencies**: `models.py`

### Analysis (`analyzer.py`)

**Purpose**: Analyze spending patterns

**What it contains**:
- Monthly summaries
- Category breakdowns
- Spending patterns
- Trend analysis

**Why separate**: Analysis is read-only, doesn't modify data

**Dependencies**: `models.py`

### Storage (`storage.py`)

**Purpose**: Persist data to disk

**What it contains**:
- Transaction repository
- Category repository
- Duplicate detection
- Import/export

**Why separate**: Storage is a cross-cutting concern

**Dependencies**: `models.py`

### Workflow (`workflow.py`)

**Purpose**: Orchestrate end-to-end operations

**What it contains**:
- CSV processing workflow
- Analysis workflows
- High-level operations

**Why separate**: Coordinates other modules, provides simple API

**Dependencies**: All other modules

### User Interfaces (`cli.py`, `web_app.py`)

**Purpose**: Provide user-facing interfaces

**What it contains**:
- CLI commands
- Web app endpoints
- User interaction logic

**Why separate**: UI is separate from business logic

**Dependencies**: `workflow.py`, other modules

## Design Principles

### 1. Single Responsibility

Each module has one clear purpose:
- `csv_parser.py` → Parse CSV files
- `analyzer.py` → Analyze data
- `storage.py` → Store data

### 2. Dependency Direction

Dependencies flow in one direction:
```
UI → Workflow → Core Logic → Models
```

Models have no dependencies. Core logic depends only on models. UI depends on workflow.

### 3. Separation of Concerns

- **Data Models**: What data looks like
- **Business Logic**: What operations do
- **Storage**: How data is persisted
- **UI**: How users interact

### 4. Testability

Each module can be tested independently:
- Mock dependencies
- Test in isolation
- Integration tests for workflows

## Code Patterns

### Repository Pattern

**Where**: `storage.py`

**Why**: Abstracts data access, makes it easy to change storage backend

**Example**:
```python
repo = TransactionRepository(data_dir)
transactions = repo.load_all()  # Don't care if it's JSON or database
```

### Strategy Pattern

**Where**: `csv_parser.py`

**Why**: Different parsing strategies for different formats

**Example**:
```python
format = parser.detect_format(file)
if format == CSVFormat.STANDARD:
    transactions = parser._parse_standard(file)
elif format == CSVFormat.ALTERNATIVE:
    transactions = parser._parse_alternative(file)
```

### Workflow Pattern

**Where**: `workflow.py`

**Why**: Coordinates multiple operations into a single flow

**Example**:
```python
workflow.process_csv_file(file)  # Does: parse → categorize → store
```

### Service Layer

**Where**: `transaction_editor.py`, `budget_tracker.py`

**Why**: Business logic separate from storage

**Example**:
```python
editor = TransactionEditor(repo)
editor.split_transaction(id, splits)  # Business logic, not storage
```

## File Organization Guidelines

### Module Size

- **Small modules** (< 200 lines): Single responsibility, easy to understand
- **Medium modules** (200-500 lines): Related functionality grouped together
- **Large modules** (> 500 lines): Consider splitting if it has multiple responsibilities

### Import Organization

1. Standard library imports
2. Third-party imports
3. Local imports

Example:
```python
# Standard library
from datetime import date
from decimal import Decimal

# Third-party
from pydantic import BaseModel

# Local
from finance_tracker.models import Transaction
```

### Function Organization

Within a module:
1. Constants
2. Classes
3. Functions
4. Module-level code

## Extension Points

### Adding a New CSV Format

1. Add format to `CSVFormat` enum
2. Add detection logic in `detect_format()`
3. Add parsing method `_parse_new_format()`
4. Add case in `parse()` method

### Adding a New Category Rule

1. Add rule in `CategoryMapper._load_default_rules()`
2. Or use `CategoryRulesManager` to add via UI

### Adding a New Analysis

1. Add method to `SpendingAnalyzer`
2. Filter transactions as needed
3. Perform calculations
4. Return results

### Adding a New Storage Backend

1. Implement repository interface
2. Update `StorageManager` to use new repository
3. Business logic doesn't change!

## Best Practices

### 1. Keep Modules Focused

Each module should have a single, clear purpose. If a module does too many things, split it.

### 2. Minimize Dependencies

Only import what you need. Avoid circular dependencies.

### 3. Use Type Hints

Type hints make code self-documenting and catch errors early.

### 4. Document Complex Logic

Add comments explaining *why*, not just *what*.

### 5. Error Handling

Handle errors at the appropriate level:
- Low-level: Catch and re-raise with context
- High-level: Handle gracefully, provide user feedback

## Testing Organization

Tests mirror the module structure:

```
tests/
├── test_models.py
├── test_csv_parser.py
├── test_categorizer.py
├── test_analyzer.py
├── test_storage.py
└── test_workflow.py
```

Each test file tests one module, keeping tests organized and maintainable.

## Future Modularization

As the codebase grows, consider organizing into subpackages:

```
finance_tracker/
├── core/           # Models, enums
├── input/          # CSV parsing
├── categorization/ # Category mapping, rules
├── analysis/       # Spending analysis
├── storage/        # Data persistence
├── workflows/      # End-to-end workflows
├── ui/             # CLI, web app
└── utils/          # Config, logging
```

This would provide even better organization for a larger codebase.

