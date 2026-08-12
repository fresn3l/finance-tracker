"""Tests for HTML/PDF monthly reports."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from finance_tracker.analyzer import SpendingAnalyzer
from finance_tracker.models import Category, Transaction, TransactionType
from finance_tracker.report import generate_monthly_report, render_html_report


def _two_months():
    return [
        Transaction(
            date=date(2024, 1, 2),
            amount=Decimal("3000.00"),
            description="Salary",
            transaction_type=TransactionType.CREDIT,
        ),
        Transaction(
            date=date(2024, 1, 5),
            amount=Decimal("-100.00"),
            description="GROCERY",
            transaction_type=TransactionType.DEBIT,
            category=Category(name="Groceries"),
        ),
        Transaction(
            date=date(2024, 2, 2),
            amount=Decimal("3000.00"),
            description="Salary",
            transaction_type=TransactionType.CREDIT,
        ),
        Transaction(
            date=date(2024, 2, 5),
            amount=Decimal("-150.00"),
            description="GROCERY",
            transaction_type=TransactionType.DEBIT,
            category=Category(name="Groceries"),
        ),
    ]


class TestMonthlyReport:
    def test_html_contains_mom_totals(self):
        analyzer = SpendingAnalyzer(_two_months())
        summary = analyzer.get_monthly_summary(2024, 2)
        mom = analyzer.get_month_over_month(2024, 2)
        html = render_html_report(summary, mom, analyzer.get_cash_flow(2024, 2))

        assert "Monthly report — 2024-02" in html
        assert "Compared with 2024-01" in html
        assert "Groceries" in html
        assert "$150.00" in html
        assert "Cash flow" in html
        assert "cdn." not in html.lower()
        assert "http" not in html.lower() or "http-equiv" in html.lower()

    def test_generate_html_and_pdf(self, tmp_path):
        analyzer = SpendingAnalyzer(_two_months())
        result = generate_monthly_report(
            analyzer, 2024, 2, tmp_path, formats=("html", "pdf")
        )
        html_path = Path(result["files"]["html"])
        pdf_path = Path(result["files"]["pdf"])
        assert html_path.exists()
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 100
        body = html_path.read_text(encoding="utf-8")
        assert "2024-02" in body
        assert "Groceries" in body
