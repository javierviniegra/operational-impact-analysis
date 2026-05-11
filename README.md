# Operational Impact Analysis

A reproducible and auditable analytics project designed to support executive decision-making
by integrating sales, purchases, costs, yields, service quality, and operational performance.

This repository is intentionally aligned with existing Power BI executive reporting and KPI definitions,
while extending analysis depth via Python-based data engineering, validation, and explainability. [1](https://app.powerbi.com/groups/7fb5d46e-0769-4f9c-8e10-990afff7b341/reports/7a109fc3-96ef-4d2a-a7a6-33042044db68?pbi_source=Substrate)[2](https://app.powerbi.com/groups/7fb5d46e-0769-4f9c-8e10-990afff7b341/reports/c3d0337b-2f5c-4cff-aedf-cf45a5ad2969?pbi_source=Substrate)

---

## What This Project Covers

The project integrates multiple domains into one consistent analytical model:

### Sales (Totals)
- Total sales and daily operational totals (POS daily cash closing)
- Channel split: Dine-in / Delivery / Takeaway
- Time analysis: hour, day-of-week, week, month, year
- Ticket and check metrics (tickets, average ticket, average check, people)

### Purchases & Costs (Subtotals)
- Purchases sourced from invoice-based inventory inputs only (`TipoEntrada = "Factura"`)
- Subtotal-based cost calculations (VAT excluded) to avoid cost contamination
- Cost decomposition (theoretical cost, waste, cancellations, complimentary items, etc.)

### Production Yields (Tablajería)
- Yield vs ideal yield
- Waste / shrink quantification
- Monetary impact of yield deviation

### People & Execution
- Waiter performance and productivity
- People-per-table and people-per-waiter analysis
- Product and mix analysis (items, categories, groups)

### Quality & Compliance (Zenput)
- Audit scores and trends
- Task completion rates and overdue patterns [2](https://app.powerbi.com/groups/7fb5d46e-0769-4f9c-8e10-990afff7b341/reports/c3d0337b-2f5c-4cff-aedf-cf45a5ad2969?pbi_source=Substrate)

### Executive KPI Cards (Power BI parity)
- KPI cards such as Total Cost, Cancellations Cost, Complimentary Cost, Waste Cost,
  Theoretical Cost, Operating Margin, etc., replicated in Python using the same business logic. [1](https://app.powerbi.com/groups/7fb5d46e-0769-4f9c-8e10-990afff7b341/reports/7a109fc3-96ef-4d2a-a7a6-33042044db68?pbi_source=Substrate)

---

## Critical Methodology

To ensure consistency and avoid fiscal noise, we apply a strict methodology:

### Sales
- Sales are reported as **Totals (VAT included)**.
- Sales totals are used as the denominator for % metrics.

### Costs
- Costs are reported as **Subtotals (VAT excluded)**.
- Purchases are based on **invoice-backed inventory inputs** only.

### Percent KPIs
- All “cost %” metrics are computed as:

  **Cost (subtotal) / Sales (total)**

Full methodology is documented in `METHODOLOGY.md`.

---

## Technology Stack

- Python
- MySQL
- pandas / numpy
- matplotlib (baseline)
- seaborn (EDA / statistical visuals)
- plotly (executive / interactive visuals)
- Jupyter notebooks
- mysql-connector-python
- python-dotenv

---

## Repository Structure (High Level)

- `src/` contains reusable logic:
  - `extract/` data pulls from MySQL
  - `transform/` KPI computation and business rules
  - `visualize/` chart helpers (seaborn + plotly)
- `notebooks/` contains narrative analysis and executive reporting output
- `output/` stores generated datasets and figures (not committed)

---

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt