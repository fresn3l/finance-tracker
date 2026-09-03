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


def test_csp_blocks_third_party_scripts():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "Content-Security-Policy" in html
    assert "object-src 'none'" in html
    assert "script-src 'self'" in html
