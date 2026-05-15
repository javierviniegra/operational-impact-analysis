import pandas as pd

def build_sales_with_payments(df_orders: pd.DataFrame, df_payments: pd.DataFrame):
    # limpieza básica
    df_orders["Movimento"] = df_orders["Movimento"].astype(str)
    df_payments["Movimiento_Id"] = df_payments["Movimiento_Id"].astype(str)

    # join
    df = df_orders.merge(
        df_payments,
        left_on="Movimento",
        right_on="Movimiento_Id",
        how="left"
    )

    return df

def add_monthly_costs(df_sales, df_cost):
    import pandas as pd

    # identificar columna de fecha en ventas
    date_col = None
    for col in ["Fecha", "Fecha_x", "Fecha_y"]:
        if col in df_sales.columns:
            date_col = col
            break

    if date_col is None:
        raise ValueError("No valid date column found in df_sales")

    # convertir ventas a mes
    df_sales["date"] = pd.to_datetime(df_sales[date_col], errors="coerce")
    df_sales["month"] = df_sales["date"].dt.to_period("M").astype(str)

    # preparar costos
    df_cost["date"] = pd.to_datetime(df_cost["mes_ano"], errors="coerce")
    df_cost["month"] = df_cost["date"].dt.to_period("M").astype(str)

    # ✅ CRÍTICO: quedarnos con el ÚLTIMO registro por mes
    if "created_at" in df_cost.columns:
        df_cost["created_at"] = pd.to_datetime(df_cost["created_at"], errors="coerce")

        df_cost = (
            df_cost.sort_values(["month", "created_at"])
                   .groupby("month", as_index=False)
                   .last()
        )
    else:
        df_cost = df_cost.drop_duplicates(subset=["month"], keep="last")

    # merge correcto
    df = df_sales.merge(
        df_cost,
        how="left",
        on="month"
    )

    return df