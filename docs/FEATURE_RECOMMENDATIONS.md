# Feature Recommendations for Finance Tracker

Based on analysis of the current codebase and common needs in personal finance applications, here are prioritized feature recommendations.

## 🔥 High Priority - Core Functionality Gaps

The items below were the original gaps. **Transaction editing, budgets, recurring detection, advanced search, and custom category rules are implemented** in the web UI and CLI. Remaining work is polish, delivery, and packaging — see [TODO.md](../TODO.md).

### 1. **Transaction Editing & Management** — implemented
Edit, delete, split, merge, and bulk edit are available in the web Transactions tab and via `finance-tracker edit` / `delete`.

Still open: merge UX in the web UI. Category corrections now learn merchant mappings for later imports.

### 2. **Budget Tracking & Alerts** — implemented (in-app)
Set/list/delete budgets and view alerts in the web Budgets tab and `finance-tracker budget`.

Still open: email/notification delivery when a threshold is hit.

### 3. **Recurring Transaction Detection** — implemented
Detect and mark patterns in the Recurring tab and `finance-tracker recurring detect|mark`.

Still open: amount-change alerts and a dedicated subscription dashboard beyond the current list.

### 4. **Advanced Search & Filtering** — implemented
Web advanced search plus `finance-tracker list --query/--category/--account/--type/--recurring`.

Still open: saved filter presets and a structured query builder.

### 5. **Custom Category Rules UI** — implemented
Rules tab can add, test, import, and export regex rules.

## 📊 Medium Priority - Enhanced Analytics

### 6. **Year-over-Year Comparisons** ⭐⭐
**Why it's valuable:**
- See spending trends across years
- Identify seasonal patterns
- Better financial planning

**What to implement:**
- Compare same month across different years
- Year-over-year percentage changes
- Seasonal spending patterns visualization
- "This time last year" insights

**Implementation complexity:** Low-Medium
**User value:** Medium

### 7. **Spending Forecasts** ⭐⭐
**Why it's valuable:**
- Predict future spending based on patterns
- Help with financial planning
- Identify potential budget issues early

**What to implement:**
- Simple moving average forecasts
- Category-level predictions
- Confidence intervals
- "If current trends continue" scenarios

**Implementation complexity:** Medium
**User value:** Medium

### 8. **Multi-Account Support** ⭐⭐
**Why it's valuable:**
- Many users have multiple accounts
- Need unified view across accounts
- Better financial picture

**What to implement:**
- Account management (add/edit/delete accounts)
- Account-specific views and filters
- Net worth calculation across accounts
- Account balance tracking over time
- Transfer detection between accounts

**Implementation complexity:** Medium
**User value:** Medium-High

## 🎨 Nice-to-Have - Polish & UX

### 9. **Dark Mode** ⭐
**Why it's nice:**
- Modern app expectation
- Better for extended use
- Accessibility benefit

**Implementation complexity:** Low
**User value:** Medium

### 10. **PDF Report Generation** ⭐
**Why it's nice:**
- Professional reports for sharing
- Tax preparation support
- Archival purposes

**What to implement:**
- Monthly/yearly summary PDFs
- Customizable report templates
- Charts and graphs in PDF
- Email delivery option

**Implementation complexity:** Medium
**User value:** Medium

### 11. **Transaction Tags/Labels** ⭐
**Why it's nice:**
- More flexible than categories
- Multiple tags per transaction
- Better organization

**What to implement:**
- Add/remove tags from transactions
- Filter by tags
- Tag-based reports
- Tag suggestions

**Implementation complexity:** Low-Medium
**User value:** Medium

## 🚀 Advanced - Future Considerations

### 12. **Machine Learning Categorization**
- Improve accuracy over time
- Learn from user corrections
- Handle edge cases better

**Implementation complexity:** High
**User value:** High (long-term)

### 13. **Bank API Integration (Plaid/Yodlee)**
- Automatic transaction import
- Real-time balance updates
- No manual CSV uploads

**Implementation complexity:** High
**User value:** Very High (but requires external services)

### 14. **Receipt Scanning (OCR)**
- Photo receipt → transaction
- Extract merchant, amount, date
- Link receipt to transaction

**Implementation complexity:** High
**User value:** Medium-High

## Recommended Implementation Order

### Phase 1: Foundation — done
1. Transaction Editing & Management
2. Advanced Search & Filtering
3. Custom Category Rules UI

### Phase 2: Planning Features — mostly done
4. Budget Tracking & Alerts (in-app; email/push still open)
5. Recurring Transaction Detection
6. Year-over-Year Comparisons — **not started** (nor month-over-month reports)

### Phase 3: Polish (Later)
7. Dark Mode
8. PDF Reports
9. Multi-Account Support

### Phase 4: Advanced (Future)
10. ML Categorization
11. Bank API Integration
12. Receipt Scanning

## Quick Wins (Low Effort, High Value)

These can be implemented quickly and provide immediate value:

1. **Transaction search in web app** - Add search box to transaction list
2. **Date range picker** - Filter transactions by custom date ranges
3. **Category quick filters** - Click category to filter transactions
4. **Export filtered data** - Export only visible/filtered transactions
5. **Keyboard shortcuts** - Power user features (Ctrl+F for search, etc.)
6. **Transaction notes** - Already in model, just need UI to edit
7. **Bulk category assignment** - Select multiple transactions, assign category

## Feature Dependencies

Some features depend on others:
- **Budget Tracking** → Needs transaction editing (to fix categorization)
- **Recurring Detection** → Benefits from multi-account support
- **ML Categorization** → Needs user correction data (from editing)
- **PDF Reports** → Needs all analysis features to be useful

## User Feedback Priorities

Consider adding:
- In-app feedback mechanism
- Feature request voting
- Usage analytics (which features are used most)
- User surveys

This will help prioritize based on actual user needs rather than assumptions.

