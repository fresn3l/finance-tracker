# Future Work

This document outlines potential enhancements. Several items that used to live here are **already implemented** — see [TODO.md](TODO.md) and [docs/FEATURE_RECOMMENDATIONS.md](docs/FEATURE_RECOMMENDATIONS.md) before rebuilding them.

Already in the codebase: CSV import, categorization (including custom rules UI), JSON storage with duplicate detection, CLI + Eel web UI, transaction edit/split/merge, search/filter, in-app budgets, and recurring detection.

## Enhanced Categorization

- **Machine Learning Integration**: NLP-based categorization from merchant names
- **Category Learning**: Improve accuracy from user corrections over time
- **Multi-account Support**: First-class accounts, transfers, and a unified net-worth view (account is currently an import tag)

## Advanced Analytics

- **Month-over-month comparison**: Totals and per-category $ / % deltas (not started)
- **Year-over-year comparisons** and seasonal patterns
- **Predictive Analytics**: Forecast future spending from history
- **Goal Setting**: Savings targets and debt reduction tracking
- **Recurring amount-change alerts**: Notify when a subscription price changes

## Data Management

- **Database Migration**: SQLite/PostgreSQL (or SQLCipher) instead of JSON files
- **Additional import formats**: OFX, QIF
- **Data Backup & Sync**: Optional encrypted backup; keep local-first as the default

## User Experience

- **Native Mac app**: `.app` bundle rather than Python + Edge
- **Dark Mode**
- **Accessibility**: WCAG compliance
- **Multi-language Support**

## Security & Privacy

- **Data Encryption**: Encrypt `~/.finance-tracker/` at rest
- **Fully offline UI**: Vendor Chart.js; no CDN
- **Local-first Architecture**: Already the default; keep it that way (no required cloud)

## Integration & Automation

- **Bank API Integration**: Plaid/Yodlee (optional; conflicts with local-only unless user opts in)
- **Scheduled monthly reports**: launchd + local notification; optional email
- **Receipt Scanning**: OCR
- **Tax Preparation**: Export formats for tax software

## Reporting & Visualization

- **Monthly report generation**: HTML/PDF of the month plus MoM comparison
- **Custom report templates**
- **Richer charts**: heatmaps, sankey diagrams
- **Export to Spreadsheets**: formatted Excel

## Collaboration Features

- **Shared Budgets** / **Expense Sharing** — low priority for a single-user local app
- **Notifications**: Email or push for budget alerts (in-app alerts already exist)

## Performance & Scalability

- **Optimization** for years of history
- **Caching** for report generation
- **Batch Processing** for multiple CSV files
