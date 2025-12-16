# Getting Started with Finance Tracker

This guide will help you get started with the Finance Tracker application.

## Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd finance-tracker
```

### Step 2: Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows
```

### Step 3: Install Dependencies

```bash
# Install the package
pip install -e .
```

## Your First Import

### Using Sample Data

The repository includes sample CSV files for testing:

```bash
# Import a sample CSV file
finance-tracker import-csv sample_data/bank_statement_jan_2024.csv
```

You should see output like:
```
✓ Imported 13 transactions
  Categorized: 12/13
  Categorization rate: 92.3%
```

### Using Your Own Data

1. Export your bank statement as CSV
2. Save it to a location you can access
3. Import it:

```bash
finance-tracker import-csv /path/to/your/statement.csv
```

## Viewing Your Data

### Dashboard Overview

```bash
# View overall statistics
finance-tracker stats
```

Output:
```
Overall Statistics
==================================================
Total Income:   $6,000.00
Total Expenses: $2,500.00
Net Amount:    $3,500.00
Savings Rate:  58.3%
```

### Monthly Summaries

```bash
# View all monthly summaries
finance-tracker summary

# View specific month
finance-tracker summary --year 2024 --month 1
```

### Category Analysis

```bash
# View top spending categories
finance-tracker categories --limit 10
```

### Finding Uncategorized Transactions

```bash
# List transactions that need categorization
finance-tracker uncategorized
```

## Using the Web Interface

### Starting the Web App

```bash
finance-tracker-web
```

The web app will:
1. Start a local web server
2. Open Microsoft Edge (on macOS) with the application
3. Display a dashboard with your data

### Web App Features

1. **Dashboard Tab**: Overview with charts and statistics
2. **Transactions Tab**: Browse and search all transactions
3. **Categories Tab**: View category breakdowns and patterns
4. **Import Tab**: Upload new CSV files

## Common Workflows

### Workflow 1: Monthly Review

```bash
# 1. Import monthly statement
finance-tracker import-csv january_2024.csv

# 2. View summary
finance-tracker summary --year 2024 --month 1

# 3. Check top categories
finance-tracker categories

# 4. Review uncategorized
finance-tracker uncategorized
```

### Workflow 2: Year-End Analysis

```bash
# 1. View all monthly summaries
finance-tracker summary

# 2. Export all data for external analysis
finance-tracker export year_end_2024.json --format json

# 3. View overall statistics
finance-tracker stats
```

### Workflow 3: Recategorizing Transactions

If you want to recategorize all transactions (e.g., after adding new rules):

```bash
# Recategorize all transactions
finance-tracker recategorize --overwrite

# Check results
finance-tracker uncategorized
```

## Understanding Categories

The application automatically categorizes transactions using pattern matching. Common categories include:

- **Food & Dining**: Groceries, Restaurants, Coffee Shops, Fast Food
- **Transportation**: Gas & Fuel, Rideshare, Parking, Public Transit
- **Shopping**: General Shopping, Clothing, Pharmacy
- **Bills & Utilities**: Electric, Water, Internet, Phone, Cable/TV
- **Entertainment**: Streaming Services, Movies, Events, Gaming
- **Health & Fitness**: Medical, Dental, Fitness, Pharmacy
- **Income**: Salary, Other Income, Refunds

## Data Location

All your data is stored in:
```
~/.finance-tracker/
├── transactions.json    # All your transactions
├── categories.json      # Custom categories
└── config.yaml          # Application settings
```

## Tips and Best Practices

1. **Regular Imports**: Import statements monthly to keep data current
2. **Review Uncategorized**: Periodically check uncategorized transactions
3. **Export Backups**: Export your data regularly as backup
4. **Account Names**: Use `--account` flag to track multiple accounts
5. **Duplicate Detection**: The app automatically skips duplicates

## Troubleshooting

### CSV Not Parsing Correctly

- Check that your CSV has headers in the first row
- Verify the format matches one of the supported formats
- Check file encoding (should be UTF-8)

### Transactions Not Categorizing

- Check `finance-tracker uncategorized` to see which transactions
- Some transactions may need manual categorization
- You can add custom rules (see CONTRIBUTING.md)

### Web App Won't Start

- Check that port 8080 (or next available) is free
- Verify Microsoft Edge is installed (on macOS)
- Check logs for error messages

## Next Steps

- Read the [Architecture Documentation](ARCHITECTURE.md) to understand the system
- Check the [API Documentation](API.md) for programmatic usage
- See [FUTURE_WORK.md](../FUTURE_WORK.md) for planned features
- Contribute! See [CONTRIBUTING.md](../CONTRIBUTING.md)

## Getting Help

- Check the documentation in `docs/`
- Review example usage in this guide
- Open an issue on GitHub for bugs or questions

