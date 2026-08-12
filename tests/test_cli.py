"""Tests for CLI commands, including later-feature coverage."""

from datetime import date
from decimal import Decimal

from click.testing import CliRunner

from finance_tracker.cli import cli
from finance_tracker.models import Category, Transaction, TransactionType
from finance_tracker.storage import TransactionRepository


def _seed_transaction(tmp_path, **overrides) -> Transaction:
    """Save one transaction and return it with its assigned ID."""
    data = {
        "date": date(2024, 1, 15),
        "amount": Decimal("-50.00"),
        "description": "GROCERY STORE",
        "transaction_type": TransactionType.DEBIT,
        "category": Category(name="Groceries", parent="Food & Dining"),
        "id": "txn-grocery-1",
    }
    data.update(overrides)
    transaction = Transaction(**data)
    TransactionRepository(tmp_path).save([transaction])
    return transaction


class TestCliLaterFeatures:
    """CLI coverage for list/edit/delete, budgets, and recurring."""

    def test_list_includes_transaction_id(self, tmp_path):
        _seed_transaction(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["--data-dir", str(tmp_path), "list"])

        assert result.exit_code == 0
        assert "txn-grocery-1" in result.output
        assert "GROCERY STORE" in result.output

    def test_edit_updates_category(self, tmp_path):
        _seed_transaction(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--data-dir",
                str(tmp_path),
                "edit",
                "txn-grocery-1",
                "--category",
                "Dining",
                "--notes",
                "reclassified",
            ],
        )

        assert result.exit_code == 0
        assert "Updated transaction" in result.output
        loaded = TransactionRepository(tmp_path).get_by_id("txn-grocery-1")
        assert loaded is not None
        assert loaded.category is not None
        assert loaded.category.name == "Dining"
        assert loaded.notes == "reclassified"

    def test_edit_missing_transaction_fails(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--data-dir", str(tmp_path), "edit", "missing-id", "--notes", "x"],
        )
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_delete_with_yes_flag(self, tmp_path):
        _seed_transaction(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--data-dir", str(tmp_path), "delete", "txn-grocery-1", "--yes"],
        )

        assert result.exit_code == 0
        assert TransactionRepository(tmp_path).get_by_id("txn-grocery-1") is None

    def test_budget_set_list_and_alerts(self, tmp_path):
        _seed_transaction(tmp_path)
        runner = CliRunner()

        set_result = runner.invoke(
            cli,
            [
                "--data-dir",
                str(tmp_path),
                "budget",
                "set",
                "Groceries",
                "--year",
                "2024",
                "--month",
                "1",
                "--amount",
                "40",
                "--alert-threshold",
                "0.5",
            ],
        )
        assert set_result.exit_code == 0

        list_result = runner.invoke(
            cli,
            [
                "--data-dir",
                str(tmp_path),
                "budget",
                "list",
                "--year",
                "2024",
                "--month",
                "1",
            ],
        )
        assert list_result.exit_code == 0
        assert "Groceries" in list_result.output
        assert "OVER" not in list_result.output or "125" in list_result.output

        alerts = runner.invoke(
            cli,
            [
                "--data-dir",
                str(tmp_path),
                "budget",
                "alerts",
                "--year",
                "2024",
                "--month",
                "1",
            ],
        )
        assert alerts.exit_code == 0
        assert "Groceries" in alerts.output

    def test_recurring_detect_and_mark(self, tmp_path):
        repo = TransactionRepository(tmp_path)
        repo.save(
            [
                Transaction(
                    date=date(2024, month, 5),
                    amount=Decimal("-15.99"),
                    description="NETFLIX.COM",
                    transaction_type=TransactionType.DEBIT,
                    id=f"netflix-{month}",
                )
                for month in range(1, 5)
            ]
        )
        runner = CliRunner()

        detect = runner.invoke(cli, ["--data-dir", str(tmp_path), "recurring", "detect"])
        assert detect.exit_code == 0
        assert "netflix" in detect.output.lower()

        mark = runner.invoke(cli, ["--data-dir", str(tmp_path), "recurring", "mark"])
        assert mark.exit_code == 0
        assert "Marked" in mark.output
        loaded = repo.load_all()
        assert all(t.is_recurring for t in loaded)
