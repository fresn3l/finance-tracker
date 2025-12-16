# Contributing to Finance Tracker

Thank you for your interest in contributing to Finance Tracker! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Code Style](#code-style)
4. [Testing](#testing)
5. [Documentation](#documentation)
6. [Submitting Changes](#submitting-changes)

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone <your-fork-url>`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git

### Setup Steps

```bash
# Clone the repository
git clone <repository-url>
cd finance-tracker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=finance_tracker --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run with verbose output
pytest -v
```

### Running the Application

```bash
# CLI
finance-tracker import-csv sample_data/bank_statement_jan_2024.csv

# Web app
finance-tracker-web
```

## Code Style

### Formatting

We use **Black** for code formatting and **ruff** for linting.

```bash
# Format code
black finance_tracker tests

# Check linting
ruff check finance_tracker tests

# Auto-fix linting issues
ruff check --fix finance_tracker tests
```

### Type Hints

- Use type hints for all function parameters and return values
- Use `Optional[T]` for nullable types
- Use `List[T]` and `Dict[K, V]` for collections
- Use `Path` from `pathlib` for file paths

### Docstrings

Follow Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of the function.

    Longer description explaining what the function does, any important
    details, and usage examples.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong

    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
    pass
```

### Naming Conventions

- **Classes**: PascalCase (e.g., `TransactionCategorizer`)
- **Functions/Methods**: snake_case (e.g., `get_monthly_summary`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_PORT`)
- **Private methods**: Leading underscore (e.g., `_load_default_rules`)

## Testing

### Writing Tests

- Place tests in the `tests/` directory
- Test file names should start with `test_`
- Use descriptive test names: `test_parse_csv_with_invalid_date`
- Test both success and failure cases
- Use fixtures for common setup

Example:

```python
import pytest
from finance_tracker.models import Transaction

def test_transaction_creation():
    """Test creating a valid transaction."""
    transaction = Transaction(...)
    assert transaction.amount > 0

def test_transaction_zero_amount_raises_error():
    """Test that zero amount transactions are rejected."""
    with pytest.raises(ValueError):
        Transaction(amount=Decimal("0"), ...)
```

### Test Coverage

- Aim for >80% code coverage
- Focus on testing business logic
- Don't test implementation details
- Use `pytest-cov` to check coverage

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Include examples in docstrings where helpful
- Document complex algorithms
- Explain "why" not just "what" in comments

### Documentation Files

- Update `README.md` for user-facing changes
- Update `docs/ARCHITECTURE.md` for architectural changes
- Update `docs/API.md` for API changes
- Add new documentation files as needed

## Module Organization

When adding new functionality:

1. **Determine the right module**: Place code in the most appropriate existing module, or create a new one if needed
2. **Follow existing patterns**: Match the style and structure of existing code
3. **Keep modules focused**: Each module should have a single, clear responsibility
4. **Update exports**: Add new public classes/functions to `__init__.py` if they should be part of the public API

## Submitting Changes

### Commit Messages

Use clear, descriptive commit messages:

```
Add support for new CSV format

- Implement parser for bank-specific format
- Add tests for new format
- Update documentation
```

### Pull Request Process

1. Ensure all tests pass
2. Ensure code is formatted and linted
3. Update documentation as needed
4. Write a clear PR description explaining:
   - What changes were made
   - Why the changes were needed
   - How to test the changes
5. Reference any related issues

### Code Review

- Be open to feedback
- Respond to review comments promptly
- Make requested changes or discuss alternatives
- Keep PRs focused and reasonably sized

## Areas for Contribution

### Good First Issues

- Adding new category rules
- Improving error messages
- Adding more CSV format support
- Writing additional tests
- Documentation improvements

### Feature Ideas

See `FUTURE_WORK.md` for ideas on features to implement.

## Questions?

- Open an issue for bugs or feature requests
- Check existing documentation first
- Ask questions in PR comments

Thank you for contributing! 🎉

