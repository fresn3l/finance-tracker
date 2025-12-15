"""Web application using Eel for finance tracker."""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import eel

from finance_tracker.config import get_config
from finance_tracker.logging_config import setup_logging
from finance_tracker.workflow import FinanceTrackerWorkflow

logger = logging.getLogger(__name__)

# Global workflow instance
workflow: Optional[FinanceTrackerWorkflow] = None


def init_workflow(data_dir: Optional[Path] = None) -> None:
    """Initialize the workflow instance."""
    global workflow
    cfg = get_config()
    if data_dir is None:
        data_dir = Path(cfg.get("data.directory", Path.home() / ".finance-tracker"))
    workflow = FinanceTrackerWorkflow(data_dir=data_dir)
    logger.info(f"Initialized workflow with data directory: {data_dir}")


@eel.expose
def select_file() -> Optional[str]:
    """
    Open file dialog to select CSV file.

    Returns:
        Selected file path or None
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        root.destroy()
        return file_path if file_path else None
    except Exception as e:
        logger.error(f"Error selecting file: {e}", exc_info=True)
        return None


@eel.expose
def import_csv_file(
    file_path: str,
    account: Optional[str] = None,
    auto_categorize: bool = True,
    overwrite: bool = False,
    check_duplicates: bool = True,
    skip_duplicates: bool = True,
) -> Dict:
    """
    Import a CSV file.

    Args:
        file_path: Path to CSV file
        account: Optional account identifier
        auto_categorize: Whether to auto-categorize
        overwrite: Whether to overwrite existing categories
        check_duplicates: Whether to check for duplicates
        skip_duplicates: Whether to skip duplicates

    Returns:
        Dictionary with import statistics
    """
    if workflow is None:
        init_workflow()

    try:
        csv_path = Path(file_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        transactions, stats = workflow.process_csv_file(
            csv_path,
            auto_categorize=auto_categorize,
            overwrite_categories=overwrite,
            check_duplicates=check_duplicates,
            skip_duplicates=skip_duplicates,
        )

        return {
            "success": True,
            "new_transactions": stats["new_transactions"],
            "duplicates_found": stats.get("duplicates_found", 0),
            "categorized": stats.get("categorized", 0),
            "categorization_rate": stats.get("categorization_rate", 0),
        }
    except Exception as e:
        logger.error(f"Error importing CSV: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@eel.expose
def get_transactions(page: int = 1, per_page: int = 50) -> List[Dict]:
    """
    Get paginated transactions.

    Args:
        page: Page number (1-indexed)
        per_page: Number of transactions per page

    Returns:
        List of transaction dictionaries
    """
    if workflow is None:
        init_workflow()

    try:
        transactions = workflow.storage.transaction_repo.load_all()
        
        # Sort by date (newest first)
        transactions.sort(key=lambda t: t.date, reverse=True)
        
        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        page_transactions = transactions[start:end]
        
        # Convert to dictionaries
        result = []
        for txn in page_transactions:
            txn_dict = {
                "date": txn.date.isoformat(),
                "description": txn.description,
                "amount": str(txn.amount),
                "transaction_type": txn.transaction_type.value,
                "category": None,
            }
            if txn.category:
                txn_dict["category"] = {
                    "name": txn.category.name,
                    "parent": txn.category.parent,
                }
            if txn.account:
                txn_dict["account"] = txn.account
            if txn.balance is not None:
                txn_dict["balance"] = str(txn.balance)
            
            result.append(txn_dict)
        
        return result
    except Exception as e:
        logger.error(f"Error getting transactions: {e}", exc_info=True)
        return []


@eel.expose
def get_overall_stats() -> Dict:
    """
    Get overall statistics.

    Returns:
        Dictionary with overall statistics
    """
    if workflow is None:
        init_workflow()

    try:
        analyzer = workflow.analyze_spending()
        total_income = analyzer.get_total_income()
        total_expenses = analyzer.get_total_expenses()
        net_amount = analyzer.get_net_amount()
        
        savings_rate = None
        if total_income > 0:
            savings_rate = float((net_amount / total_income) * 100)
        
        return {
            "total_income": str(total_income),
            "total_expenses": str(total_expenses),
            "net_amount": str(net_amount),
            "savings_rate": savings_rate,
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return {
            "total_income": "0",
            "total_expenses": "0",
            "net_amount": "0",
            "savings_rate": 0,
        }


@eel.expose
def get_monthly_summaries() -> List[Dict]:
    """
    Get all monthly summaries.

    Returns:
        List of monthly summary dictionaries
    """
    if workflow is None:
        init_workflow()

    try:
        analyzer = workflow.analyze_spending()
        summaries = analyzer.get_all_monthly_summaries()
        
        result = []
        for summary in summaries:
            result.append({
                "year": summary.year,
                "month": summary.month,
                "total_income": str(summary.total_income),
                "total_expenses": str(summary.total_expenses),
                "net_amount": str(summary.net_amount),
                "transaction_count": summary.transaction_count,
                "savings_rate": summary.savings_rate,
                "category_breakdown": {
                    k: str(v) for k, v in summary.category_breakdown.items()
                },
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting monthly summaries: {e}", exc_info=True)
        return []


@eel.expose
def get_category_breakdown() -> Dict[str, str]:
    """
    Get category breakdown.

    Returns:
        Dictionary mapping category names to total amounts
    """
    if workflow is None:
        init_workflow()

    try:
        analyzer = workflow.analyze_spending()
        breakdown = analyzer.get_category_breakdown()
        return {k: str(v) for k, v in breakdown.items()}
    except Exception as e:
        logger.error(f"Error getting category breakdown: {e}", exc_info=True)
        return {}


@eel.expose
def get_spending_patterns() -> List[Dict]:
    """
    Get spending patterns for all categories.

    Returns:
        List of spending pattern dictionaries
    """
    if workflow is None:
        init_workflow()

    try:
        analyzer = workflow.analyze_spending()
        patterns = analyzer.get_spending_patterns()
        
        result = []
        for pattern in patterns:
            result.append({
                "category": pattern.category,
                "total_amount": str(pattern.total_amount),
                "transaction_count": pattern.transaction_count,
                "average_transaction": str(pattern.average_transaction),
                "min_transaction": str(pattern.min_transaction),
                "max_transaction": str(pattern.max_transaction),
                "percentage_of_total": pattern.percentage_of_total,
                "trend": pattern.trend,
            })
        
        # Sort by total amount descending
        result.sort(key=lambda p: float(p["total_amount"]), reverse=True)
        
        return result
    except Exception as e:
        logger.error(f"Error getting spending patterns: {e}", exc_info=True)
        return []


@eel.expose
def export_transactions() -> str:
    """
    Export transactions to JSON file.

    Returns:
        Path to exported file
    """
    if workflow is None:
        init_workflow()

    try:
        from datetime import datetime
        
        export_dir = workflow.storage.data_dir / "exports"
        export_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = export_dir / f"transactions_{timestamp}.json"
        
        workflow.storage.export_transactions_json(export_file)
        
        return str(export_file)
    except Exception as e:
        logger.error(f"Error exporting transactions: {e}", exc_info=True)
        raise


@eel.expose
def recategorize_all(overwrite: bool = True) -> Dict:
    """
    Recategorize all transactions.

    Args:
        overwrite: Whether to overwrite existing categories

    Returns:
        Dictionary with recategorization statistics
    """
    if workflow is None:
        init_workflow()

    try:
        stats = workflow.recategorize_all(overwrite=overwrite)
        return {
            "success": True,
            "total": stats["total"],
            "categorized": stats["categorized"],
            "uncategorized": stats["uncategorized"],
            "categorization_rate": stats["categorization_rate"],
        }
    except Exception as e:
        logger.error(f"Error recategorizing: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def start_web_app(port: int = 8080, size: tuple = (1200, 800)) -> None:
    """
    Start the Eel web application.

    Args:
        port: Port number for the web server
        size: Window size (width, height) for desktop app
    """
    # Setup logging
    setup_logging(level="INFO")
    
    # Initialize workflow
    init_workflow()
    
    # Get web directory
    web_dir = Path(__file__).parent.parent / "web"
    
    logger.info(f"Starting web app on port {port}")
    logger.info(f"Web directory: {web_dir}")
    
    # Start Eel
    eel.init(str(web_dir))
    
    # Configure for Microsoft Edge on macOS
    edge_path = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
    
    # Start the app
    try:
        if Path(edge_path).exists():
            # For macOS, we need to manually launch Edge since Eel's edge mode is Windows-only
            logger.info(f"Using Microsoft Edge at {edge_path}")
            
            # Check if port is available, if not try next port
            import socket
            def is_port_available(port_num):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    return s.connect_ex(('localhost', port_num)) != 0
            
            actual_port = port
            if not is_port_available(port):
                # Try next few ports
                for p in range(port, port + 10):
                    if is_port_available(p):
                        actual_port = p
                        logger.info(f"Port {port} in use, using port {actual_port} instead")
                        break
                else:
                    logger.error(f"Could not find available port starting from {port}")
                    return
            
            # Launch Edge after a short delay to allow server to start
            import threading
            import time
            
            def launch_edge_delayed():
                time.sleep(1.5)  # Wait for server to start
                url = f"http://localhost:{actual_port}/index.html"
                logger.info(f"Launching Edge with URL: {url}")
                subprocess.Popen(
                    [edge_path, "--new-window", url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.PIPE
                )
            
            # Launch Edge in background thread
            edge_thread = threading.Thread(target=launch_edge_delayed, daemon=True)
            edge_thread.start()
            
            # Start Eel server (this blocks)
            eel.start("index.html", size=size, port=actual_port, mode=None, host="localhost")
        else:
            # Fallback to default browser if Edge not found
            logger.warning(f"Edge not found at {edge_path}, using default browser")
            eel.start("index.html", size=size, port=port)
    except (SystemExit, MemoryError, KeyboardInterrupt):
        logger.info("Web app closed")


if __name__ == "__main__":
    start_web_app()

