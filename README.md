# Operational Impact Analysis

A reproducible analytics pipeline and executive reporting package for restaurant operations.  
It integrates Wansoft sales/orders data, monthly costs, and operational cash-closing KPIs to produce:

- A **DG-ready HTML presentation** (interactive, deck-style)
- A **Word executive report** (editable, Spanish narrative + evidence charts)
- A full **reconciliation layer** (Orders vs CashClosing) with business flags
- Advanced diagnostics: **time heatmaps**, **median-based quadrant scatters**, **waiter performance analysis**

---

## What this project solves

Restaurant performance issues often appear as “Sales down / Ticket up”.  
This framework helps you isolate whether changes are driven by:

- Demand (tickets, customers/personas, tables)
- Customer behavior (ticket and check composition)
- Channel mix (dine-in vs delivery vs takeaway)
- Operational execution (voids/cancellations/discounts/courtesies)
- Staff performance (waiters: volume vs conversion)
- Data quality and system transitions (migration flags + branch mapping)

---

## Data sources

This project uses three core sources:

1. **Wansoft Orders / Sales**  
   Used to compute Sales totals, tickets, people/personas, tables, service-time distributions, and waiter metrics.

2. **Wansoft `costeomensual` (monthly cumulative costs)**  
   Monthly costs are cumulative; the **final record of the month** represents month-close values.

3. **Wansoft `getglobalcashclosing` (cash closing KPIs)**  
   Operational drivers used as truth for:
   - `cortesias_en_platillos`
   - `cancelaciones_en_platillos`
   - `anulaciones_en_platillos`
   - `descuentos_en_platillos`

---

## Repository structure
