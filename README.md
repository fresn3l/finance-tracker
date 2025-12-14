# Finance Tracker

A finance tracker and organizer application that processes monthly CSV bank statement files and categorizes spending by type.

## Features

- 📊 Parse and process CSV bank statement files
- 🏷️ Automatic transaction categorization
- 📈 Spending analysis and visualization
- 💾 Data storage and management
- 📋 Monthly summaries and reports

## Requirements

- Python 3.9 or higher

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd finance-tracker
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
pip install -e ".[dev]"  # For development dependencies
```

## Usage

(To be implemented)

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
ruff check .
```

### Type Checking
```bash
mypy finance_tracker
```

## Project Structure

```
finance-tracker/
├── finance_tracker/      # Main package
├── tests/                # Test files
├── sample_data/          # Sample CSV files for testing
├── docs/                 # Documentation
├── pyproject.toml        # Project configuration
└── README.md
```

## License

MIT
