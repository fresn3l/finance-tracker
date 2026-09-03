"""
py2app setup — run on macOS only:

    python packaging/macos/setup.py py2app
"""

from setuptools import setup

APP = ["packaging/app_entry.py"]
DATA_FILES = [("web", ["web/index.html", "web/style.css", "web/main.js", "web/vendor/chart.umd.min.js"])]
OPTIONS = {
    "argv_emulation": False,
    "packages": ["finance_tracker"],
    "includes": ["cryptography", "fpdf", "eel", "bottle"],
    "plist": {
        "CFBundleName": "Finance Tracker",
        "CFBundleDisplayName": "Finance Tracker",
        "CFBundleIdentifier": "com.financetracker.app",
        "CFBundleShortVersionString": "0.2.0",
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
