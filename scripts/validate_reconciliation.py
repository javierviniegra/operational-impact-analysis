from src.extract.wansoft import load_cashclosing, load_orders, load_payments, load_cost_monthly
from src.transform.sales_model import build_sales_with_payments, add_monthly_costs, add_channel_info
from src.transform.order_level import build_order_level, apply_channel_fallback
from src.transform.reconciliation import reconcile_daily_orders_vs_cashclosing, reconcile_monthly_orders_vs_cashclosing, operational_kpis_monthly_from_cashclosing
import os


def main():
    # Build order-level model (same pipeline you already validated)
    df_orders = load_orders()
    df_payments = load_payments()
    df_cost = load_cost_monthly()
    df_cash = load_cashclosing()

    df = build_sales_with_payments(df_orders, df_payments)
    df = add_monthly_costs(df, df_cost)
    df = add_channel_info(df)
    df = build_order_level(df)
    df = apply_channel_fallback(df)

    daily = reconcile_daily_orders_vs_cashclosing(df, df_cash)
    monthly = reconcile_monthly_orders_vs_cashclosing(daily)

    print("=== DAILY RECON (head) ===")
    print(daily.head(10))

    print("\n=== DAILY RECON (REVIEW rows) ===")
    print(daily[daily["status"] == "REVIEW"].head(20))

    print("\n=== MONTHLY RECON ===")
    print(monthly)

    # Optional: export for inspection
    os.makedirs("output/datasets", exist_ok=True)
    daily.to_csv("output/datasets/recon_daily.csv", index=False)
    monthly.to_csv("output/datasets/recon_monthly.csv", index=False)

    kpi_ops = operational_kpis_monthly_from_cashclosing(df_cash)
    kpi_ops.to_csv("output/datasets/kpis_operational_from_cashclosing.csv", index=False)
    print("\n=== OPERATIONAL KPIs (monthly) ===")
    print(kpi_ops.head(12))

if __name__ == "__main__":
    main()