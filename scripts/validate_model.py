from src.extract.wansoft import load_orders, load_payments, load_cost_monthly
from src.transform.sales_model import build_sales_with_payments, add_monthly_costs, add_channel_info
from src.transform.order_level import build_order_level, apply_channel_fallback

def main():
    df_orders = load_orders()
    df_payments = load_payments()
    df_cost = load_cost_monthly()

    df = build_sales_with_payments(df_orders, df_payments)
    df = add_monthly_costs(df, df_cost)
    df = add_channel_info(df)

    print("=== Model Validation ===")
    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    print("\nColumns snapshot:")
    print(df.columns.tolist()[:40])

    print("\nSample:")
    def get_existing_cols(df, candidates):
        return [c for c in candidates if c in df.columns]

    print("\nSample:")

    cols = get_existing_cols(df, [
        "Fecha", "Fecha_x",
        "Total", "Total_x",
        "MetodoDePago",
        "CostoTotal",
        "UtilidadMarginal",
    ])

    print(df[cols].head())
    
    print("\nColumns tail:")
    print(df.columns.tolist()[-30:])

    print("\nCanal distribution:")
    print(df["canal"].value_counts())

    print("\nSubcanal distribution:")
    print(df["subcanal"].value_counts().head(10))
    
    # How many payments per order?
    p = df.groupby("Movimento")["Movimiento_Id"].nunique()
    print("Payments per order (top):")
    print(p.value_counts().head(10))
    print("Orders with >1 payment:", (p > 1).sum())


    df = build_order_level(df)
    df = apply_channel_fallback(df)

    print("\nOrder-level rows:", len(df))
    print("Unique orders:", df["Movimento"].nunique())

    print("\nChannel distribution (order-level):")
    print(df["canal"].value_counts().head(10))

    print("\nSubchannel distribution (order-level):")
    print(df["subcanal"].value_counts().head(10))

if __name__ == "__main__":
    main()