from src.extract.wansoft import load_orders, load_payments, load_cost_monthly
from src.transform.sales_model import build_sales_with_payments, add_monthly_costs, add_channel_info
from src.transform.order_level import build_order_level, apply_channel_fallback
from src.transform.kpis_monthly import build_monthly_kpis


def main():
    df_orders = load_orders()
    df_payments = load_payments()
    df_cost = load_cost_monthly()

    df = build_sales_with_payments(df_orders, df_payments)
    df = add_monthly_costs(df, df_cost)
    df = add_channel_info(df)

    df = build_order_level(df)
    df = apply_channel_fallback(df)

    print("Total_x dtype:", df["Total_x"].dtype)
    print("Sample Total_x:", df["Total_x"].head(5).tolist())
    
    kpis = build_monthly_kpis(df)

    print("=== KPI VALIDATION ===")
    print(kpis.head())

    print("\nColumns:")
    print(kpis.columns.tolist())


if __name__ == "__main__":
    main()