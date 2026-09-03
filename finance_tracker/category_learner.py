"""
Learn category mappings from user corrections.

When a transaction is recategorized, the normalized merchant name is stored and
consulted before default regex rules. Later imports of the same merchant get
the user's category automatically.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

from finance_tracker.models import Category, Transaction
from finance_tracker.secure_store import SecureJSON, ensure_secure_dir

logger = logging.getLogger(__name__)

MIN_KEY_LENGTH = 3
_WS = re.compile(r"\s+")
_TRAILING_STORE_NUM = re.compile(r"(?:[\s\-#*]+\d+)+\s*$")
_LONG_NUM = re.compile(r"\b\d{4,}\b")
_NOISE = re.compile(r"[^A-Z0-9 &.'-]+")


def normalize_merchant(description: str) -> str:
    """Collapse a bank description into a stable merchant key."""
    text = (description or "").strip().upper()
    text = _WS.sub(" ", text)
    text = _TRAILING_STORE_NUM.sub("", text)
    text = _LONG_NUM.sub("", text)
    text = _NOISE.sub(" ", text)
    return _WS.sub(" ", text).strip(" -")


class CategoryLearner:
    """Persist merchant → category mappings from user corrections."""

    def __init__(self, data_dir: Path, secure: Optional[SecureJSON] = None):
        self.data_dir = Path(data_dir)
        ensure_secure_dir(self.data_dir)
        self.secure = secure or SecureJSON(self.data_dir)
        self.path = self.data_dir / "learned_categories.json"
        self._mappings: Dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            self.secure.migrate_if_plaintext(self.path)
            data = self.secure.read(self.path)
            mappings = data.get("mappings", {})
            if isinstance(mappings, dict):
                self._mappings = mappings
        except Exception as exc:
            logger.warning("Could not load learned categories: %s", exc)
            self._mappings = {}

    def _save(self) -> None:
        self.secure.write(self.path, {"mappings": self._mappings})

    def lookup(self, description: str) -> Optional[Category]:
        """Return a learned category for this description, if any."""
        key = normalize_merchant(description)
        if len(key) < MIN_KEY_LENGTH:
            return None
        item = self._mappings.get(key)
        if not item:
            return None
        name = item.get("category_name")
        if not name:
            return None
        return Category(name=name, parent=item.get("parent_category"))

    def learn(self, description: str, category: Category) -> Optional[str]:
        """
        Record that this merchant belongs in `category`.

        Latest correction wins. Returns the merchant key, or None if skipped.
        """
        key = normalize_merchant(description)
        if len(key) < MIN_KEY_LENGTH:
            return None

        existing = self._mappings.get(key)
        if (
            existing
            and existing.get("category_name") == category.name
            and existing.get("parent_category") == category.parent
        ):
            existing["count"] = int(existing.get("count", 1)) + 1
            existing["example"] = description[:120]
        else:
            self._mappings[key] = {
                "category_name": category.name,
                "parent_category": category.parent,
                "count": 1,
                "example": description[:120],
            }
        self._save()
        logger.info("Learned category %s for merchant %s", category.name, key)
        return key

    def bootstrap(self, transactions: List[Transaction]) -> int:
        """
        Seed mappings from already-categorized transactions.

        Does not overwrite keys the user has already learned. Returns how many
        new keys were added.
        """
        votes: Dict[str, Dict[tuple, int]] = {}
        examples: Dict[str, str] = {}
        for txn in transactions:
            if txn.category is None:
                continue
            key = normalize_merchant(txn.description)
            if len(key) < MIN_KEY_LENGTH:
                continue
            pair = (txn.category.name, txn.category.parent)
            votes.setdefault(key, {})
            votes[key][pair] = votes[key].get(pair, 0) + 1
            examples[key] = txn.description[:120]

        added = 0
        for key, counts in votes.items():
            if key in self._mappings:
                continue
            (name, parent), n = max(counts.items(), key=lambda item: item[1])
            self._mappings[key] = {
                "category_name": name,
                "parent_category": parent,
                "count": n,
                "example": examples.get(key, key),
            }
            added += 1
        if added:
            self._save()
            logger.info("Bootstrapped %s learned merchant mappings", added)
        return added

    def apply_to_similar(
        self,
        transactions: List[Transaction],
        description: str,
        category: Category,
        skip_id: Optional[str] = None,
    ) -> List[Transaction]:
        """Return a new list with same-merchant rows updated to `category`."""
        key = normalize_merchant(description)
        if len(key) < MIN_KEY_LENGTH:
            return transactions
        updated = []
        for txn in transactions:
            if skip_id and txn.id == skip_id:
                updated.append(txn)
                continue
            if normalize_merchant(txn.description) != key:
                updated.append(txn)
                continue
            if txn.category is not None and txn.category.name == category.name:
                updated.append(txn)
                continue
            updated.append(txn.model_copy(update={"category": category}))
        return updated

    def mappings(self) -> Dict[str, dict]:
        return dict(self._mappings)
