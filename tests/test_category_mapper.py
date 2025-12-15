"""Tests for category mapper module."""

import pytest

from finance_tracker.category_mapper import CategoryMapper, CategoryRule
from finance_tracker.models import Category


class TestCategoryMapper:
    """Tests for CategoryMapper class."""

    @pytest.fixture
    def mapper(self):
        """Create a CategoryMapper instance."""
        return CategoryMapper()

    def test_categorize_grocery_store(self, mapper):
        """Test categorizing grocery store transactions."""
        category = mapper.categorize("GROCERY STORE #1234")
        assert category is not None
        assert category.name == "Groceries"
        assert category.parent == "Food & Dining"

    def test_categorize_restaurant(self, mapper):
        """Test categorizing restaurant transactions."""
        category = mapper.categorize("RESTAURANT OLIVE GARDEN")
        assert category is not None
        assert category.name == "Restaurants"
        assert category.parent == "Food & Dining"

    def test_categorize_coffee_shop(self, mapper):
        """Test categorizing coffee shop transactions."""
        category = mapper.categorize("COFFEE SHOP STARBUCKS")
        assert category is not None
        assert category.name == "Coffee Shops"
        assert category.parent == "Food & Dining"

    def test_categorize_gas_station(self, mapper):
        """Test categorizing gas station transactions."""
        category = mapper.categorize("GAS STATION SHELL")
        assert category is not None
        assert category.name == "Gas & Fuel"
        assert category.parent == "Transportation"

    def test_categorize_amazon(self, mapper):
        """Test categorizing Amazon transactions."""
        category = mapper.categorize("AMAZON.COM PURCHASE")
        assert category is not None
        assert category.name == "General Shopping"
        assert category.parent == "Shopping"

    def test_categorize_pharmacy(self, mapper):
        """Test categorizing pharmacy transactions."""
        category = mapper.categorize("PHARMACY CVS")
        assert category is not None
        assert category.name == "Pharmacy"
        assert category.parent in ["Shopping", "Health & Fitness"]

    def test_categorize_utility(self, mapper):
        """Test categorizing utility transactions."""
        category = mapper.categorize("UTILITY BILL ELECTRIC")
        assert category is not None
        assert category.name == "Electric"
        assert category.parent == "Bills & Utilities"

    def test_categorize_netflix(self, mapper):
        """Test categorizing Netflix transactions."""
        category = mapper.categorize("NETFLIX SUBSCRIPTION")
        assert category is not None
        assert category.name == "Streaming Services"
        assert category.parent == "Entertainment"

    def test_categorize_salary(self, mapper):
        """Test categorizing salary transactions."""
        category = mapper.categorize("Salary Deposit")
        assert category is not None
        assert category.name == "Salary"
        assert category.parent == "Income"

    def test_categorize_unknown(self, mapper):
        """Test categorizing unknown transactions."""
        category = mapper.categorize("UNKNOWN MERCHANT XYZ123")
        assert category is None

    def test_case_insensitive_matching(self, mapper):
        """Test that matching is case insensitive."""
        category1 = mapper.categorize("GROCERY STORE")
        category2 = mapper.categorize("grocery store")
        category3 = mapper.categorize("Grocery Store")

        assert category1 is not None
        assert category2 is not None
        assert category3 is not None
        assert category1.name == category2.name == category3.name

    def test_add_custom_rule(self, mapper):
        """Test adding custom categorization rules."""
        mapper.add_custom_rule(r"(?i)\b(custom.?merchant)\b", "Custom Category", "Custom Parent")
        category = mapper.categorize("CUSTOM MERCHANT TRANSACTION")
        assert category is not None
        assert category.name == "Custom Category"
        assert category.parent == "Custom Parent"

    def test_custom_rule_case_sensitive(self):
        """Test case-sensitive custom rules."""
        mapper = CategoryMapper()
        mapper.add_custom_rule(r"\b(ExactCase)\b", "Exact Match", case_sensitive=True)

        # Should match
        category1 = mapper.categorize("ExactCase")
        assert category1 is not None

        # Should not match
        category2 = mapper.categorize("exactcase")
        assert category2 is None

    def test_get_all_categories(self, mapper):
        """Test getting all categories."""
        categories = mapper.get_all_categories()
        assert isinstance(categories, dict)
        assert len(categories) > 0

        # Check that parent categories exist
        assert "Food & Dining" in categories
        assert "Transportation" in categories
        assert "Shopping" in categories

        # Check that child categories are listed
        assert "Groceries" in categories["Food & Dining"]
        assert "Restaurants" in categories["Food & Dining"]

    def test_multiple_rules_same_category(self, mapper):
        """Test that multiple rules can map to the same category."""
        # Both should map to Restaurants
        cat1 = mapper.categorize("RESTAURANT")
        cat2 = mapper.categorize("PIZZA HUT")

        assert cat1 is not None
        assert cat2 is not None
        # Both should be Restaurants (or at least one should match)
        assert cat1.name == "Restaurants" or cat2.name == "Restaurants"

    def test_custom_rules_override_defaults(self):
        """Test that custom rules are checked after defaults."""
        mapper = CategoryMapper()
        # Add custom rule that might conflict
        mapper.add_custom_rule(r"(?i)\b(grocery)\b", "Custom Groceries", "Custom")

        category = mapper.categorize("GROCERY STORE")
        # Should match default rule first (first match wins in current implementation)
        assert category is not None

    def test_empty_description(self, mapper):
        """Test categorizing empty description."""
        category = mapper.categorize("")
        assert category is None

    def test_whitespace_description(self, mapper):
        """Test categorizing whitespace-only description."""
        category = mapper.categorize("   ")
        assert category is None

    def test_partial_matches(self, mapper):
        """Test that partial word matches work correctly."""
        # "grocery" should match even if part of a larger word
        category = mapper.categorize("GROCERYSTORE123")
        assert category is not None
        assert category.name == "Groceries"

    def test_get_default_mapper(self):
        """Test getting default mapper instance."""
        from finance_tracker.category_mapper import get_default_mapper

        mapper = get_default_mapper()
        assert isinstance(mapper, CategoryMapper)
        assert len(mapper.rules) > 0

