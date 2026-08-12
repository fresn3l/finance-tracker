"""Local notifications never send email."""

import sys

from finance_tracker.notify import notify


def test_notify_skips_off_macos(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert notify("Finance Tracker", "Report ready") is False
