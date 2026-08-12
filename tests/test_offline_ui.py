"""The dashboard must stay fully offline (no CDN)."""

from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"


def test_chart_js_is_vendored():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "vendor/chart.umd.min.js" in html
    assert "cdn" not in html.lower()
    assert "jsdelivr" not in html.lower()
    assert "unpkg" not in html.lower()
    assert (WEB / "vendor" / "chart.umd.min.js").exists()
