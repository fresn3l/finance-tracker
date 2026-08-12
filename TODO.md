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

## 🔄 Still missing (product gaps)

These are the remaining pieces for a local, secure Mac app that sends a monthly report with month-over-month comparison.

### Reporting
- [ ] Month-over-month comparison (totals and per-category $ / % deltas)
- [ ] Monthly report generation (HTML/PDF)
- [ ] Scheduled delivery (launchd / local notification; optional email)
- [ ] Year-over-year comparison

### Mac app & packaging
- [ ] Native Mac app bundle (`.app`), not Python + Edge
- [ ] Offline charts (vendor Chart.js; drop the CDN)
- [ ] Homebrew formula / standalone executable

### Security
- [ ] Encryption at rest for `~/.finance-tracker/` data
- [ ] Tighten local file permissions
- [ ] Keep the UI fully offline (no third-party script URLs)

### Analysis extras
- [ ] First-class multi-account / net worth / transfer detection
- [ ] Spending forecasts and goals
- [ ] Learn from user category corrections

## 📚 Docs & quality (ongoing)

- [X] Architecture, API, and getting-started docs (keep in sync with code)
- [X] Tests for editor, budgets, recurring detection, CLI, and web transaction IDs
- [ ] Performance tests for large datasets
- [ ] Property-based tests for CSV edge cases
