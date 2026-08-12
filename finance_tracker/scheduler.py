"""Install a launchd agent that runs the monthly report after month-end."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

LABEL = "com.financetracker.monthly-report"
PLIST_NAME = f"{LABEL}.plist"


def _launch_agents_dir() -> Path:
    return Path.home() / "Library" / "LaunchAgents"


def plist_path() -> Path:
    return _launch_agents_dir() / PLIST_NAME


def _argv_prefix() -> list:
    """Prefer the installed CLI; otherwise `python -m finance_tracker.cli`."""
    found = shutil.which("finance-tracker")
    if found:
        return [found]
    return [sys.executable, "-m", "finance_tracker.cli"]


def report_argv(data_dir: Optional[Path] = None) -> list:
    """Argv for the month-end report (previous calendar month, HTML+PDF, notify)."""
    args = _argv_prefix()
    if data_dir:
        args.extend(["--data-dir", str(data_dir)])
    args.extend(["report", "--previous-month", "--notify", "--pdf"])
    return args


def render_plist(program: Optional[str] = None, data_dir: Optional[Path] = None) -> str:
    """Plist that runs on the 1st of each month at 09:00 local time."""
    if program:
        args = [program]
        if data_dir:
            args.extend(["--data-dir", str(data_dir)])
        args.extend(["report", "--previous-month", "--notify", "--pdf"])
    else:
        args = report_argv(data_dir)

    arg_xml = "\n".join(f"      <string>{_escape(a)}</string>" for a in args)
    log_dir = Path.home() / "Library" / "Logs"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LABEL}</string>
    <key>ProgramArguments</key>
    <array>
{arg_xml}
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Day</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>RunAtLoad</key>
    <false/>
    <key>StandardOutPath</key>
    <string>{log_dir / "finance-tracker.monthly.log"}</string>
    <key>StandardErrorPath</key>
    <string>{log_dir / "finance-tracker.monthly.err"}</string>
</dict>
</plist>
"""


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def install(data_dir: Optional[Path] = None, agents_dir: Optional[Path] = None) -> Path:
    """Write the LaunchAgent plist and load it when launchctl is available."""
    if sys.platform != "darwin":
        logger.warning("launchd install is for macOS; writing plist anyway")
    agents = Path(agents_dir) if agents_dir is not None else _launch_agents_dir()
    agents.mkdir(parents=True, exist_ok=True)
    dest = agents / PLIST_NAME
    dest.write_text(render_plist(data_dir=data_dir), encoding="utf-8")
    os.chmod(dest, 0o644)
    if shutil.which("launchctl") and agents_dir is None:
        uid = os.getuid()
        subprocess.run(["launchctl", "unload", str(dest)], check=False, capture_output=True)
        subprocess.run(
            ["launchctl", "bootstrap", f"gui/{uid}", str(dest)],
            check=False,
            capture_output=True,
        )
        # Older macOS
        subprocess.run(["launchctl", "load", "-w", str(dest)], check=False, capture_output=True)
    return dest


def uninstall() -> bool:
    """Unload and delete the LaunchAgent."""
    dest = plist_path()
    if shutil.which("launchctl") and dest.exists():
        uid = os.getuid()
        subprocess.run(
            ["launchctl", "bootout", f"gui/{uid}/{LABEL}"],
            check=False,
            capture_output=True,
        )
        subprocess.run(["launchctl", "unload", str(dest)], check=False, capture_output=True)
    if dest.exists():
        dest.unlink()
        return True
    return False


def status() -> dict:
    """Whether the plist exists and whether launchctl lists the job."""
    dest = plist_path()
    loaded = False
    if shutil.which("launchctl"):
        result = subprocess.run(
            ["launchctl", "list", LABEL],
            capture_output=True,
            check=False,
        )
        loaded = result.returncode == 0
    return {"plist": str(dest), "installed": dest.exists(), "loaded": loaded}
