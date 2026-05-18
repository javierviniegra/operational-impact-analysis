import pandas as pd

def _to_date(series):
    return pd.to_datetime(series, errors="coerce").dt.date

def reconcile_daily_orders_vs_cashclosing(df_orders_orderlevel: pd.DataFrame, df_cash: pd.DataFrame) -> pd.DataFrame:
    """
    Compares daily totals from Orders (sum of Total_x) vs getglobalcashclosing.total_ventas.
    Also compares tickets and people where possible.
    """
    o = df_orders_orderlevel.copy()
    c = df_cash.copy()

    # Orders daily aggregation
    o["date"] = _to_date(o["Fecha_x"])
    o["Total_x"] = pd.to_numeric(o["Total_x"], errors="coerce").fillna(0)
    o["Personas"] = pd.to_numeric(o["Personas"], errors="coerce").fillna(0)

    orders_daily = (o.groupby("date", as_index=False)
                     .agg(orders_ventas=("Total_x", "sum"),
                          orders_tickets=("Movimento", "nunique"),
                          orders_personas=("Personas", "sum")))

    # Cash closing daily normalization
    c["date"] = _to_date(c["fecha_corte"])
    # total_ventas ya viene como numérico normalmente, pero lo forzamos
    c["total_ventas"] = pd.to_numeric(c["total_ventas"], errors="coerce").fillna(0)
    c["total_personas"] = pd.to_numeric(c.get("total_personas"), errors="coerce").fillna(0)
    c["no_ordenes"] = pd.to_numeric(c.get("no_ordenes"), errors="coerce").fillna(0)

    cash_daily = (c.groupby("date", as_index=False)
                   .agg(cash_ventas=("total_ventas", "sum"),
                        cash_tickets=("no_ordenes", "sum"),
                        cash_personas=("total_personas", "sum")))

    # Merge + deltas
    out = orders_daily.merge(cash_daily, on="date", how="outer").fillna(0)

    out["delta_ventas"] = out["orders_ventas"] - out["cash_ventas"]
    out["delta_ventas_pct"] = out["delta_ventas"] / out["cash_ventas"].replace({0: pd.NA})

    out["delta_tickets"] = out["orders_tickets"] - out["cash_tickets"]
    out["delta_personas"] = out["orders_personas"] - out["cash_personas"]

    # Flag rules (ajustables)
    out["status"] = "OK"
    out.loc[out["cash_ventas"].gt(0) & (out["delta_ventas_pct"].abs() > 0.01), "status"] = "REVIEW"  # >1% diferencia
    out.loc[out["cash_ventas"].eq(0) & out["orders_ventas"].gt(0), "status"] = "REVIEW"

    return out.sort_values("date")


def reconcile_monthly_orders_vs_cashclosing(df_daily_recon: pd.DataFrame) -> pd.DataFrame:
    d = df_daily_recon.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d["month"] = d["date"].dt.to_period("M").astype(str)

    m = (d.groupby("month", as_index=False)
          .agg(orders_ventas=("orders_ventas", "sum"),
               cash_ventas=("cash_ventas", "sum"),
               delta_ventas=("delta_ventas", "sum"),
               orders_tickets=("orders_tickets", "sum"),
               cash_tickets=("cash_tickets", "sum"),
               orders_personas=("orders_personas", "sum"),
               cash_personas=("cash_personas", "sum")))

    m["delta_ventas_pct"] = m["delta_ventas"] / m["cash_ventas"].replace({0: pd.NA})
    m["status"] = "OK"
    m.loc[m["cash_ventas"].gt(0) & (m["delta_ventas_pct"].abs() > 0.005), "status"] = "REVIEW"
    m.loc[m["cash_ventas"].eq(0) & m["orders_ventas"].gt(0), "status"] = "REVIEW"
    return m

def operational_kpis_monthly_from_cashclosing(df_cash: pd.DataFrame) -> pd.DataFrame:
    c = df_cash.copy()
    c["date"] = pd.to_datetime(c["fecha_corte"], errors="coerce")
    c["month"] = c["date"].dt.to_period("M").astype(str)

    for col in ["cortesias_en_platillos", "cancelaciones_en_platillos", "anulaciones_en_platillos", "descuentos_en_platillos"]:
        if col in c.columns:
            c[col] = pd.to_numeric(c[col], errors="coerce").fillna(0)
        else:
            c[col] = 0

    m = (c.groupby("month", as_index=False)
          .agg(cortesias_en_platillos=("cortesias_en_platillos", "sum"),
               cancelaciones_en_platillos=("cancelaciones_en_platillos", "sum"),
               anulaciones_en_platillos=("anulaciones_en_platillos", "sum"),
               descuentos_en_platillos=("descuentos_en_platillos", "sum")))
    return m
