# Operational Impact Analysis

A reproducible analytics framework for restaurant operations.

This project integrates Wansoft data sources to generate:

- Executive HTML dashboards (DG level)
- Executive Word reports (narrative + charts)
- Data reconciliation (Orders vs CashClosing)
- Operational diagnostics (quad analysis, heatmaps, waiter performance)

---

## Purpose

Restaurant performance issues often appear as:

- Sales decreasing
- Ticket increasing

This framework identifies whether the root cause is:

- Demand (tickets, customers)
- Consumption (ticket, check)
- Channel mix (delivery vs salon)
- Operational issues (voids, discounts, cancellations)
- Service execution (waiters)
- Data inconsistencies

---

## Data Sources

### Orders / Sales (Wansoft)

Used for:
- Sales
- Tickets
- Customers
- Tables
- Waiter performance
- Time analysis

---

### Cost Data (costeomensual)

- Monthly cost data is cumulative
- The final record of each month represents real cost

---

### Operational KPIs (getglobalcashclosing)

Provides:

- anulaciones
- cancelaciones
- cortesias
- descuentos

---

## Project Structure

OperationalImpactAnalysis/

- src/
  - extract/
  - transform/
- scripts/
  - validate_all.py
  - generate_dg_presentation_pro_es.py
  - generate_executive_word_es.py
- config/
- docs/
- output/ (ignored)

---

## Setup

### Install dependencies

pip install -r requirements.txt

---

### Configure environment (.env)

Include:

- database credentials
- analysis scope
- branch identifiers

---

## Execution Flow

### 1. Validate pipeline

python -m scripts.validate_all

---

### 2. Generate HTML presentation

python -m scripts.generate_dg_presentation_pro_es

---

### 3. Generate Word report

python -m scripts.generate_executive_word_es

---

## Key Concepts

### Order-Level Model

- 1 row = 1 order
- No duplication from payments

---

### Reconciliation

- Orders vs CashClosing comparison
- Detects inconsistencies and system issues

---

### Quadrant Analysis

Uses median-based segmentation (robust to outliers)

Used for:

- Volume vs sales
- Ticket vs demand
- Waiter performance

---

### Heatmaps

Used to analyze:

- Hourly demand
- Weekly patterns
- Operational timing

---

## Outputs

### HTML Dashboard

- Trends
- Correlations
- Quadrants
- Heatmaps
- Operational drivers

---

### Word Report

- Narrative analysis
- Graphs
- Decisions and recommendations

---

## Principle

This project is designed for:

- Executive decision-making
- Operational diagnosis
- Reproducibility across branches