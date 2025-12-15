"""Tests for CSV parser module."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from finance_tracker.csv_parser import (
    CSVParser,
    CSVParserError,
    CSVFormat,
    InvalidDataError,
    UnsupportedFormatError,
    parse_csv,
)
from finance_tracker.models import TransactionType


class TestCSVParser:
    """Tests for CSVParser class."""

    @pytest.fixture
    def sample_data_dir(self):
        """Return path to sample data directory."""
        return Path(__file__).parent.parent / "sample_data"

    @pytest.fixture
    def parser(self):
        """Create a CSVParser instance."""
        return CSVParser()

    def test_detect_standard_format(self, parser, sample_data_dir):
        """Test detection of standard CSV format."""
        csv_file = sample_data_dir / "bank_statement_jan_2024.csv"
        format_type = parser.detect_format(csv_file)
        assert format_type == CSVFormat.STANDARD

    def test_detect_alternative_format(self, parser, sample_data_dir):
        """Test detection of alternative CSV format."""
        csv_file = sample_data_dir / "bank_statement_alternative_format.csv"
        format_type = parser.detect_format(csv_file)
        assert format_type == CSVFormat.ALTERNATIVE

    def test_detect_debit_credit_format(self, parser, sample_data_dir):
        """Test detection of debit/credit CSV format."""
        csv_file = sample_data_dir / "bank_statement_debit_credit_format.csv"
        format_type = parser.detect_format(csv_file)
        assert format_type == CSVFormat.DEBIT_CREDIT

    def test_detect_unknown_format(self, parser, tmp_path):
        """Test detection of unknown CSV format."""
        csv_file = tmp_path / "unknown.csv"
        csv_file.write_text("Unknown,Headers,Here\n1,2,3\n")
        format_type = parser.detect_format(csv_file)
        assert format_type == CSVFormat.UNKNOWN

    def test_parse_standard_format(self, parser, sample_data_dir):
        """Test parsing standard format CSV."""
        csv_file = sample_data_dir / "bank_statement_jan_2024.csv"
        transactions = parser.parse(csv_file)

        assert len(transactions) > 0
        assert all(isinstance(t, type(transactions[0])) for t in transactions)

        # Check first transaction (salary deposit)
        first = transactions[0]
        assert first.date == date(2024, 1, 2)
        assert first.amount == Decimal("3000.00")
        assert first.description == "Salary Deposit"
        assert first.transaction_type == TransactionType.CREDIT

        # Check a debit transaction
        debit_txn = next(t for t in transactions if t.transaction_type == TransactionType.DEBIT)
        assert debit_txn.amount < 0
        assert debit_txn.balance is not None

    def test_parse_alternative_format(self, parser, sample_data_dir):
        """Test parsing alternative format CSV."""
        csv_file = sample_data_dir / "bank_statement_alternative_format.csv"
        transactions = parser.parse(csv_file)

        assert len(transactions) > 0

        # Check that categories are parsed
        categorized = [t for t in transactions if t.category is not None]
        assert len(categorized) > 0

        # Check transaction types
        first = transactions[0]
        assert first.transaction_type == TransactionType.DEBIT
        assert first.amount < 0

    def test_parse_debit_credit_format(self, parser, sample_data_dir):
        """Test parsing debit/credit format CSV."""
        csv_file = sample_data_dir / "bank_statement_debit_credit_format.csv"
        transactions = parser.parse(csv_file)

        assert len(transactions) > 0

        # Check first transaction (credit)
        first = transactions[0]
        assert first.transaction_type == TransactionType.CREDIT
        assert first.amount > 0

        # Check a debit transaction
        debit_txn = next(t for t in transactions if t.transaction_type == TransactionType.DEBIT)
        assert debit_txn.amount < 0

    def test_parse_with_account(self, parser, sample_data_dir):
        """Test parsing with account identifier."""
        parser_with_account = CSVParser(account="CHECKING-123")
        csv_file = sample_data_dir / "bank_statement_jan_2024.csv"
        transactions = parser_with_account.parse(csv_file)

        assert all(t.account == "CHECKING-123" for t in transactions)

    def test_parse_nonexistent_file(self, parser):
        """Test parsing nonexistent file raises error."""
        with pytest.raises(CSVParserError, match="File not found"):
            parser.parse(Path("nonexistent.csv"))

    def test_parse_unsupported_format(self, parser, tmp_path):
        """Test parsing unsupported format raises error."""
        csv_file = tmp_path / "unknown.csv"
        csv_file.write_text("Unknown,Headers\n1,2\n")

        with pytest.raises(UnsupportedFormatError):
            parser.parse(csv_file)

    def test_parse_invalid_date(self, parser, tmp_path):
        """Test parsing CSV with invalid date raises error."""
        csv_file = tmp_path / "invalid_date.csv"
        csv_file.write_text("Date,Description,Amount\nINVALID-DATE,Test,100.00\n")

        with pytest.raises(InvalidDataError, match="Unable to parse date"):
            parser.parse(csv_file)

    def test_parse_invalid_amount(self, parser, tmp_path):
        """Test parsing CSV with invalid amount raises error."""
        csv_file = tmp_path / "invalid_amount.csv"
        csv_file.write_text("Date,Description,Amount\n2024-01-01,Test,NOT-A-NUMBER\n")

        with pytest.raises(InvalidDataError, match="Unable to parse decimal"):
            parser.parse(csv_file)

    def test_parse_empty_rows_skipped(self, parser, tmp_path):
        """Test that empty rows are skipped."""
        csv_file = tmp_path / "empty_rows.csv"
        csv_file.write_text("Date,Description,Amount\n2024-01-01,Test,100.00\n\n2024-01-02,Test2,50.00\n")

        transactions = parser.parse(csv_file)
        assert len(transactions) == 2

    def test_parse_zero_amount_skipped(self, parser, tmp_path):
        """Test that zero-amount transactions are skipped."""
        csv_file = tmp_path / "zero_amount.csv"
        csv_file.write_text("Date,Description,Amount\n2024-01-01,Test,100.00\n2024-01-02,Zero,0.00\n")

        transactions = parser.parse(csv_file)
        assert len(transactions) == 1
        assert transactions[0].amount != 0

    def test_parse_decimal_with_commas(self, parser, tmp_path):
        """Test parsing decimal values with commas."""
        csv_file = tmp_path / "commas.csv"
        csv_file.write_text("Date,Description,Amount\n2024-01-01,Test,\"1,234.56\"\n")

        transactions = parser.parse(csv_file)
        assert transactions[0].amount == Decimal("1234.56")

    def test_parse_decimal_with_dollar_sign(self, parser, tmp_path):
        """Test parsing decimal values with dollar signs."""
        csv_file = tmp_path / "dollar_sign.csv"
        csv_file.write_text("Date,Description,Amount\n2024-01-01,Test,$123.45\n")

        transactions = parser.parse(csv_file)
        assert transactions[0].amount == Decimal("123.45")

    def test_parse_date_formats(self, parser):
        """Test parsing different date formats."""
        # ISO format
        date1 = CSVParser._parse_date("2024-01-15")
        assert date1 == date(2024, 1, 15)

        # MM/DD/YYYY
        date2 = CSVParser._parse_date("01/15/2024")
        assert date2 == date(2024, 1, 15)

        # DD/MM/YYYY
        date3 = CSVParser._parse_date("15/01/2024")
        assert date3 == date(2024, 1, 15)

        # Invalid format
        with pytest.raises(ValueError):
            CSVParser._parse_date("invalid")

    def test_parse_debit_credit_both_filled(self, parser, tmp_path):
        """Test that debit/credit format with both filled raises error."""
        csv_file = tmp_path / "both_filled.csv"
        csv_file.write_text("Date,Description,Debit,Credit\n2024-01-01,Test,100.00,50.00\n")

        with pytest.raises(InvalidDataError, match="Both debit and credit cannot be non-zero"):
            parser.parse(csv_file)

    def test_convenience_function(self, sample_data_dir):
        """Test parse_csv convenience function."""
        csv_file = sample_data_dir / "bank_statement_jan_2024.csv"
        transactions = parse_csv(csv_file, account="TEST-ACCOUNT")

        assert len(transactions) > 0
        assert all(t.account == "TEST-ACCOUNT" for t in transactions)

