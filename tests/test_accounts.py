"""Tests for accounts, net worth, and goals."""

from decimal import Decimal

from finance_tracker.accounts import AccountRepository, GoalRepository
from finance_tracker.models import Account, AccountType, FinancialGoal, GoalType


class TestAccountsAndGoals:
    def test_net_worth_subtracts_liabilities(self, tmp_path):
        repo = AccountRepository(tmp_path)
        repo.upsert(Account(name="Checking", account_type=AccountType.CHECKING, balance=Decimal("1000")))
        repo.upsert(Account(name="Brokerage", account_type=AccountType.INVESTMENT, balance=Decimal("5000")))
        repo.upsert(Account(name="Visa", account_type=AccountType.CREDIT_CARD, balance=Decimal("200")))
        repo.upsert(Account(name="Car loan", account_type=AccountType.LOAN, balance=Decimal("800")))

        assert repo.net_worth() == Decimal("5000")
        loaded = {a.name: a for a in repo.load_all()}
        assert loaded["Brokerage"].is_investment
        assert loaded["Visa"].is_liability

    def test_goal_add_assigns_id_and_progress(self, tmp_path):
        repo = GoalRepository(tmp_path)
        created = repo.add(
            FinancialGoal(
                id="",
                name="Emergency fund",
                goal_type=GoalType.SAVINGS,
                target_amount=Decimal("5000"),
                current_amount=Decimal("1000"),
            )
        )
        assert created.id
        loaded = repo.load_all()
        assert len(loaded) == 1
        assert loaded[0].name == "Emergency fund"
        assert loaded[0].progress_percent == 20.0
