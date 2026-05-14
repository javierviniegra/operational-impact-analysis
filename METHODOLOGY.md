# Methodology (Sales Totals vs Cost Subtotals)

This document defines the accounting and analytical methodology used throughout this project.
Its purpose is to ensure data consistency, comparability, and auditability across all outputs.

---

## 1. Core Principle

### 1.1 Sales are reported as TOTALS (VAT included)
Sales values reflect POS totals and include VAT, matching operational and customer-facing reality.

### 1.2 Costs are reported as SUBTOTALS (VAT excluded)
Costs exclude VAT to avoid fiscal noise and prevent inflated COGS.

This prevents “contamination” when comparing operational cost structures and margin drivers.

---

## 2. KPI Percentage Convention

All cost-related percentages must use the following convention:

- **Numerator:** Cost in SUBTOTAL (VAT excluded)
- **Denominator:** Sales in TOTAL (VAT included)

Example:
- Waste Cost % = Waste Cost (subtotal) / Sales (total)

---

## 3. Source-of-Truth Hierarchy

### 3.1 Sales (Source of Truth)
Primary:
- POS daily cash closing totals (e.g., global cash closing)

Secondary (validation / drilldown):
- Daily order-level tables
- Line-item detail tables

### 3.2 Purchases (Source of Truth)
Purchases are derived only from invoice-backed inventory entries:

- Filter: `TipoEntrada = "Factura"`
- This ensures purchases represent real, fiscally supported acquisition costs.

### 3.3 Production / Yields (Tablajería)
Yield and waste metrics are derived from daily meat processing records, compared against ideal benchmarks.
Variance vs ideal is treated as an operational driver of margin degradation.

### 3.4 Quality (Zenput)
Quality and execution are measured through:
- audit scores over time
- task completion and lateness patterns

---

## 4. Reconciliation & Data Quality Controls

### 4.1 Sales reconciliation
- Reconcile daily totals (cash closing) vs sum of line-item totals.
- Investigate and document any deltas.

### 4.2 Cost completeness
- Validate purchase coverage by date and branch.
- Ensure invoice-based inputs are not mixed with transfers or adjustments unless explicitly modeled.

### 4.3 Key integrity checks
- Branch key stability across Wansoft and Zenput.
- Date granularity alignment (day/week/month).
- Product naming/coding normalization where needed (mapping tables).

---

## 5. Time Windows and Comparisons

The calendar dimension standardizes:
- day
- week-of-year
- month
- year
- day-of-week
- hour (when available)

Comparisons supported:
- WoW (week-over-week)
- MoM (month-over-month)
- YoY (year-over-year)
- period vs previous period

---

## 6. Events (Context Layer)

Events provide context to interpret inflection points:
- internal changes (leadership changes, policy shifts)
- operational disruptions
- promotions/campaigns
- external shocks

Events can be sourced from:
- documented internal communication (email/meeting references), or
- a controlled manual event file committed to the repo.

---

## 7. Alignment With Executive KPI Cards

Executive KPI “cards” are implemented in Python to match Power BI definitions.
Each KPI must be registered in `METRICS.md` with:
- definition
- base table(s)
- filters
- VAT basis (total vs subtotal)
- Python function reference
- validation notes

---

## 8. Output Standards

All outputs must:
- clearly state methodology (Totals vs Subtotals)
- include the time window used
- be reproducible from raw sources
- be exportable to `output/` (datasets and figures)

No output is considered “final” unless reconciliation checks pass and the KPI is registered.