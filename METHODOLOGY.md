
# Methodology

This document explains how raw restaurant data is transformed into **executive-level insights**.

---

## 1. Data sources

### Orders / Sales (Wansoft)
Used for:
- Sales totals
- Tickets
- Customers (personas)
- Tables (mesas)
- Waiter performance

---

### Costs (`costeomensual`)
- Stores cumulative monthly values
- The **last record of each month represents the actual cost**

---

### Operational KPIs (`getglobalcashclosing`)
Used as source of truth for:

- anulaciones_en_platillos
- cancelaciones_en_platillos
- cortesias_en_platillos
- descuentos_en_platillos

---

## 2. Canonical data model

- 1 row = 1 order
- No duplication from payments
- Stable aggregation base

---

## 3. KPI construction

### Sales

- Ventas = sum(Total)
- Tickets = unique orders
- Personas = sum(Personas)
- Ticket = Ventas / Tickets
- Cheque = Ventas / Personas

---

### Costs

- CostoTotal = last monthly cumulative from costeomensual
- COGS% = CostoTotal / Ventas
- Margen = Ventas - CostoTotal
- Margen% = Margen / Ventas

---

## 4. Reconciliation layer

Compares:
- Orders vs CashClosing

Purpose:
- Detect inconsistencies
- Detect system issues
- Flag unreliable months

---

### Key flags

- `SYSTEM_MIGRATION`
- branch name normalization

---

## 5. Quadrant analysis (core methodology)

Quadrants use **median cuts** (not mean):

- Vertical line = median(X)
- Horizontal line = median(Y)

Why:

- Robust against outliers
- Stable over time
- Comparable across periods

---

## 6. Heatmaps

Dimensions:

- Day of week
- Hour of day

Used for:

- Demand pattern detection
- Staffing optimization
- Operational timing issues

---

## 7. Waiter analysis

Each waiter is evaluated on:

- Customers attended
- Sales generated
- Ticket average
- Tables managed

Purpose:

- Identify execution differences
- Detect training opportunities
- Link service quality to revenue

---

## 8. Executive interpretation layer

The analysis focuses on:

- Volume vs ticket behavior
- Demand shifts
- Operational signals
- Staff performance

---

## 9. Outputs

### HTML dashboard (DG)
Interactive, exploratory, fast diagnosis

### Word report
Narrative + charts + recommendations