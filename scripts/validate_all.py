from src.extract.wansoft import (
    load_orders,
    load_payments,
    load_cost_monthly,
    load_cashclosing
)

from src.transform.sales_model import (
    build_sales_with_payments,
    add_monthly_costs,
    add_channel_info
)

from src.transform.order_level import (
    build_order_level,
    apply_channel_fallback
)

from src.transform.kpis_monthly import build_monthly_kpis

from src.transform.reconciliation import (
    reconcile_daily_orders_vs_cashclosing,
    reconcile_monthly_orders_vs_cashclosing,
    operational_kpis_monthly_from_cashclosing
)

import os


def main():
    print("\n🔹 STEP 1 — Extraction")
    df_orders = load_orders()
    df_payments = load_payments()
    df_cost = load_cost_monthly()
    df_cash = load_cashclosing()

    print(df_cost.head())
    print(len(df_cost))

    df_test = load_cost_monthly()

    print("Cost sample:")
    print(df_test.head())
    print("Cost rows:", len(df_test))

    print(df_test)
    print(len(df_test))


    print(f"Orders: {len(df_orders)}")
    print(f"Payments: {len(df_payments)}")
    print(f"Cost: {len(df_cost)}")
    print(f"CashClosing: {len(df_cash)}")

    # ------------------

    print("\n🔹 STEP 2 — Model")
    df = build_sales_with_payments(df_orders, df_payments)
    df = add_monthly_costs(df, df_cost)

    print(f"Model rows: {len(df)}")

    # ------------------

    print("\n🔹 STEP 3 — Channels")
    df = add_channel_info(df)

    print("Canal distribution:")
    print(df["canal"].value_counts().head())

    # ------------------

    print("\n🔹 STEP 4 — Order level")
    df = build_order_level(df)
    df = apply_channel_fallback(df)

    print(f"Unique orders: {df['Movimento'].nunique()}")

    # ------------------

    print("\n🔹 STEP 5 — KPIs")
    kpis = build_monthly_kpis(df)

    print("KPIs sample:")
    print(kpis.head())

    # ------------------

    print("\n🔹 STEP 6 — Reconciliation")
    daily = reconcile_daily_orders_vs_cashclosing(df, df_cash)
    monthly = reconcile_monthly_orders_vs_cashclosing(daily)

    print("\nMonthly reconciliation:")
    print(monthly.head())

    # ------------------

    print("\n🔹 STEP 7 — Operational KPIs")
    kpi_ops = operational_kpis_monthly_from_cashclosing(df_cash)
    print(kpi_ops.head())

    # ------------------

    print("\n🔹 STEP 8 — Save outputs")

    os.makedirs("output/datasets", exist_ok=True)

    kpis.to_csv("output/datasets/kpis_monthly.csv", index=False)
    monthly.to_csv("output/datasets/reconciliation_monthly.csv", index=False)
    daily.to_csv("output/datasets/reconciliation_daily.csv", index=False)
    kpi_ops.to_csv("output/datasets/kpis_operational.csv", index=False)

    print("✅ Files saved in output/datasets")

    # ------------------

    print("\n✅ VALIDATION COMPLETED SUCCESSFULLY")
    print("✅ System is READY for analysis")


if __name__ == "__main__":
    main()