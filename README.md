# Finance Tracker

A comprehensive finance tracker and organizer application that processes monthly CSV bank statement files, automatically categorizes spending, and provides detailed analysis and reporting.

## 📚 Documentation

This codebase is designed to be educational and maintainable. Comprehensive documentation is available:

- **[Learning Guide](docs/LEARNING_GUIDE.md)** - Start here! Learn how the codebase works, design patterns used, and key concepts
- **[Code Walkthrough](docs/CODE_WALKTHROUGH.md)** - Step-by-step explanation of how data flows through the system
- **[Code Organization](docs/CODE_ORGANIZATION.md)** - Understanding the module structure and organization
- **[Architecture](docs/ARCHITECTURE.md)** - System design and architecture overview
- **[API Reference](docs/API.md)** - Complete API documentation
- **[Getting Started](docs/GETTING_STARTED.md)** - User guide for getting started

All code includes detailed docstrings and inline comments explaining:
- **What** the code does
- **Why** design decisions were made
- **How** algorithms work
- **Learning points** for understanding concepts

## Features

- 📊 **Multi-format CSV Parsing**: Automatically detects and parses 3+ common bank statement formats
- 🏷️ **Automatic Categorization**: 50+ built-in rules for automatic transaction categorization
- 📈 **Spending Analysis**: Monthly summaries, category breakdowns, and trend analysis
- 💾 **Data Persistence**: JSON-based storage with duplicate detection
- 📋 **Multiple Interfaces**: Both CLI and web application interfaces
- 🔍 **Duplicate Detection**: Automatically detects and handles duplicate transactions
- 📤 **Export Functionality**: Export data to JSON or CSV formats
- 📊 **Visualizations**: Interactive charts and graphs in the web interface

## Requirements

- Python 3.9 or higher
- Microsoft Edge (for web app on macOS) or any modern browser

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd finance-tracker
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install the package and dependencies
pip install -e .

# Install development dependencies (optional, for contributing)
pip install -e ".[dev]"
```

## Quick Start

### Using the CLI

```bash
# Import a CSV file
finance-tracker import-csv sample_data/bank_statement_jan_2024.csv

# View monthly summary
finance-tracker summary --year 2024 --month 1

# View top spending categories
finance-tracker categories --limit 10

# List uncategorized transactions
finance-tracker uncategorized

# Export transactions
finance-tracker export transactions.json --format json

# View overall statistics
finance-tracker stats
```

### Using the Web Application

```bash
# Start the web app (opens in Microsoft Edge on macOS)
# The web app provides a modern UI for all features
finance-tracker-web
```

Or run directly:

```bash
python -m finance_tracker.web_app
```

The web app provides:
- 📊 **Dashboard**: Statistics, charts, and monthly summaries
- 📝 **Transactions**: Searchable, filterable transaction list
- 🏷️ **Categories**: Category breakdown and analysis
- 📤 **Import**: Drag-and-drop CSV file import

## Usage Guide

### Importing CSV Files

The application supports multiple CSV formats:

1. **Standard Format**: `Date, Description, Amount, Balance`
2. **Alternative Format**: `Transaction Date, Post Date, Description, Category, Type, Amount`
3. **Debit/Credit Format**: `Date, Description, Debit, Credit, Balance`

```bash
# Basic import
finance-tracker import-csv bank_statement.csv

# Import with account name
finance-tracker import-csv bank_statement.csv --account "CHECKING-123"

# Import without auto-categorization
finance-tracker import-csv bank_statement.csv --no-categorize

# Import and overwrite existing categories
finance-tracker import-csv bank_statement.csv --overwrite
```

### Viewing Summaries

```bash
# View specific month
finance-tracker summary --year 2024 --month 1

# View all monthly summaries
finance-tracker summary
```

### Managing Categories

```bash
# View top categories
finance-tracker categories --limit 10

# Recategorize all transactions
finance-tracker recategorize --overwrite

# View uncategorized transactions
finance-tracker uncategorized
```

### Exporting Data

```bash
# Export to JSON
finance-tracker export transactions.json --format json

# Export to CSV
finance-tracker export transactions.csv --format csv
```

## Programmatic Usage

You can also use the finance tracker as a Python library:

```python
from finance_tracker import FinanceTrackerWorkflow
from pathlib import Path

# Create workflow instance
workflow = FinanceTrackerWorkflow()

# Process a CSV file
transactions, stats = workflow.process_csv_file(
    Path("bank_statement.csv"),
    auto_categorize=True,
    check_duplicates=True
)

print(f"Imported {stats['new_transactions']} transactions")
print(f"Categorized: {stats.get('categorized', 0)}")

# Analyze spending
analyzer = workflow.analyze_spending()
summary = analyzer.get_monthly_summary(2024, 1)
print(f"Total expenses: ${summary.total_expenses}")
```

See [API Documentation](docs/API.md) for complete API reference.

## Configuration

Configuration is stored in `~/.finance-tracker/config.yaml` and is automatically created on first run.

You can customize:
- Data directory location
- Logging level and file location
- Auto-categorization settings
- Duplicate detection settings

## Project Structure

```
finance-tracker/
├── finance_tracker/      # Main package
│   ├── models.py         # Data models
│   ├── csv_parser.py     # CSV parsing
│   ├── category_mapper.py # Category rules
│   ├── categorizer.py    # Categorization engine
│   ├── analyzer.py       # Spending analysis
│   ├── storage.py        # Data persistence
│   ├── workflow.py       # End-to-end workflows
│   ├── cli.py            # Command-line interface
│   └── web_app.py        # Web application
├── tests/                # Test suite
├── sample_data/          # Sample CSV files
├── docs/                 # Documentation
│   ├── ARCHITECTURE.md   # System architecture
│   ├── API.md            # API reference
│   └── models.md         # Model documentation
├── web/                  # Web app frontend
│   ├── index.html
│   ├── style.css
│   └── main.js
└── README.md
```

## Documentation

- [Architecture Documentation](docs/ARCHITECTURE.md) - System design and architecture
- [API Reference](docs/API.md) - Complete API documentation
- [Data Models](docs/models.md) - Model documentation
- [Contributing Guide](CONTRIBUTING.md) - How to contribute

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=finance_tracker --cov-report=html

# Run specific test file
pytest tests/test_models.py -v
```

### Code Quality

```bash
# Format code
black finance_tracker tests

# Lint code
ruff check finance_tracker tests

# Type checking
mypy finance_tracker
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

## Supported CSV Formats

The application automatically detects and supports:

1. **Standard Format** (most common):
   ```csv
   Date,Description,Amount,Balance
   2024-01-15,Grocery Store,-50.00,1000.00
   ```

2. **Alternative Format** (with categories):
   ```csv
   Transaction Date,Post Date,Description,Category,Type,Amount
   2024-01-15,2024-01-15,Grocery Store,Food,debit,50.00
   ```

3. **Debit/Credit Format**:
   ```csv
   Date,Description,Debit,Credit,Balance
   2024-01-15,Grocery Store,50.00,,950.00
   ```

## Data Storage

All data is stored locally in `~/.finance-tracker/`:
- `transactions.json`: All transactions
- `categories.json`: Custom categories
- `config.yaml`: Application configuration
- `exports/`: Exported data files

## Troubleshooting

### Port Already in Use

If port 8080 is already in use, the web app will automatically try the next available port.

### CSV Format Not Recognized

If your CSV format isn't recognized, check:
1. The file has headers in the first row
2. Headers match one of the supported formats
3. File encoding is UTF-8

You can also manually specify the format or add support for new formats (see CONTRIBUTING.md).

### Edge Browser Not Found

On macOS, the web app looks for Edge at:
`/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge`

If Edge is installed elsewhere, you can modify the path in `web_app.py`.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see LICENSE file for details

## Support

- Check the [documentation](docs/) for detailed information
- Open an issue on GitHub for bugs or feature requests
- See [FUTURE_WORK.md](FUTURE_WORK.md) for planned features
