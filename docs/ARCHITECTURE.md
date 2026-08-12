# Finance Tracker Architecture

This document provides a comprehensive overview of the finance tracker application architecture, design decisions, and how the components interact.

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Module Structure](#module-structure)
4. [Data Flow](#data-flow)
5. [Design Patterns](#design-patterns)
6. [Technology Stack](#technology-stack)

## Overview

The Finance Tracker is a Python application that processes bank statement CSV files, automatically categorizes transactions, and provides analysis and reporting capabilities. The application follows a modular architecture with clear separation of concerns.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interfaces                         │
├──────────────────────┬───────────────────────────────────────┤
│   CLI (Click)       │      Web App (Eel)                    │
└──────────┬──────────┴──────────────┬──────────────────────┘
           │                          │
           └──────────┬───────────────┘
                      │
        ┌─────────────▼──────────────┐
        │   Workflow Layer            │
        │  (FinanceTrackerWorkflow)   │
        └─────────────┬───────────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
┌───────▼────────┐         ┌─────────▼──────────┐
│  CSV Parser    │         │   Categorizer      │
│  (CSVParser)   │─────────▶│ (TransactionCat.)  │
└───────┬────────┘         └─────────┬──────────┘
        │                            │
        │                    ┌──────▼──────────┐
        │                    │ Category Mapper  │
        │                    │ (CategoryMapper) │
        │                    └──────────────────┘
        │
┌───────▼────────┐
│   Analyzer     │
│ (SpendingAn.)  │
└───────┬────────┘
        │
┌───────▼────────┐
│   Storage      │
│ (StorageMgr)   │
└────────────────┘
```

## Module Structure

### Core Models (`models.py`)

**Purpose**: Define the data structures used throughout the application.

**Key Classes**:
- `TransactionType`: Enum for transaction types (DEBIT, CREDIT, TRANSFER)
- `Category`: Represents a spending category with hierarchical support
- `Transaction`: Core transaction model with validation (includes `id`, notes, recurring/split fields)
- `MonthlySummary`: Aggregated monthly statistics
- `SpendingPattern`: Category-level spending analysis
- `Budget` / `BudgetTemplate`: Per-category monthly budgets
- `RecurringTransaction`: Detected subscription/bill pattern
- `SplitTransaction`: One transaction split across categories

**Design Decisions**:
- Uses Pydantic v2 for validation and serialization
- Immutable categories to prevent accidental modification
- Decimal for all monetary values to avoid floating-point errors
- Type hints throughout for better IDE support

### CSV Parser (`csv_parser.py`)

**Purpose**: Parse bank statement CSV files into Transaction objects.

**Key Classes**:
- `CSVParser`: Main parser class with format detection
- `CSVFormat`: Enum of supported formats
- Custom exceptions for error handling

**Supported Formats**:
1. **Standard**: `Date, Description, Amount, Balance`
2. **Alternative**: `Transaction Date, Post Date, Description, Category, Type, Amount`
3. **Debit/Credit**: `Date, Description, Debit, Credit, Balance`

**Features**:
- Automatic format detection
- Flexible date parsing (ISO, US, European formats)
- Amount parsing with currency symbols and commas
- Row-level error reporting

### Category Mapper (`category_mapper.py`)

**Purpose**: Map transaction descriptions to categories using pattern matching.

**Key Classes**:
- `CategoryMapper`: Main mapper with regex-based rules
- `CategoryRule`: Individual categorization rule

**Features**:
- 50+ default categorization rules
- Regex pattern matching (case-insensitive by default)
- Hierarchical category support
- Custom rule support
- Categories organized by parent (Food & Dining, Transportation, etc.)

### Categorizer (`categorizer.py`)

**Purpose**: Apply categorization to transactions and track statistics.

**Key Classes**:
- `TransactionCategorizer`: Main categorization engine
- `CategorizationStats`: Statistics about categorization results

**Features**:
- Batch and single transaction categorization
- Option to overwrite or preserve existing categories
- Statistics tracking (success rate, categorized count, etc.)
- Filtering methods (uncategorized, by category, etc.)

### Analyzer (`analyzer.py`)

**Purpose**: Analyze spending patterns and generate summaries.

**Key Classes**:
- `SpendingAnalyzer`: Main analysis engine

**Features**:
- Monthly summaries with income/expense breakdowns
- Category breakdowns (overall or by month)
- Spending patterns with statistics (avg, min, max, percentage)
- Top categories analysis
- Spending trend detection
- Average monthly spending calculations
- Month-over-month comparison (`get_month_over_month`) — income, expenses, net, and per-category $ / % deltas
- Cash flow (`get_cash_flow`) — operating income/expenses vs transfers
- Spending forecast (`forecast_next_month`) — moving average of recent months

### Storage (`storage.py`)

**Purpose**: Persist transactions and categories to disk.

**Key Classes**:
- `TransactionRepository`: Transaction persistence
- `CategoryRepository`: Category persistence
- `StorageManager`: Unified storage operations

**Features**:
- JSON-based storage with Fernet encryption at rest (`secure_store.SecureJSON`)
- Automatic duplicate detection
- Transaction fingerprinting for uniqueness
- Import/export functionality (JSON and CSV exports remain plaintext)
- Data directory mode 0700; data files mode 0600
- Plaintext files from older versions are migrated on the next load

### Workflow (`workflow.py`)

**Purpose**: Orchestrate end-to-end processing workflows.

**Key Classes**:
- `FinanceTrackerWorkflow`: Main workflow orchestrator

**Features**:
- Complete CSV processing pipeline
- Duplicate detection and handling
- Automatic categorization
- Integration of all components

### CLI (`cli.py`)

**Purpose**: Command-line interface using Click.

**Commands**:
- `import-csv`: Import and process CSV files
- `summary`: Show monthly spending summaries
- `categories`: Display top spending categories
- `uncategorized`: List uncategorized transactions
- `recategorize`: Recategorize all transactions
- `export`: Export transactions to JSON/CSV
- `stats`: Show overall statistics
- `list`: List stored transactions (includes IDs)
- `edit`: Edit a stored transaction by ID
- `delete`: Delete a stored transaction by ID
- `budget`: Manage category budgets (`set`, `list`, `status`, `alerts`, `delete`)
- `recurring`: Detect and mark recurring transactions (`detect`, `mark`)
- `report`: Write a local HTML/PDF monthly report with MoM (optional `--notify`)
- `review`: Import → uncategorized → summary/MoM/cash flow → report
- `cashflow` / `forecast`: Operating vs transfers; moving-average forecast
- `schedule`: Install/uninstall/status for the month-end launchd agent
- `account` / `goal`: Balances (including investments and debts) and targets

### Web App (`web_app.py`)

**Purpose**: Web-based interface using Eel, bound to `127.0.0.1` only.

**Features**:
- Desktop app window (Chrome/Edge `--app=` on macOS; no CDN)
- Dashboard with charts, month-over-month, cash flow, forecast, and net worth
- Transaction list with search/filter, edit, delete, split, and bulk actions
- Category analysis
- Budget management and alerts
- Recurring transaction detection
- Category rules management
- Review tab: load a month, list uncategorized, generate HTML/PDF
- CSV import with drag-and-drop
- Real-time data updates

`get_transactions` returns the same dictionary shape as other transaction endpoints, including `id`, `notes`, and `is_recurring`, so the table's edit/delete actions work.

### Transaction Editor (`transaction_editor.py`)

**Purpose**: Mutate stored transactions.

**Features**:
- Edit description, amount, date, category, and notes
- Delete one or many transactions
- Split a transaction across categories
- Merge transactions
- Bulk category/notes updates

### Search & Filter (`search_filter.py`)

**Purpose**: Query stored transactions.

**Features**:
- Text search over description and notes
- Filters for category, account, date range, amount range, type, and recurring flag

### Budget Tracker (`budget_tracker.py`)

**Purpose**: Set monthly category budgets and compare against spending.

**Features**:
- Persist budgets and templates as JSON
- Spending vs. budget status
- Alert when a threshold is reached or the budget is exceeded

### Recurring Detector (`recurring_detector.py`)

**Purpose**: Find subscription/bill patterns and mark matching transactions.

**Features**:
- Group by normalized description
- Classify weekly / monthly / yearly frequency
- Confidence score and next-expected date
- `mark_recurring` uses `model_copy(update=...)` so existing fields are preserved

### Reports (`report.py`)

Self-contained HTML and fpdf2 PDF of a month plus MoM and cash flow. No external assets.

### Notifications (`notify.py`)

macOS Notification Center via `osascript`. Never sends email.

### Scheduler (`scheduler.py`)

Writes `~/Library/LaunchAgents/com.financetracker.monthly-report.plist` to run `report --previous-month --notify --pdf` at 09:00 on the 1st.

### Secure store (`secure_store.py`)

Fernet (`FTENC1` magic) encryption, key in `.key` (0600) or macOS Keychain, directory 0700.

### Accounts (`accounts.py`)

Checking, savings, credit cards, loans, investments, cash. Net worth = assets − liabilities. Goals with progress percent.

### Category Rules Manager (`category_rules_manager.py`)

**Purpose**: Add, test, import, and export custom categorization rules.

### Configuration (`config.py`)

**Purpose**: Manage application configuration.

**Features**:
- YAML-based configuration files
- Default configuration generation
- Dot notation for nested values
- Configurable data directory, logging, categorization settings

### Logging (`logging_config.py`)

**Purpose**: Centralized logging configuration.

**Features**:
- Configurable log levels
- Console and file logging support
- Verbose mode for debugging

## Data Flow

### CSV Import Flow

```
CSV File
  │
  ▼
CSV Parser (detect format, parse rows)
  │
  ▼
Transaction Objects (uncategorized)
  │
  ▼
Duplicate Detection (check against stored)
  │
  ▼
Categorizer (apply category rules)
  │
  ▼
Transaction Objects (categorized)
  │
  ▼
Storage (save to JSON)
  │
  ▼
Analyzer (generate summaries/patterns)
  │
  ▼
Reports/Visualizations
```

### Analysis Flow

```
Stored Transactions
  │
  ▼
SpendingAnalyzer
  │
  ├─► Monthly Summaries
  ├─► Category Breakdowns
  ├─► Spending Patterns
  ├─► Month-over-month deltas
  ├─► Cash flow (operating vs transfers)
  └─► Top Categories / forecasts
```

## Design Patterns

### Repository Pattern
- `TransactionRepository` and `CategoryRepository` abstract data access
- Allows easy migration from JSON to database storage

### Strategy Pattern
- Different CSV format parsers (standard, alternative, debit/credit)
- Format detection selects appropriate parsing strategy

### Factory Pattern
- `get_default_mapper()` creates CategoryMapper with default rules
- `analyze_spending()` creates SpendingAnalyzer instances

### Facade Pattern
- `FinanceTrackerWorkflow` provides simple interface to complex operations
- `StorageManager` unifies storage operations

## Technology Stack

### Core Dependencies
- **Pydantic v2**: Data validation and serialization
- **Pandas/NumPy**: Data processing (for future enhancements)
- **Click**: CLI framework
- **cryptography**: Fernet encryption at rest
- **fpdf2**: Local PDF reports
- **Eel**: Web app framework (desktop window; host `127.0.0.1`)
- **PyYAML**: Configuration file parsing

### Development Tools
- **pytest**: Testing framework
- **black**: Code formatting
- **ruff**: Linting
- **mypy**: Type checking

## File Organization

```
finance_tracker/
├── __init__.py                 # Package initialization and exports
├── models.py                   # Data models (Transaction, Category, Budget, etc.)
├── csv_parser.py               # CSV parsing and format detection
├── category_mapper.py          # Category mapping rules
├── categorizer.py              # Transaction categorization
├── analyzer.py                 # Spending analysis (MoM, cash flow, forecast)
├── report.py                   # HTML/PDF monthly reports
├── secure_store.py             # Encrypted JSON + file permissions
├── scheduler.py                # launchd month-end agent
├── notify.py                   # macOS notifications (no email)
├── accounts.py                 # Accounts, net worth, goals
├── storage.py                  # Data persistence
├── workflow.py                 # End-to-end workflows
├── config.py                   # Configuration management
├── logging_config.py           # Logging setup
├── cli.py                      # Command-line interface
├── web_app.py                  # Web application (localhost)
├── transaction_editor.py       # Edit / delete / split / merge
├── search_filter.py            # Advanced search
├── budget_tracker.py           # Budgets and alerts
├── recurring_detector.py       # Recurring pattern detection
└── category_rules_manager.py   # Custom category rules
```

## Error Handling

The application uses a hierarchical exception structure:

- `CSVParserError`: Base exception for CSV parsing
  - `UnsupportedFormatError`: Unsupported CSV format
  - `InvalidDataError`: Invalid or malformed data

All exceptions include descriptive error messages and context.

## Data Storage

### Current Implementation
- Encrypted JSON file storage (`FTENC1` Fernet); key in `.key` or macOS Keychain
- Files stored in `~/.finance-tracker/` (0700); data files 0600
- `transactions.json`: All transactions
- `categories.json`: Custom categories
- `budgets.json` / `budget_templates.json`: Category budgets
- `accounts.json` / `goals.json`: Balances and targets
- `custom_category_rules.json`: User-defined categorization rules
- `config.yaml`: Application configuration (0600, not encrypted)
- `reports/`: Generated HTML/PDF

### Future Migration Path
The repository pattern allows easy migration to SQLCipher without changing business logic.

## Performance Considerations

- Transactions are loaded into memory for analysis (suitable for typical personal finance use)
- Large datasets (10,000+ transactions) may benefit from database storage
- CSV parsing is streaming-based (doesn't load entire file into memory)
- Category matching uses compiled regex patterns for efficiency

## Security Considerations

- All data stored locally (no cloud sync)
- Eel listens on `127.0.0.1` only
- Chart.js is vendored; the UI loads no third-party script URLs
- JSON data encrypted at rest; directory 0700 / files 0600
- Monthly report delivery is a local macOS notification (no email unless you add it later)

## Testing Strategy

- Unit tests for each module, including editor, budgets, recurring detection, CLI, and web transaction payloads
- Integration tests for workflows
- Sample data for testing different CSV formats
- Test coverage tracking with pytest-cov
- GitHub Actions CI (lint + pytest on Python 3.9–3.12)

## Extension Points

The architecture supports easy extension:

1. **New CSV Formats**: Add parser method to `CSVParser`
2. **New Categories**: Add rules to `CategoryMapper`
3. **New Analysis**: Add methods to `SpendingAnalyzer`
4. **New Storage**: Implement repository interface
5. **New UI**: Add new Eel-exposed functions in `web_app.py`

