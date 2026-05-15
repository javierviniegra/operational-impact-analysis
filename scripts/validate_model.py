from src.extract.wansoft import load_orders, load_payments, load_cost_monthly
from src.transform.sales_model import build_sales_with_payments, add_monthly_costs

def main():
    df_orders = load_orders()
    df_payments = load_payments()
    df_cost = load_cost_monthly()

    df = build_sales_with_payments(df_orders, df_payments)
    df = add_monthly_costs(df, df_cost)

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

if __name__ == "__main__":
    main()