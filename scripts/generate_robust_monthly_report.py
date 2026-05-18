import os
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Opcional: para heatmap hour x dow desde Orders
from src.extract.wansoft import load_orders
from config.analysis import get_scope


def ensure_dirs():
    os.makedirs("output/report", exist_ok=True)
    os.makedirs("output/figures", exist_ok=True)


def read_inputs():
    kpis = pd.read_csv("output/datasets/kpis_monthly.csv")
    recon_m = pd.read_csv("output/datasets/reconciliation_monthly.csv")
    recon_d = pd.read_csv("output/datasets/reconciliation_daily.csv")
    ops = pd.read_csv("output/datasets/kpis_operational.csv")
    return kpis, recon_m, recon_d, ops


def prepare_monthly_frame(kpis, recon_m, ops):
    df = kpis.merge(recon_m, on=["month"], how="left", suffixes=("", "_recon"))
    df = df.merge(ops, on=["month"], how="left")

    # Numeric coercion safety
    for col in ["Ventas", "Tickets", "Personas", "CostoTotal", "COGS_%", "Margen", "Margen_%", "delta_ventas_pct"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # If KPI script already computed these, keep; else compute safely
    if "COGS_%" not in df.columns or df["COGS_%"].isna().all():
        df["COGS_%"] = df["CostoTotal"] / df["Ventas"]

    if "Margen" not in df.columns or df["Margen"].isna().all():
        df["Margen"] = df["Ventas"] - df["CostoTotal"]

    if "Margen_%" not in df.columns or df["Margen_%"].isna().all():
        df["Margen_%"] = df["Margen"] / df["Ventas"]

    # Business-quality flags (if missing, default)
    if "source_flag" not in df.columns:
        df["source_flag"] = "OK"
    if "status" not in df.columns:
        df["status"] = "OK"

    # Month ordering
    df["month_dt"] = pd.to_datetime(df["month"] + "-01", errors="coerce")
    df = df.sort_values("month_dt")

    # Real issue definition: REVIEW excluding known migrations
    df["is_real_issue"] = (df["status"] == "REVIEW") & (df["source_flag"] == "OK")

    return df


def compute_breakpoints(df):
    """
    Breakpoints: big changes MoM in sales, COGS%, margin%, and reconciliation deltas.
    """
    out = df[["month", "month_dt", "Ventas", "COGS_%", "Margen_%", "delta_ventas_pct", "status", "source_flag", "is_real_issue"]].copy()

    out["ventas_mom_pct"] = out["Ventas"].pct_change()
    out["cogs_mom_pp"] = out["COGS_%"].diff() * 100  # percentage points
    out["margen_mom_pp"] = out["Margen_%"].diff() * 100

    # Simple breakpoint score (weighted)
    out["break_score"] = (
        out["ventas_mom_pct"].abs().fillna(0) * 1.0 +
        (out["cogs_mom_pp"].abs().fillna(0) / 10.0) * 0.6 +
        (out["margen_mom_pp"].abs().fillna(0) / 10.0) * 0.6 +
        out["delta_ventas_pct"].abs().fillna(0) * 1.2
    )

    # Flag top breakpoints
    thresh = out["break_score"].quantile(0.90) if out["break_score"].notna().any() else 0
    out["is_breakpoint"] = out["break_score"] >= thresh

    return out


def plotly_exec_report(df, breakpoints):
    """
    Builds a premium HTML report with:
    - Time series: Sales / COGS% / Margin%
    - Mix by channel
    - Scatter: Ticket vs COGS% colored by Delivery share
    - Reconciliation delta timeline
    - Breakpoints table
    """
    # Sales + COGS + Margin
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        specs=[[{"secondary_y": True}],
               [{"secondary_y": True}],
               [{"secondary_y": False}],
               [{"secondary_y": False}]],
        subplot_titles=(
            "Ventas (Total) vs COGS% (Monthly)",
            "Margen% y Ticket/Cheque",
            "Mix por canal (Ventas)",
            "Reconciliación: delta_ventas_pct (Monthly)"
        )
    )

    # Row 1: Sales + COGS
    fig.add_trace(go.Scatter(x=df["month_dt"], y=df["Ventas"], name="Ventas", mode="lines+markers"), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=df["month_dt"], y=df["COGS_%"]*100, name="COGS %", mode="lines+markers"), row=1, col=1, secondary_y=True)

    # Row 2: Margin% + ticket/check
    fig.add_trace(go.Scatter(x=df["month_dt"], y=df["Margen_%"]*100, name="Margen %", mode="lines+markers"), row=2, col=1, secondary_y=False)
    if "Ticket_Promedio" in df.columns:
        fig.add_trace(go.Scatter(x=df["month_dt"], y=df["Ticket_Promedio"], name="Ticket Promedio", mode="lines"), row=2, col=1, secondary_y=True)
    if "Cheque_Promedio" in df.columns:
        fig.add_trace(go.Scatter(x=df["month_dt"], y=df["Cheque_Promedio"], name="Cheque Promedio", mode="lines"), row=2, col=1, secondary_y=True)

    # Row 3: Mix (stacked)
    mix_cols = [c for c in df.columns if c.startswith("Ventas_") and c not in ["Ventas_Unknown"]]
    for c in mix_cols:
        label = c.replace("Ventas_", "")
        fig.add_trace(go.Bar(x=df["month_dt"], y=df[c], name=f"Ventas {label}"), row=3, col=1)

    # Row 4: Reconciliation delta
    if "delta_ventas_pct" in df.columns:
        fig.add_trace(go.Bar(x=df["month_dt"], y=df["delta_ventas_pct"]*100, name="Δ Ventas % (Orders vs CashClosing)"), row=4, col=1)

    # Mark breakpoints
    bp = breakpoints[breakpoints["is_breakpoint"]].copy()
    if not bp.empty:
        fig.add_trace(
            go.Scatter(
                x=bp["month_dt"],
                y=[max(df["Ventas"].max(), 1)] * len(bp),
                mode="markers",
                marker=dict(size=12, symbol="x", color="red"),
                name="Breakpoints (Top 10%)"
            ),
            row=1, col=1, secondary_y=False
        )

    fig.update_layout(
        height=1200,
        title="Robust Monthly Executive Report (Branch Evolution & Breakpoints)",
        barmode="stack",
        legend=dict(orientation="h"),
        margin=dict(l=40, r=40, t=80, b=40)
    )

    # Scatter: Ticket vs COGS% colored by Delivery share
    scatter = None
    if "Ticket_Promedio" in df.columns and "COGS_%" in df.columns and "%_Delivery" in df.columns:
        scatter = px.scatter(
            df,
            x="Ticket_Promedio",
            y=df["COGS_%"]*100,
            color="%_Delivery",
            size="Ventas",
            hover_data=["month", "status", "source_flag"],
            title="Scatter: Ticket Promedio vs COGS% (color = % Delivery, size = Ventas)",
            labels={"y": "COGS (%)", "%_Delivery": "% Delivery"}
        )

    return fig, scatter


def seaborn_boxplot_daily_deltas(recon_daily_path="output/datasets/reconciliation_daily.csv"):
    """
    Boxplot of daily delta_ventas_pct by month (shows volatility and outliers).
    """
    d = pd.read_csv(recon_daily_path)
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d["month"] = d["date"].dt.to_period("M").astype(str)
    d["delta_ventas_pct"] = pd.to_numeric(d["delta_ventas_pct"], errors="coerce")

    plt.figure(figsize=(16, 6))
    sns.boxplot(data=d, x="month", y="delta_ventas_pct")
    plt.xticks(rotation=90)
    plt.title("Daily Reconciliation Delta (Orders vs CashClosing) — Boxplot by Month")
    plt.tight_layout()
    plt.savefig("output/figures/boxplot_daily_delta_by_month.png", dpi=150)
    plt.close()


def seaborn_heatmap_hour_dow_from_orders():
    """
    Heatmap: Sales by day-of-week and hour (from Orders).
    Uses Orders table only. Great to detect operational patterns or shifts.
    """
    df_orders = load_orders()
    # date/time parsing
    df_orders["HoraApertura_dt"] = pd.to_datetime(df_orders["HoraApertura"], errors="coerce")
    df_orders["Total_x"] = pd.to_numeric(df_orders["Total"], errors="coerce")  # Orders table uses Total column name
    df_orders = df_orders.dropna(subset=["HoraApertura_dt"])

    df_orders["dow"] = df_orders["HoraApertura_dt"].dt.day_name()
    df_orders["hour"] = df_orders["HoraApertura_dt"].dt.hour

    piv = (df_orders.groupby(["dow", "hour"])["Total_x"].sum()
           .reset_index()
           .pivot(index="dow", columns="hour", values="Total_x")
           .fillna(0))

    # order days for readability
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    piv = piv.reindex(dow_order)

    plt.figure(figsize=(18, 6))
    sns.heatmap(piv, cmap="YlOrRd")
    plt.title("Heatmap: Ventas por Día de Semana vs Hora (Orders)")
    plt.tight_layout()
    plt.savefig("output/figures/heatmap_sales_dow_hour.png", dpi=150)
    plt.close()


def main():
    ensure_dirs()

    kpis, recon_m, recon_d, ops = read_inputs()
    df = prepare_monthly_frame(kpis, recon_m, ops)
    breakpoints = compute_breakpoints(df)

    # Save breakpoints
    breakpoints.to_csv("output/report/breakpoints_monthly.csv", index=False)

    # Build plotly report
    fig_main, fig_scatter = plotly_exec_report(df, breakpoints)

    # Export HTML
    html_path = "output/report/monthly_robust_report.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(fig_main.to_html(full_html=True, include_plotlyjs="cdn"))
        if fig_scatter is not None:
            f.write("<hr>")
            f.write(fig_scatter.to_html(full_html=False, include_plotlyjs=False))

    # Static figures
    seaborn_boxplot_daily_deltas()
    # Optional heatmap (heavy; comment out if you prefer faster runs)
    seaborn_heatmap_hour_dow_from_orders()

    print("\n✅ Robust report generated:")
    print(f"- HTML: {html_path}")
    print("- Breakpoints CSV: output/report/breakpoints_monthly.csv")
    print("- Figures: output/figures/boxplot_daily_delta_by_month.png, output/figures/heatmap_sales_dow_hour.png")


if __name__ == "__main__":
    main()
