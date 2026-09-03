"""Security hardening tests."""

import stat
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from finance_tracker.models import Transaction, TransactionType
from finance_tracker.safe_regex import compile_user_regex
from finance_tracker.storage import StorageManager, sanitize_csv_cell
from finance_tracker.web_app import import_csv_file, init_workflow


class TestSafeRegex:
    def test_accepts_simple_merchant_pattern(self):
        compiled = compile_user_regex(r"zephyr.?market")
        assert compiled.search("ZEPHYR MARKET")

    def test_rejects_nested_quantifiers(self):
        with pytest.raises(ValueError, match="nested"):
            compile_user_regex(r"(a+)+")

    def test_rejects_stacked_wildcards(self):
        with pytest.raises(ValueError, match="nested"):
            compile_user_regex(r".*.*.*")

    def test_rejects_overlong_pattern(self):
        with pytest.raises(ValueError, match="too long"):
            compile_user_regex("a" * 200)

    def test_rejects_empty_pattern(self):
        with pytest.raises(ValueError, match="required"):
            compile_user_regex("   ")


class TestCsvExport:
    def test_formula_injection_is_prefixed(self):
        assert sanitize_csv_cell("=CMD()") == "'=CMD()"
        assert sanitize_csv_cell("+1+1") == "'+1+1"
        assert sanitize_csv_cell("Grocery") == "Grocery"

    def test_csv_export_neutralizes_formulas_and_is_private(self, tmp_path):
        manager = StorageManager(tmp_path)
        manager.transaction_repo.save(
            [
                Transaction(
                    date=date(2024, 1, 1),
                    amount=Decimal("-1.00"),
                    description='=HYPERLINK("http://evil")',
                    transaction_type=TransactionType.DEBIT,
                    notes="@SUM(A1)",
                )
            ]
        )
        out = tmp_path / "export.csv"
        manager.export_transactions_csv(out)
        body = out.read_text(encoding="utf-8")
        assert "'=HYPERLINK" in body
        assert "'@SUM" in body
        assert stat.S_IMODE(out.stat().st_mode) == 0o600


class TestImportPath:
    def test_web_import_rejects_non_csv(self, tmp_path):
        init_workflow(tmp_path)
        secrets = tmp_path / "secrets.txt"
        secrets.write_text("not a csv", encoding="utf-8")
        result = import_csv_file(str(secrets))
        assert result["success"] is False
        assert "csv" in result["error"].lower()


class TestKeyHandling:
    def test_key_is_not_passed_on_argv(self):
        source = Path("finance_tracker/secure_store.py").read_text(encoding="utf-8")
        assert "_keychain_set" not in source
        assert "add-generic-password" not in source
