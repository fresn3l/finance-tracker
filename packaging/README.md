# Packaging Finance Tracker as a Mac app

The UI is a local `127.0.0.1` Eel server opened in a Chrome/Edge `--app=` window (no browser chrome). Data stays on disk, encrypted.

Build **on macOS**. This Linux/CI environment cannot produce a signed `.app`.

## PyInstaller (recommended)

```bash
pip install -e ".[mac]"
pyinstaller packaging/pyinstaller.spec
open dist/Finance\ Tracker.app
```

## py2app

```bash
pip install -e ".[mac]"
python packaging/macos/setup.py py2app
open dist/Finance\ Tracker.app
```

## After install

```bash
finance-tracker schedule install
```

That writes `~/Library/LaunchAgents/com.financetracker.monthly-report.plist` and runs `finance-tracker report --previous-month --notify --pdf` at 09:00 on the 1st of each month. Fully offline: local HTML/PDF plus a Notification Center banner. No email.
