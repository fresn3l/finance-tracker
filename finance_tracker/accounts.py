"""Accounts (including investments and debts) and net worth."""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from finance_tracker.models import Account, AccountType
from finance_tracker.secure_store import SecureJSON

logger = logging.getLogger(__name__)


class AccountRepository:
    """Persist accounts as encrypted JSON."""

    def __init__(self, data_dir: Path, secure: Optional[SecureJSON] = None):
        self.data_dir = Path(data_dir)
        self.secure = secure or SecureJSON(self.data_dir)
        self.accounts_file = self.data_dir / "accounts.json"

    def load_all(self) -> List[Account]:
        if not self.accounts_file.exists():
            return []
        data = self.secure.read(self.accounts_file)
        accounts = []
        for item in data.get("accounts", []):
            accounts.append(
                Account(
                    name=item["name"],
                    account_type=AccountType(item.get("account_type", "checking")),
                    institution=item.get("institution"),
                    balance=Decimal(item.get("balance", "0")),
                    notes=item.get("notes"),
                )
            )
        return accounts

    def save_all(self, accounts: List[Account]) -> None:
        payload = {
            "accounts": [
                {
                    "name": a.name,
                    "account_type": a.account_type.value,
                    "institution": a.institution,
                    "balance": str(a.balance),
                    "notes": a.notes,
                }
                for a in accounts
            ]
        }
        self.secure.write(self.accounts_file, payload)

    def upsert(self, account: Account) -> None:
        accounts = [a for a in self.load_all() if a.name != account.name]
        accounts.append(account)
        self.save_all(accounts)

    def delete(self, name: str) -> bool:
        accounts = self.load_all()
        kept = [a for a in accounts if a.name != name]
        if len(kept) == len(accounts):
            return False
        self.save_all(kept)
        return True

    def net_worth(self) -> Decimal:
        """Assets minus liabilities (credit cards and loans)."""
        total = Decimal("0")
        for account in self.load_all():
            if account.is_liability:
                total -= abs(account.balance)
            else:
                total += account.balance
        return total


class GoalRepository:
    """Persist financial goals as encrypted JSON."""

    def __init__(self, data_dir: Path, secure: Optional[SecureJSON] = None):
        self.data_dir = Path(data_dir)
        self.secure = secure or SecureJSON(self.data_dir)
        self.goals_file = self.data_dir / "goals.json"

    def load_all(self):
        from datetime import date as date_cls

        from finance_tracker.models import FinancialGoal, GoalType

        if not self.goals_file.exists():
            return []
        data = self.secure.read(self.goals_file)
        goals = []
        for item in data.get("goals", []):
            target_date = item.get("target_date")
            if isinstance(target_date, str) and target_date:
                target_date = date_cls.fromisoformat(target_date)
            elif not target_date:
                target_date = None
            goals.append(
                FinancialGoal(
                    id=item["id"],
                    name=item["name"],
                    goal_type=GoalType(item["goal_type"]),
                    target_amount=Decimal(item["target_amount"]),
                    current_amount=Decimal(item.get("current_amount", "0")),
                    target_date=target_date,
                    category=item.get("category"),
                    notes=item.get("notes"),
                )
            )
        return goals

    def save_all(self, goals) -> None:
        payload = {
            "goals": [
                {
                    "id": g.id,
                    "name": g.name,
                    "goal_type": g.goal_type.value,
                    "target_amount": str(g.target_amount),
                    "current_amount": str(g.current_amount),
                    "target_date": g.target_date.isoformat() if g.target_date else None,
                    "category": g.category,
                    "notes": g.notes,
                }
                for g in goals
            ]
        }
        self.secure.write(self.goals_file, payload)

    def add(self, goal):
        """Persist a goal, assigning an ID when missing. Returns the stored goal."""
        if not goal.id:
            goal = goal.model_copy(update={"id": str(uuid.uuid4())})
        goals = self.load_all()
        goals.append(goal)
        self.save_all(goals)
        return goal

    def delete(self, goal_id: str) -> bool:
        goals = self.load_all()
        kept = [g for g in goals if g.id != goal_id]
        if len(kept) == len(goals):
            return False
        self.save_all(kept)
        return True
