# KPI Registry (Power BI → Python Contract)

This file is the single source of truth for KPI definitions.
Each KPI must match Power BI business logic and be reproducible in Python.

---

## How to Use This Registry

For every KPI:
1. Copy the Power BI definition (DAX) and list source tables.
2. Specify filters and time logic.
3. Specify VAT basis (Totals vs Subtotals).
4. Implement the Python equivalent and reference the function.
5. Validate against Power BI outputs for at least one known period.

---

## Standard Fields (Required)

- **KPI Name**
- **Business Purpose**
- **Power BI Measure Name**
- **Power BI DAX**
- **Source Tables**
- **Join Keys**
- **Filters**
- **Time Window Logic**
- **VAT Basis**
  - Sales: Totals (VAT included)
  - Costs: Subtotals (VAT excluded)
- **Python Function**
- **Validation**
  - Method used and sample period(s)
- **Notes / Edge Cases**

---

## KPI List (Initial Executive Cards)

> These KPIs are aligned with the executive “card” fields referenced in the Power BI executive reporting. [1](https://app.powerbi.com/groups/7fb5d46e-0769-4f9c-8e10-990afff7b341/reports/7a109fc3-96ef-4d2a-a7a6-33042044db68?pbi_source=Substrate)

### 1) Sales (Total)
- **KPI Name:** Sales (Total)
- **VAT Basis:** Totals
- **Status:** Pending definition

### 2) Raw Material Purchases
- **KPI Name:** Raw Material Purchases
- **VAT Basis:** Subtotals
- **Status:** Pending definition

### 3) Total Cost
- **KPI Name:** Total Cost
- **VAT Basis:** Subtotals
- **Status:** Pending definition

### 4) Theoretical Cost
- **KPI Name:** Theoretical Cost
- **VAT Basis:** Subtotals
- **Status:** Pending definition

### 5) Cost of Cancellations
- **KPI Name:** Cost of Cancellations
- **VAT Basis:** Subtotals
- **Status:** Pending definition

### 6) Cost of Complimentary Items (Comp)
- **KPI Name:** Cost of Complimentary Items
- **VAT Basis:** Subtotals
- **Status:** Pending definition

### 7) Waste Cost (Mermas)
- **KPI Name:** Waste Cost
- **VAT Basis:** Subtotals
- **Status:** Pending definition

### 8) Operating Margin
- **KPI Name:** Operating Margin
- **VAT Basis:** Mixed
  - Sales: Totals
  - Costs/Expenses: Subtotals
- **Status:** Pending definition

### 9) Selling Expense
- **KPI Name:** Selling Expense
- **VAT Basis:** Subtotals
- **Status:** Pending definition

---

## KPI Definition Template (Copy/Paste)

### KPI: <KPI Name>

- **Business Purpose:**
- **Power BI Measure Name:**
- **Power BI DAX:**
  ```DAX
  -- paste DAX here