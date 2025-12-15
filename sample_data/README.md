# Sample CSV Data Files

This directory contains sample bank statement CSV files in various formats for testing and development.

## File Formats

### Standard Format (Date, Description, Amount, Balance)
- `bank_statement_jan_2024.csv` - January 2024 transactions
- `bank_statement_feb_2024.csv` - February 2024 transactions

**Format:**
```csv
Date,Description,Amount,Balance
2024-01-02,Salary Deposit,3000.00,5000.00
2024-01-03,GROCERY STORE #1234,-45.67,4954.33
```

**Characteristics:**
- Date format: YYYY-MM-DD
- Amount: Positive for credits (income), negative for debits (expenses)
- Balance: Account balance after each transaction

### Alternative Format (With Category and Type)
- `bank_statement_alternative_format.csv`

**Format:**
```csv
Transaction Date,Post Date,Description,Category,Type,Amount
2024-01-15,2024-01-15,GROCERY STORE WHOLE FOODS,Food,debit,125.50
```

**Characteristics:**
- Includes category and transaction type columns
- Separate transaction and post dates
- Type field explicitly indicates debit/credit

### Debit/Credit Format (Separate Columns)
- `bank_statement_debit_credit_format.csv`

**Format:**
```csv
Date,Description,Debit,Credit,Balance
2024-01-10,Salary Payment,,2000.00,2000.00
2024-01-11,Grocery Store Purchase,85.50,,1914.50
```

**Characteristics:**
- Separate Debit and Credit columns
- Empty values in the opposite column
- Common format for many bank exports

## Transaction Categories in Sample Data

The sample data includes transactions across various categories:
- **Food & Dining**: Grocery stores, restaurants, coffee shops
- **Transportation**: Gas stations
- **Utilities**: Electric, water bills
- **Entertainment**: Netflix, Spotify, Amazon Prime
- **Health**: Pharmacy purchases
- **Income**: Salary deposits
- **Transfers**: Savings transfers

## Usage

These files can be used to:
1. Test CSV parsing functionality
2. Develop and test categorization logic
3. Validate data models
4. Test spending analysis features
5. Develop UI components with realistic data

## Notes

- All amounts are in USD
- Dates are in ISO format (YYYY-MM-DD)
- Negative amounts represent debits (money going out)
- Positive amounts represent credits (money coming in)
- Sample data includes realistic transaction patterns and amounts

