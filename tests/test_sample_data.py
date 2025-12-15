"""Tests for sample CSV data files."""

import csv
from pathlib import Path

import pytest


class TestSampleCSVFiles:
    """Tests to validate sample CSV files exist and have correct structure."""

    @pytest.fixture
    def sample_data_dir(self):
        """Return path to sample data directory."""
        return Path(__file__).parent.parent / "sample_data"

    def test_sample_data_directory_exists(self, sample_data_dir):
        """Test that sample data directory exists."""
        assert sample_data_dir.exists()
        assert sample_data_dir.is_dir()

    def test_january_csv_exists(self, sample_data_dir):
        """Test that January 2024 CSV file exists."""
        csv_file = sample_data_dir / "bank_statement_jan_2024.csv"
        assert csv_file.exists()
        assert csv_file.is_file()

    def test_february_csv_exists(self, sample_data_dir):
        """Test that February 2024 CSV file exists."""
        csv_file = sample_data_dir / "bank_statement_feb_2024.csv"
        assert csv_file.exists()
        assert csv_file.is_file()

    def test_alternative_format_csv_exists(self, sample_data_dir):
        """Test that alternative format CSV file exists."""
        csv_file = sample_data_dir / "bank_statement_alternative_format.csv"
        assert csv_file.exists()
        assert csv_file.is_file()

    def test_debit_credit_format_csv_exists(self, sample_data_dir):
        """Test that debit/credit format CSV file exists."""
        csv_file = sample_data_dir / "bank_statement_debit_credit_format.csv"
        assert csv_file.exists()
        assert csv_file.is_file()

    def test_january_csv_structure(self, sample_data_dir):
        """Test that January CSV has correct structure."""
        csv_file = sample_data_dir / "bank_statement_jan_2024.csv"
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            assert headers is not None
            assert "Date" in headers
            assert "Description" in headers
            assert "Amount" in headers
            assert "Balance" in headers

            # Check that we have data rows
            rows = list(reader)
            assert len(rows) > 0

            # Validate first row structure
            first_row = rows[0]
            assert "Date" in first_row
            assert "Description" in first_row
            assert "Amount" in first_row
            assert "Balance" in first_row

    def test_february_csv_structure(self, sample_data_dir):
        """Test that February CSV has correct structure."""
        csv_file = sample_data_dir / "bank_statement_feb_2024.csv"
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            assert headers is not None
            assert "Date" in headers
            assert "Description" in headers
            assert "Amount" in headers

            rows = list(reader)
            assert len(rows) > 0

    def test_alternative_format_csv_structure(self, sample_data_dir):
        """Test that alternative format CSV has correct structure."""
        csv_file = sample_data_dir / "bank_statement_alternative_format.csv"
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            assert headers is not None
            assert "Transaction Date" in headers or "Date" in headers
            assert "Description" in headers
            assert "Amount" in headers or ("Debit" in headers and "Credit" in headers)

            rows = list(reader)
            assert len(rows) > 0

    def test_debit_credit_format_csv_structure(self, sample_data_dir):
        """Test that debit/credit format CSV has correct structure."""
        csv_file = sample_data_dir / "bank_statement_debit_credit_format.csv"
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            assert headers is not None
            assert "Date" in headers
            assert "Description" in headers
            assert "Debit" in headers
            assert "Credit" in headers
            assert "Balance" in headers

            rows = list(reader)
            assert len(rows) > 0

    def test_csv_files_are_readable(self, sample_data_dir):
        """Test that all CSV files can be read without errors."""
        csv_files = list(sample_data_dir.glob("*.csv"))
        assert len(csv_files) > 0

        for csv_file in csv_files:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                # Try to read all rows
                rows = list(reader)
                assert len(rows) > 0, f"{csv_file.name} should have at least one data row"

    def test_csv_files_have_valid_dates(self, sample_data_dir):
        """Test that CSV files contain valid date formats."""
        from datetime import datetime

        csv_file = sample_data_dir / "bank_statement_jan_2024.csv"
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                date_str = row.get("Date")
                if date_str:
                    # Should be parseable as date
                    try:
                        datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        pytest.fail(f"Invalid date format: {date_str}")

    def test_csv_files_have_valid_amounts(self, sample_data_dir):
        """Test that CSV files contain valid numeric amounts."""
        csv_file = sample_data_dir / "bank_statement_jan_2024.csv"
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                amount_str = row.get("Amount")
                if amount_str:
                    try:
                        float(amount_str.replace(",", ""))
                    except ValueError:
                        pytest.fail(f"Invalid amount format: {amount_str}")

