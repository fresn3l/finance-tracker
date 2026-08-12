# Future Work

This document outlines potential enhancements. Several items that used to live here are **already implemented** — see [TODO.md](TODO.md) and [docs/FEATURE_RECOMMENDATIONS.md](docs/FEATURE_RECOMMENDATIONS.md) before rebuilding them.

Already in the codebase: CSV import, categorization (including custom rules UI and learning from category corrections), encrypted JSON storage, CLI + Eel web UI (localhost, vendored Chart.js), transaction edit/split/merge, search/filter, in-app budgets, recurring detection, month-over-month comparison, cash flow / forecasts / goals / accounts, local HTML/PDF monthly reports, macOS notifications, launchd scheduling, and Mac app packaging scaffolding.

## Enhanced Categorization

- **Machine Learning Integration**: NLP-based categorization from merchant names
- **Richer multi-account**: Full portfolio and loan amortization (balances + net worth already exist)

## Advanced Analytics

- **Year-over-year comparisons** and seasonal patterns
- **Recurring amount-change alerts**: Notify when a subscription price changes

## Data Management

- **Database Migration**: SQLCipher instead of encrypted JSON files
- **Additional import formats**: OFX, QIF
- **Data Backup & Sync**: Optional encrypted backup; keep local-first as the default

## User Experience

- **Signed/notarized Mac app**: Scaffolding is in `packaging/`; build on macOS
- **Dark Mode**
- **Accessibility**: WCAG compliance
- **Multi-language Support**

## Security & Privacy

- **Local-first Architecture**: Already the default; keep it that way (no required cloud)

## Integration & Automation

- **Bank API Integration**: Plaid/Yodlee (optional; conflicts with local-only unless user opts in)
- **Email delivery**: Only if you want the monthly report leaving the machine (notification is local today)
- **Receipt Scanning**: OCR
- **Tax Preparation**: Export formats for tax software

## Reporting & Visualization

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
