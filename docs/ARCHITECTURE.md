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
- `Transaction`: Core transaction model with validation
- `MonthlySummary`: Aggregated monthly statistics
- `SpendingPattern`: Category-level spending analysis

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

### Storage (`storage.py`)

**Purpose**: Persist transactions and categories to disk.

**Key Classes**:
- `TransactionRepository`: Transaction persistence
- `CategoryRepository`: Category persistence
- `StorageManager`: Unified storage operations

**Features**:
- JSON-based storage (easily migratable to SQLite)
- Automatic duplicate detection
- Transaction fingerprinting for uniqueness
- Import/export functionality (JSON and CSV)
- Data directory management

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

### Web App (`web_app.py`)

**Purpose**: Web-based interface using Eel framework.

**Features**:
- Desktop app window (using Microsoft Edge on macOS)
- Dashboard with charts and statistics
- Transaction list with search/filter
- Category analysis
- CSV import with drag-and-drop
- Real-time data updates

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
  └─► Top Categories
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
- **Eel**: Web app framework (desktop app)
- **PyYAML**: Configuration file parsing

### Development Tools
- **pytest**: Testing framework
- **black**: Code formatting
- **ruff**: Linting
- **mypy**: Type checking

## File Organization

```
finance_tracker/
├── __init__.py          # Package initialization and exports
├── models.py            # Data models (Transaction, Category, etc.)
├── csv_parser.py        # CSV parsing and format detection
├── category_mapper.py   # Category mapping rules
├── categorizer.py       # Transaction categorization
├── analyzer.py          # Spending analysis
├── storage.py           # Data persistence
├── workflow.py          # End-to-end workflows
├── config.py            # Configuration management
├── logging_config.py    # Logging setup
├── cli.py               # Command-line interface
└── web_app.py           # Web application
```

## Error Handling

The application uses a hierarchical exception structure:

- `CSVParserError`: Base exception for CSV parsing
  - `UnsupportedFormatError`: Unsupported CSV format
  - `InvalidDataError`: Invalid or malformed data

All exceptions include descriptive error messages and context.

## Data Storage

### Current Implementation
- JSON-based file storage
- Files stored in `~/.finance-tracker/`
- `transactions.json`: All transactions
- `categories.json`: Custom categories
- `config.yaml`: Application configuration

### Future Migration Path
The repository pattern allows easy migration to SQLite or PostgreSQL without changing business logic.

## Performance Considerations

- Transactions are loaded into memory for analysis (suitable for typical personal finance use)
- Large datasets (10,000+ transactions) may benefit from database storage
- CSV parsing is streaming-based (doesn't load entire file into memory)
- Category matching uses compiled regex patterns for efficiency

## Security Considerations

- All data stored locally (no cloud sync)
- No network communication (except Eel's local web server)
- File-based storage with standard file permissions
- No encryption (consider for sensitive financial data in future)

## Testing Strategy

- Unit tests for each module
- Integration tests for workflows
- Sample data for testing different CSV formats
- Test coverage tracking with pytest-cov

## Extension Points

The architecture supports easy extension:

1. **New CSV Formats**: Add parser method to `CSVParser`
2. **New Categories**: Add rules to `CategoryMapper`
3. **New Analysis**: Add methods to `SpendingAnalyzer`
4. **New Storage**: Implement repository interface
5. **New UI**: Add new Eel-exposed functions in `web_app.py`

