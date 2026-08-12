# TODO List - Finance Tracker Implementation

This list tracks what is implemented versus what is still missing. Prefer this file and the code over older planning docs.

## ✅ Completed

### Core engine
- [X] Project structure, packaging (`pyproject.toml`), and dev tooling
- [X] CSV parser with automatic format detection (3 bank statement formats)
- [X] Data models for transactions, categories, summaries, budgets, recurring patterns
- [X] Category mapping (50+ default regex rules) and categorization engine
- [X] Spending analysis (monthly summaries, category breakdowns, simple trends)
- [X] Sample CSV files and unit tests for core modules
- [X] End-to-end workflow: parse CSV → categorize → store → analyze
- [X] JSON file storage with duplicate detection and import/export (JSON/CSV)
- [X] YAML configuration and logging
- [X] CLI and Eel web UI

### Later features (web + CLI)
- [X] Transaction editing, delete, split, merge, and bulk edit
- [X] Advanced search and filtering
- [X] Budget tracking, templates, and in-app alerts
- [X] Recurring transaction detection and marking
- [X] Custom category rules manager (add/test/import/export)
- [X] MIT LICENSE and GitHub Actions CI

### Reporting, analysis extras, security, Mac packaging
- [X] Month-over-month comparison (totals and per-category $ / % deltas) in analyzer, CLI `summary`, and dashboard
- [X] Cash flow (operating vs transfers), spending forecasts, accounts/net worth, and goals
- [X] Monthly review workflow: import → uncategorized → summary/MoM → local HTML/PDF report
- [X] Monthly report generation (self-contained HTML + PDF) with macOS Notification Center delivery (no email)
- [X] launchd agent (`finance-tracker schedule install`) — 1st of the month at 09:00, fully offline
- [X] Encryption at rest for JSON data (`FTENC1` Fernet; key in `.key` 0600 or macOS Keychain)
- [X] Data directory 0700 / data files 0600; config.yaml 0600
- [X] Vendored Chart.js (no CDN); Eel bound to `127.0.0.1` only
- [X] Mac app packaging scaffolding (PyInstaller spec + py2app setup; build on macOS)

## 🔄 Still missing (product gaps)

### Reporting
- [ ] Year-over-year comparison

### Mac app & packaging
- [ ] Signed/notarized `.app` built on macOS (scaffolding is in `packaging/`)
- [ ] Homebrew formula

### Analysis extras
- [ ] Full portfolio / amortization engines (accounts today are balances + net worth)
- [ ] Learn from user category corrections

## 📚 Docs & quality (ongoing)

- [X] Architecture, API, and getting-started docs (keep in sync with code)
- [X] Tests for editor, budgets, recurring detection, CLI, web transaction IDs, MoM, reports, encryption
- [ ] Performance tests for large datasets
- [ ] Property-based tests for CSV edge cases
