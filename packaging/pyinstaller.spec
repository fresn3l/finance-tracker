# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for a Mac (or local) Finance Tracker build.

Run on macOS:
    pyinstaller packaging/pyinstaller.spec
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).parent

hidden = collect_submodules("finance_tracker")

a = Analysis(
    [str(ROOT / "packaging" / "app_entry.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(ROOT / "web"), "web")],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="FinanceTracker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name="Finance Tracker.app",
    icon=None,
    bundle_identifier="com.financetracker.app",
    info_plist={
        "CFBundleName": "Finance Tracker",
        "CFBundleDisplayName": "Finance Tracker",
        "CFBundleShortVersionString": "0.2.0",
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
    },
)
