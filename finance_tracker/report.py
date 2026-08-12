"""
Monthly HTML and PDF reports with month-over-month comparison.
"""

from __future__ import annotations

import html
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from finance_tracker.analyzer import SpendingAnalyzer
from finance_tracker.models import CashFlowSummary, MonthlySummary, MonthOverMonthComparison
from finance_tracker.secure_store import chmod_private, ensure_secure_dir


def _money(value: Decimal) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def _pct(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.1f}%"


def _delta_class(delta: Decimal) -> str:
    if delta > 0:
        return "up"
    if delta < 0:
        return "down"
    return "flat"


def render_html_report(
    summary: MonthlySummary,
    mom: MonthOverMonthComparison,
    cash_flow: Optional[CashFlowSummary] = None,
) -> str:
    """Return a self-contained HTML monthly report (no external assets)."""
    period = f"{summary.year}-{summary.month:02d}"
    prev = f"{mom.previous_year}-{mom.previous_month:02d}"
    savings = f"{summary.savings_rate:.1f}%" if summary.savings_rate is not None else "n/a"

    category_rows = []
    for item in mom.category_deltas:
        category_rows.append(
            "<tr>"
            f"<td>{html.escape(item.category)}</td>"
            f"<td>{_money(item.current)}</td>"
            f"<td>{_money(item.previous)}</td>"
            f"<td class='{_delta_class(item.delta)}'>{_money(item.delta)} ({_pct(item.percent_change)})</td>"
            "</tr>"
        )
    if not category_rows:
        category_rows.append("<tr><td colspan='4'>No categorized expenses.</td></tr>")

    cash_section = ""
    if cash_flow:
        cash_section = f"""
        <h2>Cash flow</h2>
        <table>
          <tr><th>Operating income</th><td>{_money(cash_flow.income)}</td></tr>
          <tr><th>Operating expenses</th><td>{_money(cash_flow.expenses)}</td></tr>
          <tr><th>Net operating</th><td>{_money(cash_flow.net_operating)}</td></tr>
          <tr><th>Transfers in</th><td>{_money(cash_flow.transfers_in)}</td></tr>
          <tr><th>Transfers out</th><td>{_money(cash_flow.transfers_out)}</td></tr>
          <tr><th>Net cash</th><td>{_money(cash_flow.net_cash)}</td></tr>
        </table>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Finance report {period}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif;
           margin: 32px; color: #111; }}
    h1 {{ margin-bottom: 4px; }}
    .sub {{ color: #555; margin-bottom: 24px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
    th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #ddd; }}
    th {{ background: #f4f4f4; }}
    .up {{ color: #b45309; }}
    .down {{ color: #047857; }}
    .flat {{ color: #555; }}
    .totals td {{ font-weight: 600; }}
  </style>
</head>
<body>
  <h1>Monthly report — {period}</h1>
  <p class="sub">Compared with {prev}. Generated {date.today().isoformat()}.</p>

  <h2>Totals</h2>
  <table class="totals">
    <tr><th></th><th>{period}</th><th>{prev}</th><th>Change</th></tr>
    <tr>
      <td>Income</td><td>{_money(mom.income.current)}</td>
      <td>{_money(mom.income.previous)}</td>
      <td class="{_delta_class(mom.income.delta)}">{_money(mom.income.delta)} ({_pct(mom.income.percent_change)})</td>
    </tr>
    <tr>
      <td>Expenses</td><td>{_money(mom.expenses.current)}</td>
      <td>{_money(mom.expenses.previous)}</td>
      <td class="{_delta_class(mom.expenses.delta)}">{_money(mom.expenses.delta)} ({_pct(mom.expenses.percent_change)})</td>
    </tr>
    <tr>
      <td>Net</td><td>{_money(mom.net.current)}</td>
      <td>{_money(mom.net.previous)}</td>
      <td class="{_delta_class(mom.net.delta)}">{_money(mom.net.delta)} ({_pct(mom.net.percent_change)})</td>
    </tr>
    <tr>
      <td>Savings rate</td><td>{savings}</td>
      <td>{"n/a" if mom.savings_rate_previous is None else f"{mom.savings_rate_previous:.1f}%"}</td>
      <td></td>
    </tr>
    <tr>
      <td>Transactions</td><td>{mom.transaction_count_current}</td>
      <td>{mom.transaction_count_previous}</td>
      <td></td>
    </tr>
  </table>

  {cash_section}

  <h2>Category month-over-month</h2>
  <table>
    <tr><th>Category</th><th>{period}</th><th>{prev}</th><th>Change</th></tr>
    {''.join(category_rows)}
  </table>
</body>
</html>
"""


def write_html_report(output_file: Path, html_body: str) -> Path:
    output_file = Path(output_file)
    ensure_secure_dir(output_file.parent)
    output_file.write_text(html_body, encoding="utf-8")
    chmod_private(output_file)
    return output_file


def write_pdf_report(
    output_file: Path,
    summary: MonthlySummary,
    mom: MonthOverMonthComparison,
    cash_flow: Optional[CashFlowSummary] = None,
) -> Path:
    """Write a simple PDF of the monthly report using fpdf2."""
    from fpdf import FPDF

    output_file = Path(output_file)
    ensure_secure_dir(output_file.parent)

    period = f"{summary.year}-{summary.month:02d}"
    prev = f"{mom.previous_year}-{mom.previous_month:02d}"
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Monthly report {period}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Compared with {prev}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    def row(label: str, current: str, previous: str, change: str) -> None:
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(50, 8, label)
        pdf.cell(40, 8, current)
        pdf.cell(40, 8, previous)
        pdf.cell(0, 8, change, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(50, 8, "")
    pdf.cell(40, 8, period)
    pdf.cell(40, 8, prev)
    pdf.cell(0, 8, "Change", new_x="LMARGIN", new_y="NEXT")
    row(
        "Income",
        _money(mom.income.current),
        _money(mom.income.previous),
        f"{_money(mom.income.delta)} ({_pct(mom.income.percent_change)})",
    )
    row(
        "Expenses",
        _money(mom.expenses.current),
        _money(mom.expenses.previous),
        f"{_money(mom.expenses.delta)} ({_pct(mom.expenses.percent_change)})",
    )
    row(
        "Net",
        _money(mom.net.current),
        _money(mom.net.previous),
        f"{_money(mom.net.delta)} ({_pct(mom.net.percent_change)})",
    )

    if cash_flow:
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Cash flow", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, f"Operating net: {_money(cash_flow.net_operating)}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"Net cash: {_money(cash_flow.net_cash)}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Category month-over-month", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(60, 7, "Category")
    pdf.cell(40, 7, period)
    pdf.cell(40, 7, prev)
    pdf.cell(0, 7, "Change", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for item in mom.category_deltas[:25]:
        name = item.category[:28]
        pdf.cell(60, 7, name)
        pdf.cell(40, 7, _money(item.current))
        pdf.cell(40, 7, _money(item.previous))
        pdf.cell(
            0,
            7,
            f"{_money(item.delta)} ({_pct(item.percent_change)})",
            new_x="LMARGIN",
            new_y="NEXT",
        )

    pdf.output(str(output_file))
    chmod_private(output_file)
    return output_file


def generate_monthly_report(
    analyzer: SpendingAnalyzer,
    year: int,
    month: int,
    output_dir: Path,
    formats: tuple[str, ...] = ("html", "pdf"),
) -> dict:
    """Write HTML and/or PDF reports for a month. Returns output paths."""
    summary = analyzer.get_monthly_summary(year, month)
    mom = analyzer.get_month_over_month(year, month)
    cash_flow = analyzer.get_cash_flow(year, month)
    output_dir = Path(output_dir)
    ensure_secure_dir(output_dir)
    stem = f"report-{year}-{month:02d}"
    paths = {}
    if "html" in formats:
        html_body = render_html_report(summary, mom, cash_flow)
        paths["html"] = str(write_html_report(output_dir / f"{stem}.html", html_body))
    if "pdf" in formats:
        paths["pdf"] = str(
            write_pdf_report(output_dir / f"{stem}.pdf", summary, mom, cash_flow)
        )
    return {"period": f"{year}-{month:02d}", "files": paths, "mom": mom, "summary": summary}
