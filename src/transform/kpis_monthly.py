import pandas as pd

def build_monthly_kpis(df_orders):
    df = df_orders.copy()

    # --- Dates ---
    # Usa la fecha de orders (date_x ya existe en tu modelo)
    df["date"] = pd.to_datetime(df["date_x"], errors="coerce")
    df["month"] = df["date"].dt.to_period("M").astype(str)

    # --- Numeric coercion (CRITICAL) ---
    # Total_x viene como string en Wansoft, lo convertimos a float
    df["Total_x"] = pd.to_numeric(df["Total_x"], errors="coerce")
    df["Personas"] = pd.to_numeric(df["Personas"], errors="coerce")

    # Evita NaN rompiendo agregaciones
    df["Total_x"] = df["Total_x"].fillna(0)
    df["Personas"] = df["Personas"].fillna(0)

    grouped = df.groupby("month")

    result = pd.DataFrame({
        "Ventas": grouped["Total_x"].sum(),
        "Tickets": grouped["Movimento"].nunique(),
        "Personas": grouped["Personas"].sum(),
    }).reset_index()

    # Derivados (evita división por cero)
    result["Ticket_Promedio"] = result["Ventas"] / result["Tickets"].replace({0: pd.NA})
    result["Cheque_Promedio"] = result["Ventas"] / result["Personas"].replace({0: pd.NA})

    # --- Monthly costs (already one row per month in your canonical model) ---
    # Usa first porque ya deduplicaste por mes en Tema 6
    costos = df.groupby("month", as_index=False).agg({
        "CostoTotal": "first",
        "CostoDeProductosVendidos": "first",
        "CostoIdealDeProductosPendientesDeRebaja": "first",
        "CostoDeCancelaciones": "first",
        "CostoDeCortesías": "first",
        "CostoDeMerma": "first",
        "CostoDeConsumo": "first",
        "UtilidadMarginal": "first",
    })

    # Asegura costos numéricos
    for c in [
        "CostoTotal","CostoDeProductosVendidos","CostoIdealDeProductosPendientesDeRebaja",
        "CostoDeCancelaciones","CostoDeCortesías","CostoDeMerma","CostoDeConsumo","UtilidadMarginal"
    ]:
        if c in costos.columns:
            costos[c] = pd.to_numeric(costos[c], errors="coerce")

    result = result.merge(costos, on="month", how="left")

    # KPIs financieros
    result["COGS_%"] = result["CostoTotal"] / result["Ventas"].replace({0: pd.NA})
    result["Margen"] = result["Ventas"] - result["CostoTotal"]
    result["Margen_%"] = result["Margen"] / result["Ventas"].replace({0: pd.NA})
    result["Gasto_Venta_%"] = result["CostoDeConsumo"] / result["Ventas"].replace({0: pd.NA})

    # Mix por canal (order-level ya está en df)
    canal_mix = df.groupby(["month", "canal"])["Total_x"].sum().unstack(fill_value=0)
    for col in canal_mix.columns:
        result[f"Ventas_{col}"] = canal_mix[col].values
        result[f"%_{col}"] = canal_mix[col].values / result["Ventas"].replace({0: pd.NA})

    return result
