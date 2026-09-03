"""Tests for launchd monthly-report scheduling."""

from pathlib import Path

from finance_tracker.scheduler import LABEL, PLIST_NAME, install, render_plist, report_argv


class TestScheduler:
    def test_plist_runs_previous_month_report_on_the_first(self):
        xml = render_plist(program="/usr/local/bin/finance-tracker", data_dir=Path("/tmp/ft"))
        assert LABEL in xml
        assert "<integer>1</integer>" in xml
        assert "<integer>9</integer>" in xml
        assert "report" in xml
        assert "--previous-month" in xml
        assert "--notify" in xml
        assert "--pdf" in xml
        assert "--data-dir" in xml
        assert "/tmp/ft" in xml
        assert "mailto" not in xml.lower()
        assert "smtp" not in xml.lower()

    def test_report_argv_falls_back_to_python_module(self, monkeypatch):
        monkeypatch.setattr("finance_tracker.scheduler.shutil.which", lambda _name: None)
        argv = report_argv(data_dir=Path("/data"))
        assert "-m" in argv
        assert "finance_tracker.cli" in argv
        assert argv[-4:] == ["report", "--previous-month", "--notify", "--pdf"]

    def test_install_writes_plist_without_touching_home(self, tmp_path):
        dest = install(data_dir=tmp_path / "data", agents_dir=tmp_path)
        assert dest == tmp_path / PLIST_NAME
        assert dest.exists()
        text = dest.read_text(encoding="utf-8")
        assert "report" in text
        assert str(tmp_path / "data") in text
