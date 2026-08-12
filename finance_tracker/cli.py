"""
Command-line interface for finance tracker.

This module provides a Click-based CLI with multiple subcommands for different
operations. The CLI integrates with all core components to provide a complete
command-line experience.

Available Commands:
    - import-csv: Import and process CSV files
    - summary: Show monthly spending summaries
    - categories: Display top spending categories
    - uncategorized: List uncategorized transactions
    - recategorize: Recategorize all stored transactions
    - export: Export transactions to JSON/CSV
    - stats: Show overall statistics
    - list: List stored transactions (includes IDs)
    - edit: Edit a stored transaction by ID
    - delete: Delete a stored transaction by ID
    - budget: Manage category budgets (set, list, delete, status, alerts)
    - recurring: Detect and mark recurring transactions
    - report / review: Local HTML/PDF monthly report with MoM
    - cashflow / forecast: Operating vs transfers; next-month forecast
    - schedule: launchd agent for month-end report (macOS)
    - account / goal: Investments, debts, net worth, and targets

The CLI respects configuration settings and provides helpful error messages.

Example Usage:
    $ finance-tracker import-csv bank_statement.csv
    $ finance-tracker summary --year 2024 --month 1
    $ finance-tracker categories --limit 10
    $ finance-tracker export transactions.json --format json
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

import click

from finance_tracker.budget_tracker import BudgetRepository, BudgetTracker
from finance_tracker.config import get_config
from finance_tracker.logging_config import setup_logging
from finance_tracker.models import Budget, Category
from finance_tracker.recurring_detector import RecurringTransactionDetector
from finance_tracker.search_filter import TransactionSearchFilter
from finance_tracker.transaction_editor import TransactionEditor
from finance_tracker.workflow import FinanceTrackerWorkflow

logger = logging.getLogger(__name__)


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    help="Data directory for storing transactions",
)
@click.pass_context
def cli(ctx: click.Context, config: Optional[Path], verbose: bool, data_dir: Optional[Path]):
    """Finance Tracker - Track and categorize your spending."""
    # Load configuration
    cfg = get_config(config)
    if data_dir:
        cfg.set("data.directory", str(data_dir))

    # Setup logging
    log_level = cfg.get("logging.level", "INFO")
    log_file = cfg.get("logging.file")
    if log_file:
        log_file = Path(log_file)
    setup_logging(level=log_level, log_file=log_file, verbose=verbose)

    # Store config in context
    ctx.ensure_object(dict)
    ctx.obj["config"] = cfg
    ctx.obj["data_dir"] = Path(cfg.get("data.directory", Path.home() / ".finance-tracker"))


@cli.command()
@click.argument("csv_file", type=click.Path(exists=True, path_type=Path))
@click.option("--account", help="Account identifier for transactions")
@click.option(
    "--no-categorize", is_flag=True, help="Skip automatic categorization"
)
@click.option(
    "--overwrite", is_flag=True, help="Overwrite existing categories"
)
@click.option(
    "--no-duplicate-check", is_flag=True, help="Skip duplicate detection"
)
@click.pass_context
def import_csv(
    ctx: click.Context,
    csv_file: Path,
    account: Optional[str],
    no_categorize: bool,
    overwrite: bool,
    no_duplicate_check: bool,
):
    """Import transactions from a CSV file."""
    cfg = ctx.obj["config"]
    data_dir = ctx.obj["data_dir"]

    auto_categorize = not no_categorize and cfg.get("categorization.auto_categorize", True)
    check_duplicates = not no_duplicate_check and cfg.get("duplicates.check_on_import", True)
    skip_duplicates = cfg.get("duplicates.skip_duplicates", True)

    click.echo(f"Importing transactions from {csv_file}...")

    workflow = FinanceTrackerWorkflow(data_dir=data_dir, account=account)
    transactions, stats = workflow.process_csv_file(
        csv_file,
        auto_categorize=auto_categorize,
        overwrite_categories=overwrite,
        check_duplicates=check_duplicates,
        skip_duplicates=skip_duplicates,
    )

    click.echo(f"\n✓ Imported {stats['new_transactions']} transactions")
    if stats.get("duplicates_found", 0) > 0:
        click.echo(f"  Found {stats['duplicates_found']} duplicates")
        if stats.get("duplicates_skipped", 0) > 0:
            click.echo(f"  Skipped {stats['duplicates_skipped']} duplicates")

    if auto_categorize and "categorized" in stats:
        click.echo(f"  Categorized: {stats['categorized']}/{stats.get('total_parsed', 0)}")
        click.echo(f"  Categorization rate: {stats.get('categorization_rate', 0):.1f}%")


@cli.command()
@click.option("--year", type=int, help="Filter by year")
@click.option("--month", type=int, help="Filter by month (requires --year)")
@click.pass_context
def summary(ctx: click.Context, year: Optional[int], month: Optional[int]):
    """Show spending summary."""
    data_dir = ctx.obj["data_dir"]

    if month and not year:
        click.echo("Error: --month requires --year", err=True)
        return

    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    analyzer = workflow.analyze_spending(year=year, month=month)

    if month and year:
        # Show monthly summary
        summary_data = analyzer.get_monthly_summary(year, month)
        click.echo(f"\nMonthly Summary - {year}-{month:02d}")
        click.echo("=" * 50)
        click.echo(f"Total Income:    ${summary_data.total_income:,.2f}")
        click.echo(f"Total Expenses:  ${summary_data.total_expenses:,.2f}")
        click.echo(f"Net Amount:     ${summary_data.net_amount:,.2f}")
        if summary_data.savings_rate:
            click.echo(f"Savings Rate:   {summary_data.savings_rate:.1f}%")
        click.echo(f"Transactions:   {summary_data.transaction_count}")

        if summary_data.category_breakdown:
            click.echo("\nCategory Breakdown:")
            for category, amount in sorted(
                summary_data.category_breakdown.items(), key=lambda x: x[1], reverse=True
            ):
                click.echo(f"  {category:20s} ${amount:>10,.2f}")

        mom = analyzer.get_month_over_month(year, month)
        _print_mom(mom)
    else:
        # Show all monthly summaries
        summaries = analyzer.get_all_monthly_summaries()
        if not summaries:
            click.echo("No transactions found.")
            return

        click.echo("\nMonthly Summaries")
        click.echo("=" * 80)
        click.echo(f"{'Month':<12} {'Income':>12} {'Expenses':>12} {'Net':>12} {'Savings':>10}")
        click.echo("-" * 80)

        for s in summaries:
            savings = f"{s.savings_rate:.1f}%" if s.savings_rate else "N/A"
            click.echo(
                f"{s.year}-{s.month:02d:<8} "
                f"${s.total_income:>10,.2f} "
                f"${s.total_expenses:>10,.2f} "
                f"${s.net_amount:>10,.2f} "
                f"{savings:>10}"
            )


@cli.command()
@click.option("--limit", default=10, help="Number of top categories to show")
@click.pass_context
def categories(ctx: click.Context, limit: int):
    """Show top spending categories."""
    data_dir = ctx.obj["data_dir"]

    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    analyzer = workflow.analyze_spending()
    top_categories = analyzer.get_top_categories(limit=limit)

    if not top_categories:
        click.echo("No categorized transactions found.")
        return

    click.echo(f"\nTop {limit} Spending Categories")
    click.echo("=" * 80)
    click.echo(f"{'Category':<30} {'Total':>15} {'Avg':>15} {'Count':>10} {'%':>8}")
    click.echo("-" * 80)

    for pattern in top_categories:
        percentage = f"{pattern.percentage_of_total:.1f}%" if pattern.percentage_of_total else "N/A"
        click.echo(
            f"{pattern.category:<30} "
            f"${pattern.total_amount:>14,.2f} "
            f"${pattern.average_transaction:>14,.2f} "
            f"{pattern.transaction_count:>10} "
            f"{percentage:>8}"
        )


@cli.command()
@click.pass_context
def uncategorized(ctx: click.Context):
    """Show uncategorized transactions."""
    data_dir = ctx.obj["data_dir"]

    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    uncategorized_txns = workflow.get_uncategorized_transactions()

    if not uncategorized_txns:
        click.echo("All transactions are categorized!")
        return

    click.echo(f"\nFound {len(uncategorized_txns)} uncategorized transactions:")
    click.echo("=" * 100)
    click.echo(f"{'ID':<36} {'Date':<12} {'Description':<40} {'Amount':>12}")
    click.echo("-" * 100)

    for txn in uncategorized_txns[:50]:  # Show first 50
        click.echo(
            f"{txn.id or 'N/A':<36} {txn.date} {_truncate(txn.description, 40):<40} "
            f"${txn.absolute_amount:>10,.2f}"
        )

    if len(uncategorized_txns) > 50:
        click.echo(f"\n... and {len(uncategorized_txns) - 50} more")


@cli.command()
@click.option("--overwrite", is_flag=True, help="Overwrite existing categories")
@click.pass_context
def recategorize(ctx: click.Context, overwrite: bool):
    """Recategorize all stored transactions."""
    data_dir = ctx.obj["data_dir"]

    click.echo("Recategorizing all transactions...")

    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    stats = workflow.recategorize_all(overwrite=overwrite)

    click.echo(f"\n✓ Recategorized {stats['total']} transactions")
    click.echo(f"  Categorized: {stats['categorized']}")
    click.echo(f"  Uncategorized: {stats['uncategorized']}")
    click.echo(f"  Rate: {stats['categorization_rate']:.1f}%")


@cli.command()
@click.argument("output_file", type=click.Path(path_type=Path))
@click.option("--format", "export_format", type=click.Choice(["json", "csv"]), default="json")
@click.pass_context
def export(ctx: click.Context, output_file: Path, export_format: str):
    """Export transactions to JSON or CSV file."""
    data_dir = ctx.obj["data_dir"]

    workflow = FinanceTrackerWorkflow(data_dir=data_dir)

    if export_format == "json":
        workflow.storage.export_transactions_json(output_file)
    else:
        workflow.storage.export_transactions_csv(output_file)

    click.echo(f"✓ Exported transactions to {output_file}")


@cli.command()
@click.pass_context
def stats(ctx: click.Context):
    """Show general statistics."""
    data_dir = ctx.obj["data_dir"]

    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    analyzer = workflow.analyze_spending()

    total_income = analyzer.get_total_income()
    total_expenses = analyzer.get_total_expenses()
    net_amount = analyzer.get_net_amount()

    click.echo("\nOverall Statistics")
    click.echo("=" * 50)
    click.echo(f"Total Income:   ${total_income:,.2f}")
    click.echo(f"Total Expenses: ${total_expenses:,.2f}")
    click.echo(f"Net Amount:    ${net_amount:,.2f}")

    if total_income > 0:
        savings_rate = (net_amount / total_income) * 100
        click.echo(f"Savings Rate:  {savings_rate:.1f}%")


def _truncate(text: str, width: int) -> str:
    """Truncate text to width, adding ellipsis when needed."""
    if len(text) <= width:
        return text
    return text[: width - 3] + "..."


def _print_transaction_table(transactions, limit: Optional[int] = None) -> None:
    """Print a table of transactions including IDs for edit/delete."""
    rows = transactions[:limit] if limit is not None else transactions
    click.echo(f"{'ID':<36} {'Date':<12} {'Description':<32} {'Category':<18} {'Amount':>12}")
    click.echo("-" * 114)
    for txn in rows:
        category = txn.category.name if txn.category else "Uncategorized"
        click.echo(
            f"{txn.id or 'N/A':<36} "
            f"{txn.date.isoformat():<12} "
            f"{_truncate(txn.description, 32):<32} "
            f"{_truncate(category, 18):<18} "
            f"${txn.amount:>10,.2f}"
        )


@cli.command("list")
@click.option("--limit", default=50, help="Maximum number of transactions to show")
@click.option("--query", help="Search description and notes")
@click.option("--category", help="Filter by category name")
@click.option("--account", help="Filter by account")
@click.option("--type", "transaction_type", type=click.Choice(["debit", "credit", "transfer"]))
@click.option("--recurring", is_flag=True, help="Show only recurring transactions")
@click.pass_context
def list_transactions(
    ctx: click.Context,
    limit: int,
    query: Optional[str],
    category: Optional[str],
    account: Optional[str],
    transaction_type: Optional[str],
    recurring: bool,
):
    """List stored transactions (includes IDs for edit/delete)."""
    data_dir = ctx.obj["data_dir"]
    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    transactions = workflow.storage.transaction_repo.load_all()
    transactions.sort(key=lambda t: t.date, reverse=True)

    searcher = TransactionSearchFilter(transactions)
    results = searcher.search(
        query=query,
        category=category,
        account=account,
        transaction_type=transaction_type,
        is_recurring=True if recurring else None,
    )

    if not results:
        click.echo("No transactions found.")
        return

    click.echo(f"\nShowing {min(limit, len(results))} of {len(results)} transactions")
    click.echo("=" * 114)
    _print_transaction_table(results, limit=limit)


@cli.command()
@click.argument("transaction_id")
@click.option("--description", help="New description")
@click.option("--amount", type=str, help="New amount (negative for expenses)")
@click.option("--date", "txn_date", help="New date (YYYY-MM-DD)")
@click.option("--category", help="New category name")
@click.option("--parent", help="Parent category name")
@click.option("--notes", help="New notes")
@click.pass_context
def edit(
    ctx: click.Context,
    transaction_id: str,
    description: Optional[str],
    amount: Optional[str],
    txn_date: Optional[str],
    category: Optional[str],
    parent: Optional[str],
    notes: Optional[str],
):
    """Edit a stored transaction by ID."""
    if not any([description, amount, txn_date, category, notes]):
        click.echo("Error: provide at least one field to change.", err=True)
        raise SystemExit(1)

    data_dir = ctx.obj["data_dir"]
    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    editor = TransactionEditor(workflow.storage.transaction_repo)

    parsed_amount = Decimal(amount) if amount is not None else None
    parsed_date = datetime.fromisoformat(txn_date).date() if txn_date else None
    parsed_category = None
    if category:
        parsed_category = Category(name=category, parent=parent)

    updated = editor.edit_transaction(
        transaction_id=transaction_id,
        description=description,
        amount=parsed_amount,
        date=parsed_date,
        category=parsed_category,
        notes=notes,
    )
    if not updated:
        click.echo(f"Error: transaction {transaction_id} not found.", err=True)
        raise SystemExit(1)

    click.echo(f"✓ Updated transaction {updated.id}")
    click.echo(f"  {updated.date}  {_truncate(updated.description, 40)}  ${updated.amount:,.2f}")
    if updated.category:
        click.echo(f"  Category: {updated.category.name}")


@cli.command("delete")
@click.argument("transaction_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_transaction(ctx: click.Context, transaction_id: str, yes: bool):
    """Delete a stored transaction by ID."""
    data_dir = ctx.obj["data_dir"]
    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    editor = TransactionEditor(workflow.storage.transaction_repo)

    existing = workflow.storage.transaction_repo.get_by_id(transaction_id)
    if not existing:
        click.echo(f"Error: transaction {transaction_id} not found.", err=True)
        raise SystemExit(1)

    if not yes and not click.confirm(f"Delete '{existing.description}' ({existing.date})?"):
        click.echo("Cancelled.")
        return

    if editor.delete_transaction(transaction_id):
        click.echo(f"✓ Deleted transaction {transaction_id}")
    else:
        click.echo(f"Error: failed to delete {transaction_id}.", err=True)
        raise SystemExit(1)


@cli.group()
def budget():
    """Manage category budgets."""


@budget.command("set")
@click.argument("category_name")
@click.option("--year", type=int, help="Budget year (defaults to current year)")
@click.option("--month", type=int, help="Budget month 1-12 (defaults to current month)")
@click.option("--amount", required=True, type=str, help="Budget amount")
@click.option(
    "--alert-threshold",
    default="0.8",
    show_default=True,
    help="Alert when spending reaches this fraction of the budget (0-1)",
)
@click.option("--notes", help="Optional budget notes")
@click.pass_context
def budget_set(
    ctx: click.Context,
    category_name: str,
    year: Optional[int],
    month: Optional[int],
    amount: str,
    alert_threshold: str,
    notes: Optional[str],
):
    """Set a monthly budget for a category."""
    year = year or date.today().year
    month = month or date.today().month
    data_dir = ctx.obj["data_dir"]
    repo = BudgetRepository(data_dir)
    repo.save_budget(
        Budget(
            category_name=category_name,
            year=year,
            month=month,
            amount=Decimal(amount),
            alert_threshold=Decimal(alert_threshold),
            notes=notes,
        )
    )
    click.echo(f"✓ Set {category_name} budget for {year}-{month:02d} to ${Decimal(amount):,.2f}")


@budget.command("list")
@click.option("--year", type=int, help="Filter by year (defaults to current year)")
@click.option("--month", type=int, help="Filter by month (defaults to current month)")
@click.pass_context
def budget_list(ctx: click.Context, year: Optional[int], month: Optional[int]):
    """List budgets and spending status for a month."""
    year = year or date.today().year
    month = month or date.today().month
    data_dir = ctx.obj["data_dir"]
    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    transactions = workflow.storage.transaction_repo.load_all()
    tracker = BudgetTracker(transactions, BudgetRepository(data_dir))
    statuses = tracker.get_all_budget_statuses(year, month)

    if not statuses:
        click.echo(f"No budgets set for {year}-{month:02d}.")
        return

    click.echo(f"\nBudgets for {year}-{month:02d}")
    click.echo("=" * 80)
    click.echo(f"{'Category':<24} {'Budget':>12} {'Spent':>12} {'Remaining':>12} {'%':>8}")
    click.echo("-" * 80)
    for status in statuses:
        remaining = Decimal(status["remaining"])
        click.echo(
            f"{status['category_name']:<24} "
            f"${Decimal(status['budget']):>10,.2f} "
            f"${Decimal(status['spent']):>10,.2f} "
            f"${remaining:>10,.2f} "
            f"{status['percentage_spent']:>7.1f}%"
        )


@budget.command("status")
@click.argument("category_name")
@click.option("--year", type=int, help="Budget year (defaults to current year)")
@click.option("--month", type=int, help="Budget month (defaults to current month)")
@click.pass_context
def budget_status(
    ctx: click.Context, category_name: str, year: Optional[int], month: Optional[int]
):
    """Show budget status for a single category."""
    year = year or date.today().year
    month = month or date.today().month
    data_dir = ctx.obj["data_dir"]
    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    transactions = workflow.storage.transaction_repo.load_all()
    tracker = BudgetTracker(transactions, BudgetRepository(data_dir))
    status = tracker.get_budget_status(category_name, year, month)

    if not status.get("has_budget"):
        click.echo(f"No budget set for {category_name} in {year}-{month:02d}.")
        raise SystemExit(1)

    click.echo(f"\n{category_name} — {year}-{month:02d}")
    click.echo("=" * 40)
    click.echo(f"Budget:     ${Decimal(status['budget']):,.2f}")
    click.echo(f"Spent:      ${Decimal(status['spent']):,.2f}")
    click.echo(f"Remaining:  ${Decimal(status['remaining']):,.2f}")
    click.echo(f"Used:       {status['percentage_spent']:.1f}%")
    if status.get("over_budget"):
        click.echo("Status:     OVER BUDGET")
    elif status.get("should_alert"):
        click.echo("Status:     Alert threshold reached")
    else:
        click.echo("Status:     On track")


@budget.command("alerts")
@click.option("--year", type=int, help="Year (defaults to current year)")
@click.option("--month", type=int, help="Month (defaults to current month)")
@click.pass_context
def budget_alerts(ctx: click.Context, year: Optional[int], month: Optional[int]):
    """Show budget alerts for a month."""
    year = year or date.today().year
    month = month or date.today().month
    data_dir = ctx.obj["data_dir"]
    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    transactions = workflow.storage.transaction_repo.load_all()
    tracker = BudgetTracker(transactions, BudgetRepository(data_dir))
    alerts = tracker.check_alerts(year, month)

    if not alerts:
        click.echo(f"No budget alerts for {year}-{month:02d}.")
        return

    click.echo(f"\nBudget alerts for {year}-{month:02d}")
    click.echo("=" * 60)
    for alert in alerts:
        click.echo(f"  {alert['category']}: {alert['message']}")


@budget.command("delete")
@click.argument("category_name")
@click.option("--year", type=int, required=True, help="Budget year")
@click.option("--month", type=int, required=True, help="Budget month")
@click.pass_context
def budget_delete(ctx: click.Context, category_name: str, year: int, month: int):
    """Delete a category budget for a month."""
    data_dir = ctx.obj["data_dir"]
    repo = BudgetRepository(data_dir)
    if repo.delete_budget(category_name, year, month):
        click.echo(f"✓ Deleted {category_name} budget for {year}-{month:02d}")
    else:
        click.echo(f"Error: no budget found for {category_name} in {year}-{month:02d}.", err=True)
        raise SystemExit(1)


@cli.group()
def recurring():
    """Detect and mark recurring transactions."""


@recurring.command("detect")
@click.option("--min-occurrences", default=3, show_default=True, help="Minimum repeats to flag")
@click.pass_context
def recurring_detect(ctx: click.Context, min_occurrences: int):
    """Detect recurring transaction patterns."""
    data_dir = ctx.obj["data_dir"]
    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    transactions = workflow.storage.transaction_repo.load_all()
    detector = RecurringTransactionDetector(transactions)
    found = detector.detect_recurring(min_occurrences=min_occurrences)

    if not found:
        click.echo("No recurring patterns detected.")
        return

    click.echo(f"\nDetected {len(found)} recurring pattern(s)")
    click.echo("=" * 90)
    click.echo(f"{'Description':<32} {'Freq':<10} {'Amount':>12} {'Count':>8} {'Conf':>8}")
    click.echo("-" * 90)
    for item in found:
        click.echo(
            f"{_truncate(item.description_pattern, 32):<32} "
            f"{item.frequency:<10} "
            f"${item.amount:>10,.2f} "
            f"{item.transaction_count:>8} "
            f"{item.confidence:>7.0%}"
        )


@recurring.command("mark")
@click.option("--min-occurrences", default=3, show_default=True, help="Minimum repeats to flag")
@click.pass_context
def recurring_mark(ctx: click.Context, min_occurrences: int):
    """Mark matching stored transactions as recurring."""
    data_dir = ctx.obj["data_dir"]
    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    transactions = workflow.storage.transaction_repo.load_all()
    detector = RecurringTransactionDetector(transactions)
    found = detector.detect_recurring(min_occurrences=min_occurrences)
    if not found:
        click.echo("No recurring patterns detected.")
        return

    updated = detector.mark_recurring(found)
    workflow.storage.transaction_repo._save_all(updated)
    marked = sum(1 for t in updated if t.is_recurring)
    click.echo(f"✓ Marked {marked} transaction(s) as recurring ({len(found)} pattern(s))")


def _fmt_pct(value) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.1f}%"


def _print_mom(mom) -> None:
    """Print month-over-month totals and category deltas."""
    click.echo(
        f"\nMonth-over-month vs {mom.previous_year}-{mom.previous_month:02d}"
    )
    click.echo("=" * 72)
    click.echo(f"{'':16} {'Current':>14} {'Previous':>14} {'Delta':>14} {'%':>10}")
    click.echo("-" * 72)
    for label, delta in (
        ("Income", mom.income),
        ("Expenses", mom.expenses),
        ("Net", mom.net),
    ):
        click.echo(
            f"{label:16} ${delta.current:>12,.2f} ${delta.previous:>12,.2f} "
            f"${delta.delta:>12,.2f} {_fmt_pct(delta.percent_change):>10}"
        )
    if mom.category_deltas:
        click.echo("\nCategory changes:")
        for item in mom.category_deltas:
            click.echo(
                f"  {item.category:20s} ${item.current:>10,.2f}  "
                f"{_fmt_pct(item.percent_change):>8}  ({item.delta:+,.2f})"
            )


def _resolve_year_month(year, month, previous_month: bool):
    today = date.today()
    if previous_month:
        if today.month == 1:
            return today.year - 1, 12
        return today.year, today.month - 1
    return year or today.year, month or today.month


@cli.command()
@click.option("--year", type=int, help="Report year")
@click.option("--month", type=int, help="Report month (1-12)")
@click.option("--previous-month", is_flag=True, help="Use last calendar month")
@click.option("--pdf/--no-pdf", default=True, show_default=True)
@click.option("--html/--no-html", default=True, show_default=True)
@click.option("--notify", is_flag=True, help="Show a macOS notification when done")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="Where to write the report (default: data-dir/reports)",
)
@click.pass_context
def report(
    ctx: click.Context,
    year: Optional[int],
    month: Optional[int],
    previous_month: bool,
    pdf: bool,
    html: bool,
    notify: bool,
    output_dir: Optional[Path],
):
    """Generate a local HTML/PDF monthly report with MoM comparison."""
    from finance_tracker.notify import notify as send_notification
    from finance_tracker.report import generate_monthly_report

    year, month = _resolve_year_month(year, month, previous_month)
    data_dir = ctx.obj["data_dir"]
    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    analyzer = workflow.analyze_spending()
    dest = output_dir or (data_dir / "reports")
    formats = tuple(fmt for fmt, on in (("html", html), ("pdf", pdf)) if on)
    if not formats:
        click.echo("Error: enable --html and/or --pdf", err=True)
        raise SystemExit(1)

    result = generate_monthly_report(analyzer, year, month, dest, formats=formats)
    _print_mom(result["mom"])
    click.echo("\nWrote:")
    for kind, path in result["files"].items():
        click.echo(f"  {kind}: {path}")

    if notify:
        files = ", ".join(result["files"].values())
        sent = send_notification(
            "Finance Tracker",
            f"Monthly report for {year}-{month:02d} is ready. {files}",
        )
        if sent:
            click.echo("✓ Notification sent")
        else:
            click.echo("Notification not sent (macOS Notification Center only)")


@cli.command()
@click.option("--year", type=int)
@click.option("--month", type=int)
@click.option("--csv", "csv_file", type=click.Path(exists=True, path_type=Path))
@click.option("--notify", is_flag=True)
@click.pass_context
def review(
    ctx: click.Context,
    year: Optional[int],
    month: Optional[int],
    csv_file: Optional[Path],
    notify: bool,
):
    """Monthly review: optional import → uncategorized → summary/MoM → report."""
    from finance_tracker.notify import notify as send_notification
    from finance_tracker.report import generate_monthly_report

    year, month = _resolve_year_month(year, month, previous_month=False)
    data_dir = ctx.obj["data_dir"]
    workflow = FinanceTrackerWorkflow(data_dir=data_dir)

    click.echo(f"\nMonthly review — {year}-{month:02d}")
    click.echo("=" * 50)

    if csv_file:
        click.echo(f"\n1. Import {csv_file}")
        _, stats = workflow.process_csv_file(csv_file)
        click.echo(f"   Imported {stats['new_transactions']} new transactions")
    else:
        click.echo("\n1. Import skipped (pass --csv to import a statement)")

    analyzer = workflow.analyze_spending()
    month_txns = [
        t
        for t in workflow.storage.transaction_repo.load_all()
        if t.date.year == year and t.date.month == month
    ]
    uncategorized = [t for t in month_txns if t.category is None]
    click.echo(f"\n2. Uncategorized this month: {len(uncategorized)}")
    for txn in uncategorized[:15]:
        click.echo(
            f"   {txn.id or 'N/A':<36} {txn.date} {_truncate(txn.description, 32)} "
            f"${txn.absolute_amount:,.2f}"
        )
    if uncategorized:
        click.echo("   Fix with: finance-tracker edit <id> --category NAME")

    click.echo("\n3. Summary and month-over-month")
    summary_data = analyzer.get_monthly_summary(year, month)
    click.echo(f"   Income ${summary_data.total_income:,.2f}  "
               f"Expenses ${summary_data.total_expenses:,.2f}  "
               f"Net ${summary_data.net_amount:,.2f}")
    mom = analyzer.get_month_over_month(year, month)
    _print_mom(mom)

    cash = analyzer.get_cash_flow(year, month)
    click.echo(
        f"\n   Cash flow — operating net ${cash.net_operating:,.2f}, "
        f"net cash ${cash.net_cash:,.2f}"
    )

    click.echo("\n4. Report")
    result = generate_monthly_report(
        analyzer, year, month, data_dir / "reports", formats=("html", "pdf")
    )
    for kind, path in result["files"].items():
        click.echo(f"   {kind}: {path}")

    if notify:
        send_notification(
            "Finance Tracker",
            f"Review for {year}-{month:02d} complete. Net ${summary_data.net_amount:,.2f}.",
        )


@cli.command()
@click.option("--year", type=int)
@click.option("--month", type=int)
@click.pass_context
def cashflow(ctx: click.Context, year: Optional[int], month: Optional[int]):
    """Show operating cash flow vs transfers for a month."""
    year, month = _resolve_year_month(year, month, previous_month=False)
    workflow = FinanceTrackerWorkflow(data_dir=ctx.obj["data_dir"])
    cash = workflow.analyze_spending().get_cash_flow(year, month)
    click.echo(f"\nCash flow — {year}-{month:02d}")
    click.echo("=" * 40)
    click.echo(f"Operating income:   ${cash.income:,.2f}")
    click.echo(f"Operating expenses: ${cash.expenses:,.2f}")
    click.echo(f"Net operating:      ${cash.net_operating:,.2f}")
    click.echo(f"Transfers in:       ${cash.transfers_in:,.2f}")
    click.echo(f"Transfers out:      ${cash.transfers_out:,.2f}")
    click.echo(f"Net cash:           ${cash.net_cash:,.2f}")


@cli.command()
@click.option("--months", default=3, show_default=True)
@click.option("--category", help="Forecast one category instead of total expenses")
@click.pass_context
def forecast(ctx: click.Context, months: int, category: Optional[str]):
    """Forecast next-month spending (moving average)."""
    workflow = FinanceTrackerWorkflow(data_dir=ctx.obj["data_dir"])
    analyzer = workflow.analyze_spending()
    if category:
        item = analyzer.forecast_next_month(months=months, category_name=category)
        items = [item] if item else []
    else:
        items = analyzer.forecast_all_categories(months=months)
    if not items:
        click.echo("Not enough history to forecast.")
        return
    click.echo(f"\nForecast (moving average, last {months} month(s))")
    click.echo("=" * 60)
    for item in items:
        label = item.category or "Total expenses"
        click.echo(f"  {label:24s} ${item.predicted_amount:>10,.2f}")


@cli.group()
def schedule():
    """Install a launchd agent that runs the monthly report on the 1st."""


@schedule.command("install")
@click.pass_context
def schedule_install(ctx: click.Context):
    """Install the month-end report LaunchAgent (macOS)."""
    from finance_tracker.scheduler import install

    path = install(data_dir=ctx.obj["data_dir"])
    click.echo(f"✓ Installed {path}")
    click.echo("  Runs on the 1st of each month at 09:00 (offline, local report + notification).")


@schedule.command("uninstall")
def schedule_uninstall():
    """Remove the month-end report LaunchAgent."""
    from finance_tracker.scheduler import uninstall

    if uninstall():
        click.echo("✓ Uninstalled monthly report agent")
    else:
        click.echo("No agent was installed.")


@schedule.command("status")
def schedule_status():
    """Show whether the LaunchAgent is installed."""
    from finance_tracker.scheduler import status

    info = status()
    click.echo(f"Plist:     {info['plist']}")
    click.echo(f"Installed: {info['installed']}")
    click.echo(f"Loaded:    {info['loaded']}")


@cli.group()
def account():
    """Track checking, savings, credit, loans, and investments."""


@account.command("add")
@click.argument("name")
@click.option(
    "--type",
    "account_type",
    type=click.Choice(["checking", "savings", "credit_card", "loan", "investment", "cash"]),
    default="checking",
)
@click.option("--balance", default="0")
@click.option("--institution")
@click.pass_context
def account_add(ctx, name, account_type, balance, institution):
    """Add or update an account balance."""
    from finance_tracker.accounts import AccountRepository
    from finance_tracker.models import Account, AccountType

    repo = AccountRepository(ctx.obj["data_dir"])
    repo.upsert(
        Account(
            name=name,
            account_type=AccountType(account_type),
            balance=Decimal(balance),
            institution=institution,
        )
    )
    click.echo(f"✓ Saved account {name} ({account_type}) balance ${Decimal(balance):,.2f}")


@account.command("list")
@click.pass_context
def account_list(ctx):
    """List accounts and net worth."""
    from finance_tracker.accounts import AccountRepository

    repo = AccountRepository(ctx.obj["data_dir"])
    accounts = repo.load_all()
    if not accounts:
        click.echo("No accounts yet. Add one with: finance-tracker account add NAME --type investment")
        return
    click.echo(f"\n{'Name':<22} {'Type':<14} {'Balance':>14}")
    click.echo("-" * 52)
    for acct in accounts:
        click.echo(f"{acct.name:<22} {acct.account_type.value:<14} ${acct.balance:>12,.2f}")
    click.echo(f"\nNet worth: ${repo.net_worth():,.2f}")


@cli.group()
def goal():
    """Savings, spending, debt, and investment goals."""


@goal.command("add")
@click.argument("name")
@click.option(
    "--type",
    "goal_type",
    type=click.Choice(["savings", "spend_under", "debt_payoff", "investment"]),
    default="savings",
)
@click.option("--target", required=True)
@click.option("--current", default="0")
@click.option("--category")
@click.pass_context
def goal_add(ctx, name, goal_type, target, current, category):
    """Add a financial goal."""
    from finance_tracker.accounts import GoalRepository
    from finance_tracker.models import FinancialGoal, GoalType

    repo = GoalRepository(ctx.obj["data_dir"])
    created = repo.add(
        FinancialGoal(
            id="",
            name=name,
            goal_type=GoalType(goal_type),
            target_amount=Decimal(target),
            current_amount=Decimal(current),
            category=category,
        )
    )
    click.echo(f"✓ Goal {created.name} ({created.id})")


@goal.command("list")
@click.pass_context
def goal_list(ctx):
    """List goals and progress."""
    from finance_tracker.accounts import GoalRepository

    goals = GoalRepository(ctx.obj["data_dir"]).load_all()
    if not goals:
        click.echo("No goals yet.")
        return
    click.echo(f"\n{'Name':<22} {'Type':<14} {'Progress':>12} {'Target':>12}")
    click.echo("-" * 64)
    for item in goals:
        pct = f"{item.progress_percent:.0f}%" if item.progress_percent is not None else "n/a"
        click.echo(
            f"{item.name:<22} {item.goal_type.value:<14} {pct:>12} ${item.target_amount:>10,.2f}"
        )


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()

