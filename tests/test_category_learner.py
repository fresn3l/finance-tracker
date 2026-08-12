"""Tests for learning category corrections."""

from datetime import date
from decimal import Decimal

from finance_tracker.category_learner import CategoryLearner, normalize_merchant
from finance_tracker.category_mapper import CategoryMapper
from finance_tracker.models import Category, Transaction, TransactionType
from finance_tracker.storage import TransactionRepository
from finance_tracker.transaction_editor import TransactionEditor
from finance_tracker.workflow import FinanceTrackerWorkflow


def _debit(description, txn_id, category=None):
    return Transaction(
        date=date(2024, 3, 1),
        amount=Decimal("-12.00"),
        description=description,
        transaction_type=TransactionType.DEBIT,
        category=category,
        id=txn_id,
    )


class TestNormalizeMerchant:
    def test_strips_store_numbers_and_case(self):
        assert normalize_merchant("Local Coffee Roasters #1234") == "LOCAL COFFEE ROASTERS"
        assert normalize_merchant("LOCAL COFFEE ROASTERS 5678") == "LOCAL COFFEE ROASTERS"


class TestCategoryLearner:
    def test_learn_then_lookup(self, tmp_path):
        learner = CategoryLearner(tmp_path)
        category = Category(name="Coffee Shops", parent="Food & Dining")
        key = learner.learn("LOCAL COFFEE ROASTERS #12", category)
        assert key == "LOCAL COFFEE ROASTERS"
        found = learner.lookup("Local Coffee Roasters #99")
        assert found is not None
        assert found.name == "Coffee Shops"
        assert found.parent == "Food & Dining"

    def test_latest_correction_wins(self, tmp_path):
        learner = CategoryLearner(tmp_path)
        learner.learn("ACME HARDWARE", Category(name="Shopping"))
        learner.learn("ACME HARDWARE", Category(name="Home Improvement", parent="Shopping"))
        found = learner.lookup("ACME HARDWARE")
        assert found is not None
        assert found.name == "Home Improvement"

    def test_skips_tiny_keys(self, tmp_path):
        learner = CategoryLearner(tmp_path)
        assert learner.learn("AB", Category(name="Other")) is None
        assert learner.lookup("AB") is None

    def test_learned_overrides_default_rule(self, tmp_path):
        learner = CategoryLearner(tmp_path)
        learner.learn("AMAZON.COM PURCHASE", Category(name="Office Supplies", parent="Shopping"))
        mapper = CategoryMapper(learner=learner)
        category = mapper.categorize("AMAZON.COM PURCHASE")
        assert category is not None
        assert category.name == "Office Supplies"

    def test_edit_learns_and_applies_to_similar(self, tmp_path):
        repo = TransactionRepository(tmp_path)
        repo.save(
            [
                _debit("LOCAL COFFEE ROASTERS #1", "c1"),
                _debit("LOCAL COFFEE ROASTERS #2", "c2"),
            ]
        )
        editor = TransactionEditor(repo)
        updated = editor.edit_transaction(
            "c1", category=Category(name="Coffee Shops", parent="Food & Dining")
        )
        assert updated is not None
        assert updated.category is not None
        assert updated.category.name == "Coffee Shops"

        other = repo.get_by_id("c2")
        assert other is not None
        assert other.category is not None
        assert other.category.name == "Coffee Shops"

        learner = CategoryLearner(tmp_path)
        assert learner.lookup("LOCAL COFFEE ROASTERS #9").name == "Coffee Shops"

    def test_import_uses_learned_category(self, tmp_path):
        learner = CategoryLearner(tmp_path)
        learner.learn("ZEPHYR MARKET", Category(name="Groceries", parent="Food & Dining"))

        csv_file = tmp_path / "stmt.csv"
        csv_file.write_text(
            "Date,Description,Amount,Balance\n"
            "2024-03-02,ZEPHYR MARKET #88,-21.50,900.00\n"
        )
        workflow = FinanceTrackerWorkflow(data_dir=tmp_path)
        transactions, _stats = workflow.process_csv_file(csv_file)
        assert len(transactions) == 1
        assert transactions[0].category is not None
        assert transactions[0].category.name == "Groceries"

    def test_bootstrap_from_existing_transactions(self, tmp_path):
        repo = TransactionRepository(tmp_path)
        repo.save(
            [
                _debit(
                    "ODD MERCHANT LLC",
                    "m1",
                    Category(name="Subscriptions", parent="Subscriptions"),
                )
            ]
        )
        workflow = FinanceTrackerWorkflow(data_dir=tmp_path)
        found = workflow.learner.lookup("ODD MERCHANT LLC")
        assert found is not None
        assert found.name == "Subscriptions"

    def test_recategorize_persists_learned_and_keeps_id(self, tmp_path):
        repo = TransactionRepository(tmp_path)
        repo.save([_debit("ZEPHYR MARKET", "z1")])
        CategoryLearner(tmp_path).learn(
            "ZEPHYR MARKET", Category(name="Groceries", parent="Food & Dining")
        )
        workflow = FinanceTrackerWorkflow(data_dir=tmp_path)
        stats = workflow.recategorize_all(overwrite=True)
        assert stats["categorized"] >= 1
        loaded = repo.get_by_id("z1")
        assert loaded is not None
        assert loaded.id == "z1"
        assert loaded.category is not None
        assert loaded.category.name == "Groceries"
