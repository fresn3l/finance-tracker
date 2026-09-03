"""Local notifications never send email."""

import sys

from finance_tracker.notify import notify


def test_notify_skips_off_macos(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert notify("Finance Tracker", "Report ready") is False


def test_notify_truncates_long_strings(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr("finance_tracker.notify.shutil.which", lambda _name: "/usr/bin/osascript")
    captured = {}

    def fake_run(args, capture_output=True, check=False):
        captured["args"] = args

        class Result:
            returncode = 0
            stderr = b""

        return Result()

    monkeypatch.setattr("finance_tracker.notify.subprocess.run", fake_run)
    long_title = "T" * 200
    long_message = "M" * 500
    assert notify(long_title, long_message) is True
    script = captured["args"][2]
    assert "T" * 81 not in script
    assert "M" * 201 not in script
