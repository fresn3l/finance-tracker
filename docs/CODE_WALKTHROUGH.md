# Code Walkthrough: Understanding the Finance Tracker

This guide walks through the codebase step-by-step, explaining how everything fits together. Perfect for someone new to the codebase who wants to understand how it works.

## Starting Point: The Workflow

The best place to start understanding the codebase is `workflow.py`, specifically the `process_csv_file()` method. This method shows the complete flow from CSV file to stored, categorized transactions.

```python
def process_csv_file(self, csv_file: Path, ...):
    # Step 1: Parse CSV
    transactions = self.parser.parse(csv_file)
    
    # Step 2: Check duplicates
    duplicates = self.storage.transaction_repo.check_duplicates(transactions)
    
    # Step 3: Categorize
    categorized, stats = self.categorizer.categorize_transactions(transactions)
    
    # Step 4: Store
    self.storage.transaction_repo.save(categorized)
```

This is the "big picture" - everything else supports this workflow.

## Step-by-Step Deep Dive

### Step 1: CSV Parsing (`csv_parser.py`)

**What happens**: CSV file → List of Transaction objects

**How it works**:

1. **Format Detection** (`detect_format()`):
   ```python
   # Reads just the header row
   headers = csv.DictReader(f).fieldnames
   # Checks for key column names
   if "transaction date" in headers and "type" in headers:
       return CSVFormat.ALTERNATIVE
   ```

2. **Parsing** (`parse()`):
   ```python
   # Selects the right parser based on format
   if format_type == CSVFormat.STANDARD:
       return self._parse_standard(file_path)
   ```

3. **Row Processing** (`_parse_standard()`):
   ```python
   # For each row:
   # - Parse date string to date object
   # - Parse amount string to Decimal
   # - Create Transaction object
   transaction = Transaction(date=..., amount=..., ...)
   ```

**Key Learning**: Strategy pattern - different parsers for different formats

### Step 2: Duplicate Detection (`storage.py`)

**What happens**: New transactions → Filtered list (duplicates removed)

**How it works**:

1. **Fingerprinting** (`transaction_id()`):
   ```python
   # Creates unique ID from key attributes
   fingerprint = f"{date}|{amount}|{description.lower()}|{reference}"
   ```

2. **Comparison** (`check_duplicates()`):
   ```python
   # Load stored transactions
   stored = self.load_all()
   stored_ids = {self.transaction_id(t) for t in stored}
   
   # Check new transactions against stored
   duplicates = [t for t in new if self.transaction_id(t) in stored_ids]
   ```

**Key Learning**: Set-based lookup for O(1) duplicate checking

### Step 3: Categorization (`categorizer.py` + `category_mapper.py`)

**What happens**: Uncategorized transactions → Categorized transactions

**How it works**:

1. **Rule Matching** (`CategoryMapper.categorize()`):
   ```python
   # Check each rule in order
   for rule in self.rules:
       if rule.pattern.search(description):
           return Category(name=rule.category_name, ...)
   ```

2. **Batch Processing** (`categorize_transactions()`):
   ```python
   # Process all transactions
   for transaction in transactions:
       category = mapper.categorize(transaction.description)
       transaction.category = category
   ```

**Key Learning**: Rule-based systems are simple but effective

### Step 4: Storage (`storage.py`)

**What happens**: Transaction objects → JSON file on disk

**How it works**:

1. **Serialization** (`_serialize_transaction()`):
   ```python
   # Convert Transaction object to dictionary
   data = {
       "date": transaction.date.isoformat(),
       "amount": str(transaction.amount),
       ...
   }
   ```

2. **File Writing** (`save()`):
   ```python
   # Write to JSON file
   with open(self.transactions_file, "w") as f:
       json.dump({"transactions": serialized_data}, f)
   ```

**Key Learning**: Repository pattern abstracts storage details

### Step 5: Analysis (`analyzer.py`)

**What happens**: Stored transactions → Insights and summaries

**How it works**:

1. **Filtering** (`_filter_transactions()`):
   ```python
   # Filter by date range
   filtered = [t for t in transactions if t.date.year == year]
   ```

2. **Aggregation** (`get_monthly_summary()`):
   ```python
   # Sum transactions
   total_expenses = sum(t.absolute_amount for t in expenses)
   ```

3. **Category Breakdown**:
   ```python
   # Group by category
   for transaction in expenses:
       category_breakdown[transaction.category.name] += amount
   ```

**Key Learning**: Data aggregation patterns

## Data Flow Example

Let's trace a single transaction through the system:

```
1. CSV File Row:
   "2024-01-15,Grocery Store,-50.00,1000.00"
   
2. CSVParser.parse():
   → Transaction(
       date=date(2024, 1, 15),
       amount=Decimal("-50.00"),
       description="Grocery Store",
       transaction_type=TransactionType.DEBIT,
       category=None  # Not categorized yet
   )
   
3. TransactionCategorizer.categorize_transaction():
   → CategoryMapper.categorize("Grocery Store")
   → Matches rule: r"(?i)\b(grocery|supermarket)\b"
   → Returns Category(name="Groceries", parent="Food & Dining")
   → Transaction.category = Category(...)
   
4. TransactionRepository.save():
   → Generates UUID: "abc-123-def"
   → Serializes to JSON
   → Writes to transactions.json
   
5. SpendingAnalyzer.get_monthly_summary():
   → Filters: year=2024, month=1
   → Finds this transaction
   → Adds $50 to "Groceries" category
   → Adds $50 to total_expenses
```

## Key Algorithms Explained

### Duplicate Detection Algorithm

```python
def transaction_id(transaction):
    # Create fingerprint from key attributes
    parts = [
        transaction.date.isoformat(),      # Date
        str(transaction.amount),           # Amount
        transaction.description.lower(),   # Description (normalized)
    ]
    if transaction.reference:
        parts.append(transaction.reference)  # Reference (if available)
    return "|".join(parts)  # Join with pipe separator
```

**Why this works**:
- Date + Amount + Description uniquely identifies most transactions
- Normalization (lowercase) handles case variations
- Reference adds extra uniqueness when available

### Categorization Algorithm

```python
def categorize(description):
    description_lower = description.lower()
    for rule in self.rules:  # Check rules in order
        if rule.pattern.search(description_lower):
            return Category(name=rule.category_name, ...)
    return None  # No match found
```

**Why this works**:
- Regex patterns are flexible (handle variations)
- First match wins (priority-based)
- Case-insensitive matching handles "GROCERY" = "grocery"

### Monthly Summary Algorithm

```python
def get_monthly_summary(year, month):
    # Filter transactions
    month_transactions = [t for t in transactions 
                         if t.date.year == year and t.date.month == month]
    
    # Initialize totals
    total_income = Decimal("0")
    total_expenses = Decimal("0")
    category_breakdown = defaultdict(Decimal)
    
    # Process each transaction
    for transaction in month_transactions:
        if transaction.is_income:
            total_income += transaction.absolute_amount
        elif transaction.is_expense:
            total_expenses += transaction.absolute_amount
            if transaction.category:
                category_breakdown[transaction.category.name] += amount
    
    # Calculate net
    net_amount = total_income - total_expenses
    
    return MonthlySummary(...)
```

**Why this works**:
- Simple aggregation (sum, count)
- defaultdict handles new categories automatically
- Decimal prevents floating-point errors

## Common Patterns

### 1. Filter-Then-Process

```python
# Pattern: Filter first, then process
filtered = [item for item in items if condition]
results = process(filtered)
```

Used in:
- `analyzer.py`: Filter by date, then analyze
- `search_filter.py`: Apply filters, then return results

### 2. Accumulator Pattern

```python
# Pattern: Initialize, accumulate, return
total = Decimal("0")
for item in items:
    total += item.amount
return total
```

Used in:
- `analyzer.py`: Summing expenses, income
- `budget_tracker.py`: Calculating spending

### 3. Dictionary Aggregation

```python
# Pattern: Group and sum
breakdown = defaultdict(Decimal)
for transaction in transactions:
    breakdown[transaction.category.name] += amount
```

Used in:
- `analyzer.py`: Category breakdowns
- `budget_tracker.py`: Budget status

## Error Handling Strategy

### Levels of Error Handling

1. **Low Level** (csv_parser.py):
   - Catch parsing errors
   - Re-raise with context (row number, error message)

2. **Mid Level** (workflow.py):
   - Catch component errors
   - Log and continue (don't fail entire workflow)

3. **High Level** (cli.py, web_app.py):
   - Catch all errors
   - Show user-friendly messages

### Example Error Flow

```
CSV Row Error:
  csv_parser.py → InvalidDataError("Row 5: Invalid date")
    ↓
  workflow.py → Logs error, continues with other rows
    ↓
  cli.py → Shows: "Warning: 1 row had errors, 99 rows imported successfully"
```

## Testing Strategy

### Unit Tests

Test individual functions/methods:
```python
def test_parse_date():
    assert CSVParser._parse_date("2024-01-15") == date(2024, 1, 15)
```

### Integration Tests

Test workflows end-to-end:
```python
def test_import_workflow():
    workflow.process_csv_file("test.csv")
    transactions = workflow.storage.transaction_repo.load_all()
    assert len(transactions) > 0
```

## How to Read the Code

### For Understanding

1. Start with `workflow.py` - see the big picture
2. Read `models.py` - understand the data structures
3. Pick a module - read it in detail
4. Trace through an example - follow data flow

### For Learning

1. Read docstrings - they explain what and why
2. Read inline comments - they explain how
3. Run the code - see it in action
4. Modify and test - learn by doing

### For Contributing

1. Understand the architecture (see ARCHITECTURE.md)
2. Find the right module for your change
3. Follow existing patterns
4. Add tests for your changes

## Common Questions

### Q: Why Decimal instead of float?

**A**: Floating-point has precision issues. `0.1 + 0.2 != 0.3` in floating-point, but equals exactly `0.3` in Decimal. Financial calculations need exact precision.

### Q: Why Pydantic models?

**A**: Automatic validation, type safety, and JSON serialization. Catches errors early and makes code more reliable.

### Q: Why repository pattern?

**A**: Abstracts storage details. Business logic doesn't care if data is in JSON or a database. Makes testing easier and allows future migration.

### Q: Why workflow pattern?

**A**: Coordinates complex operations. Instead of calling 5 methods, call 1 workflow method. Simpler API, consistent behavior.

### Q: How do I add a new feature?

**A**: 
1. Identify which module it belongs to
2. Follow existing patterns
3. Add tests
4. Update documentation

## Next Steps

1. **Read the code**: Start with workflow.py, then explore
2. **Run examples**: Use the sample CSV files
3. **Modify something**: Try adding a category rule
4. **Read tests**: See how things are tested
5. **Check docs**: ARCHITECTURE.md, API.md for more details

