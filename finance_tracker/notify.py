"""Local notifications. macOS first; no email unless explicitly requested."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys

logger = logging.getLogger(__name__)


def notify(title: str, message: str) -> bool:
    """
    Show a local notification.

    On macOS uses `osascript` (Notification Center). Returns True if a
    notification was sent. Never sends email.
    """
    title = (title or "Finance Tracker")[:80]
    message = (message or "")[:200]
    if sys.platform == "darwin" and shutil.which("osascript"):
        script = (
            "display notification "
            f"{json.dumps(message)} "
            "with title "
            f"{json.dumps(title)}"
        )
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return True
        logger.warning("osascript notification failed: %s", result.stderr.decode())
        return False

    logger.info("Notification skipped (not macOS): %s — %s", title, message)
    return False
