import os
import numpy as np
import pandas as pd

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

import matplotlib.pyplot as plt
import seaborn as sns

from config.analysis import get_scope
from src.extract.wansoft import load_orders


# -------------------------
# Helpers
# -------------------------
def ensure_dirs():
    os.makedirs("output/presentation", exist_ok=True)
    os.makedirs("output/figures", exist_ok=True)

def to_month_dt(m):
    return pd.to_datetime(m + "-01", errors="coerce")

def safe_num(s):
    return pd.to_numeric(s, errors="coerce")

def compute_breakpoints(df):
    out = df[["month", "Ventas", "COGS_%", "Margen_%", "delta_ventas_pct", "status", "source_flag"]].copy()
    out["month_dt"] = to_month_dt(out["month"])
    out = out.sort_values("month_dt")

    out["ventas_mom_pct"] = out["Ventas"].pct_change()
    out["cogs_mom_pp"] = out["COGS_%"].diff() * 100
    out["margen_mom_pp"] = out["Margen_%"].diff() * 100

    out["break_score"] = (
        out["ventas_mom_pct"].abs().fillna(0) * 1.0 +
        (out["cogs_mom_pp"].abs().fillna(0) / 10.0) * 0.6 +
        (out["margen_mom_pp"].abs().fillna(0) / 10.0) * 0.6 +
        out["delta_ventas_pct"].abs().fillna(0) * 1.2
    )

    thresh = out["break_score"].quantile(0.90) if out["break_score"].notna().any() else 0
    out["is_breakpoint"] = out["break_score"] >= thresh
    return out

def kpi_card(fig, row, col, title, value, subtitle=""):
    fig.add_trace(go.Indicator(
        mode="number",
        value=value if pd.notna(value) else 0,
        title={"text": f"<b>{title}</b><br><span style='font-size:0.8em;color:gray'>{subtitle}</span>"},
        number={"valueformat": ",.2f"} if isinstance(value, (float, np.floating)) else {"valueformat": ",.0f"}
    ), row=row, col=col)


# -------------------------
# Load datasets
# -------------------------
def load_inputs():
    kpis = pd.read_csv("output/datasets/kpis_monthly.csv")
    recon_m = pd.read_csv("output/datasets/reconciliation_monthly.csv")
    ops = pd.read_csv("output/datasets/kpis_operational.csv")
    return kpis, recon_m, ops

def prepare_monthly_frame(kpis, recon_m, ops):
    df = kpis.merge(recon_m[["month", "status", "source_flag", "delta_ventas_pct"]], on="month", how="left")
    df = df.merge(ops, on="month", how="left")

    # numeric
    for c in ["Ventas","Tickets","Personas","Ticket_Promedio","Cheque_Promedio","CostoTotal",
              "COGS_%","Margen","Margen_%","delta_ventas_pct",
              "cortesias_en_platillos","cancelaciones_en_platillos","anulaciones_en_platillos","descuentos_en_platillos"]:
        if c in df.columns:
            df[c] = safe_num(df[c])

    # derived safety
    if "COGS_%" not in df.columns or df["COGS_%"].isna().all():
        df["COGS_%"] = df["CostoTotal"] / df["Ventas"]

    if "Margen" not in df.columns or df["Margen"].isna().all():
        df["Margen"] = df["Ventas"] - df["CostoTotal"]

    if "Margen_%" not in df.columns or df["Margen_%"].isna().all():
        df["Margen_%"] = df["Margen"] / df["Ventas"]

    df["month_dt"] = to_month_dt(df["month"])
    df = df.sort_values("month_dt")

    df["is_real_issue"] = (df["status"] == "REVIEW") & (df["source_flag"] == "OK")
    return df


# -------------------------
# Meseros & Mesas (from Orders)
# -------------------------
def build_meseros_mesas_monthly():
    orders = load_orders()

    # Normalize
    orders["Fecha_dt"] = pd.to_datetime(orders["Fecha"], errors="coerce")
    orders["month"] = orders["Fecha_dt"].dt.to_period("M").astype(str)
    orders["Total_num"] = safe_num(orders["Total"]).fillna(0)
    orders["Personas_num"] = safe_num(orders["Personas"]).fillna(0)

    # Meseros monthly
    meseros = (orders.groupby(["month", "Mesero"], as_index=False)
               .agg(ventas=("Total_num","sum"),
                    tickets=("Movimento","nunique") if "Movimento" in orders.columns else ("Orden","nunique"),
                    personas=("Personas_num","sum"),
                    mesas=("Mesa","nunique")))

    meseros["ticket_promedio"] = meseros["ventas"] / meseros["tickets"].replace({0: np.nan})
    meseros["personas_por_mesa"] = meseros["personas"] / meseros["mesas"].replace({0: np.nan})

    # Mesas monthly
    mesas = (orders.groupby(["month"], as_index=False)
             .agg(ventas=("Total_num","sum"),
                  tickets=("Orden","nunique") if "Orden" in orders.columns else ("id","count"),
                  personas=("Personas_num","sum"),
                  mesas=("Mesa","nunique")))

    mesas["personas_por_mesa"] = mesas["personas"] / mesas["mesas"].replace({0: np.nan})
    mesas["ticket_promedio"] = mesas["ventas"] / mesas["tickets"].replace({0: np.nan})

    return meseros, mesas, orders


def save_static_heatmaps(orders):
    # Heatmap: Day of week vs Hour (ventas)
    orders["HoraApertura_dt"] = pd.to_datetime(orders["HoraApertura"], errors="coerce")
    o = orders.dropna(subset=["HoraApertura_dt"]).copy()
    o["dow"] = o["HoraApertura_dt"].dt.day_name()
    o["hour"] = o["HoraApertura_dt"].dt.hour
    o["Total_num"] = safe_num(o["Total"]).fillna(0)

    piv = (o.groupby(["dow","hour"])["Total_num"].sum()
           .reset_index()
           .pivot(index="dow", columns="hour", values="Total_num")
           .fillna(0))

    dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    piv = piv.reindex(dow_order)

    plt.figure(figsize=(18,6))
    sns.heatmap(piv, cmap="YlOrRd")
    plt.title("Heatmap: Ventas por día de semana vs hora (Orders)")
    plt.tight_layout()
    plt.savefig("output/figures/heatmap_sales_dow_hour.png", dpi=150)
    plt.close()


# -------------------------
# Build DG HTML report (Plotly + simple HTML sections)
# -------------------------
def build_dg_html(df, breakpoints, meseros, mesas):
    s = get_scope()
    title = f"DG Presentation — Branch Monthly Evolution ({s.wansoft_subsidiary_id})"
    subtitle = f"Period: {s.start_date} to {s.end_date} | Methodology: Sales=Totals, Costs=Monthly cumulative (final of month) + CashClosing operational KPIs"

    # --- KPI Cards (latest month) ---
    latest = df.dropna(subset=["month_dt"]).iloc[-1]
    fig_cards = make_subplots(rows=2, cols=4, specs=[[{"type":"indicator"}]*4,[{"type":"indicator"}]*4],
                              subplot_titles=("Ventas","COGS %","Margen %","Ticket Promedio",
                                             "Cheque Promedio","Personas","% Delivery","Δ Ventas % (Recon)"))

    kpi_card(fig_cards, 1, 1, "Ventas", float(latest["Ventas"]), "Total (VAT included)")
    kpi_card(fig_cards, 1, 2, "COGS %", float(latest["COGS_%"]*100), "Costs / Sales")
    kpi_card(fig_cards, 1, 3, "Margen %", float(latest["Margen_%"]*100), "Sales - Costs")
    kpi_card(fig_cards, 1, 4, "Ticket", float(latest.get("Ticket_Promedio", np.nan)), "Ventas / Tickets")
    kpi_card(fig_cards, 2, 1, "Cheque", float(latest.get("Cheque_Promedio", np.nan)), "Ventas / Personas")
    kpi_card(fig_cards, 2, 2, "Personas", float(latest.get("Personas", np.nan)), "Monthly")
    kpi_card(fig_cards, 2, 3, "% Delivery", float(latest.get("%_Delivery", 0)*100), "Share of Sales")
    kpi_card(fig_cards, 2, 4, "Δ Ventas %", float(latest.get("delta_ventas_pct", 0)*100), "Orders vs CashClosing")

    fig_cards.update_layout(height=500, title="KPI Snapshot (Latest Month)")

    # --- Timeline: Sales / COGS / Margin with breakpoints ---
    fig_ts = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                           specs=[[{"secondary_y": True}], [{"secondary_y": True}]],
                           subplot_titles=("Ventas vs COGS% (Monthly)", "Margen% and Mix (Delivery/Salon/Llevar)"))

    fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df["Ventas"], mode="lines+markers", name="Ventas"), row=1, col=1, secondary_y=False)
    fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df["COGS_%"]*100, mode="lines+markers", name="COGS %"), row=1, col=1, secondary_y=True)

    # Breakpoints markers
    bp = breakpoints[breakpoints["is_breakpoint"]].copy()
    if not bp.empty:
        fig_ts.add_trace(go.Scatter(
            x=bp["month_dt"],
            y=df.loc[df["month_dt"].isin(bp["month_dt"]), "Ventas"],
            mode="markers",
            marker=dict(size=10, symbol="x", color="red"),
            name="Breakpoints"
        ), row=1, col=1, secondary_y=False)

    fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df["Margen_%"]*100, mode="lines+markers", name="Margen %"), row=2, col=1, secondary_y=False)
    if "%_Delivery" in df.columns:
        fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df["%_Delivery"]*100, mode="lines", name="% Delivery"), row=2, col=1, secondary_y=True)
    if "%_Salon" in df.columns:
        fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df["%_Salon"]*100, mode="lines", name="% Salón"), row=2, col=1, secondary_y=True)
    if "%_Llevar" in df.columns:
        fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df["%_Llevar"]*100, mode="lines", name="% Llevar"), row=2, col=1, secondary_y=True)

    fig_ts.update_layout(height=800, title="Monthly Evolution & Inflection Points")

    # --- Scatter: Ticket vs COGS% (size=Sales, color=%Delivery) ---
    fig_scatter = px.scatter(
        df,
        x="Ticket_Promedio",
        y=df["COGS_%"]*100,
        size="Ventas",
        color=df.get("%_Delivery", 0),
        hover_data=["month","status","source_flag","delta_ventas_pct"],
        title="Scatter: Ticket Promedio vs COGS% (size=Ventas, color=%Delivery)",
        labels={"y":"COGS (%)", "color":"% Delivery"}
    )

    # --- Operational drivers timeline (bars) ---
    fig_ops = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            subplot_titles=("Anulaciones / Cancelaciones (monthly)", "Cortesías / Descuentos (monthly)"))
    fig_ops.add_trace(go.Bar(x=df["month_dt"], y=df["anulaciones_en_platillos"], name="Anulaciones"), row=1, col=1)
    fig_ops.add_trace(go.Bar(x=df["month_dt"], y=df["cancelaciones_en_platillos"], name="Cancelaciones"), row=1, col=1)
    fig_ops.add_trace(go.Bar(x=df["month_dt"], y=df["cortesias_en_platillos"], name="Cortesías"), row=2, col=1)
    fig_ops.add_trace(go.Bar(x=df["month_dt"], y=df["descuentos_en_platillos"], name="Descuentos"), row=2, col=1)
    fig_ops.update_layout(barmode="group", height=800, title="Operational Drivers from CashClosing")

    # --- Meseros: top 10 by sales (latest month) + boxplot ticket ---
    last_month = df.iloc[-1]["month"]
    m_last = meseros[meseros["month"] == last_month].copy().sort_values("ventas", ascending=False).head(10)

    fig_waiters = px.bar(
        m_last,
        x="Mesero",
        y="ventas",
        title=f"Top 10 Meseros by Sales — {last_month}",
        labels={"ventas":"Ventas"}
    )

    # Boxplot ticket per mesero (latest month)
    fig_waiters_box = px.box(
        meseros[meseros["month"] == last_month],
        x="Mesero",
        y="ticket_promedio",
        title=f"Distribution: Ticket promedio por Mesero — {last_month}"
    )

    # --- Mesas/Clientes: people per table monthly evolution ---
    fig_tables = px.line(
        mesas,
        x=to_month_dt(mesas["month"]),
        y="personas_por_mesa",
        markers=True,
        title="Clientes por mesa (monthly)",
        labels={"personas_por_mesa":"Personas por mesa", "x":"Month"}
    )

    # --- Monthly data-quality dashboard ---
    fig_quality = px.bar(
        df,
        x="month",
        y=df["delta_ventas_pct"]*100,
        color="status",
        title="Data Quality: Δ Ventas % (Orders vs CashClosing) by month",
        labels={"y":"Δ Ventas %"}
    )

    # Build HTML with sections (presentation style)
    css = """
    <style>
      body { font-family: Arial, sans-serif; margin: 0; background: #0b0f19; color: #e6e6e6; }
      .slide { padding: 30px 50px; page-break-after: always; }
      .title { font-size: 34px; font-weight: 800; margin-bottom: 8px; }
      .subtitle { font-size: 14px; color: #b6b6b6; margin-bottom: 18px; }
      .section { font-size: 22px; margin: 26px 0 10px 0; font-weight: 700; }
      .note { font-size: 12px; color: #b6b6b6; margin-top: 10px; }
      .bullets { font-size: 16px; line-height: 1.45; }
      .chip { display:inline-block; padding: 6px 10px; border-radius: 14px; margin-right: 6px; background:#1b2440; color:#e6e6e6; font-size:12px;}
      hr { border: 0; height: 1px; background: #27314f; margin: 18px 0; }
    </style>
    """

    # Executive bullets (auto)
    clean_ratio = (df["status"] != "REVIEW").mean()
    real_issues = df[df["is_real_issue"]]
    top_anom = df[df["is_real_issue"]].copy()
    top_anom["abs_delta"] = top_anom["delta_ventas_pct"].abs()
    top_anom = top_anom.sort_values("abs_delta", ascending=False).head(3)

    bullets = [
        f"Months analyzed: <b>{len(df)}</b> | Clean months: <b>{clean_ratio:.1%}</b>",
        f"Real issue months (excluding migrations): <b>{len(real_issues)}</b>",
    ]
    if not top_anom.empty:
        bullets.append("Top deviations (monthly): " + ", ".join([f"<b>{r['month']}</b> ({r['delta_ventas_pct']:.1%})" for _, r in top_anom.iterrows()]))

    html = css
    # Slide 1: Cover
    html += f"""
    <div class='slide'>
      <div class='title'>{title}</div>
      <div class='subtitle'>{subtitle}</div>
      <div>
        <span class='chip'>Branch keyword: {s.branch_keyword}</span>
        <span class='chip'>Wansoft subsidiary_id: {s.wansoft_subsidiary_id}</span>
        <span class='chip'>Start: {s.start_date}</span>
        <span class='chip'>End: {s.end_date}</span>
      </div>
      <hr>
      <div class='section'>Executive Highlights</div>
      <ul class='bullets'>
        {''.join([f"<li>{b}</li>" for b in bullets])}
      </ul>
      <div class='note'>
        Notes: Costs are taken from <b>costeomensual</b> (monthly cumulative; final of month). Operational KPIs are taken from <b>getglobalcashclosing</b> (cortesías/cancelaciones/anulaciones/descuentos). Sales are reported as totals. 
      </div>
    </div>
    """

    # Slide 2: KPI cards
    html += f"<div class='slide'><div class='section'>KPI Snapshot</div>{fig_cards.to_html(full_html=False, include_plotlyjs='cdn')}</div>"
    # Slide 3: evolution
    html += f"<div class='slide'><div class='section'>Evolution & Breakpoints</div>{fig_ts.to_html(full_html=False, include_plotlyjs=False)}</div>"
    # Slide 4: scatter
    html += f"<div class='slide'><div class='section'>Relationship: Ticket vs COGS</div>{fig_scatter.to_html(full_html=False, include_plotlyjs=False)}</div>"
    # Slide 5: operational drivers
    html += f"<div class='slide'><div class='section'>Operational Drivers (CashClosing)</div>{fig_ops.to_html(full_html=False, include_plotlyjs=False)}</div>"
    # Slide 6: waiters
    html += f"<div class='slide'><div class='section'>Waiters (Meseros)</div>{fig_waiters.to_html(full_html=False, include_plotlyjs=False)}<hr>{fig_waiters_box.to_html(full_html=False, include_plotlyjs=False)}</div>"
    # Slide 7: tables/clients
    html += f"<div class='slide'><div class='section'>Tables & Clients</div>{fig_tables.to_html(full_html=False, include_plotlyjs=False)}</div>"
    # Slide 8: data quality
    html += f"<div class='slide'><div class='section'>Data Quality & Reconciliation</div>{fig_quality.to_html(full_html=False, include_plotlyjs=False)}<div class='note'>Months marked as SYSTEM_MIGRATION should be interpreted with caution (system transition).</div></div>"

    return html


def main():
    ensure_dirs()

    # Load
    kpis, recon_m, ops = load_inputs()
    df = prepare_monthly_frame(kpis, recon_m, ops)
    breakpoints = compute_breakpoints(df)

    # Meseros / Mesas
    meseros, mesas, orders = build_meseros_mesas_monthly()

    # Save static heatmap (optional but very useful for ops)
    save_static_heatmaps(orders)

    # Save supporting CSVs
    breakpoints.to_csv("output/presentation/breakpoints.csv", index=False)
    meseros.to_csv("output/presentation/meseros_monthly.csv", index=False)
    mesas.to_csv("output/presentation/mesas_monthly.csv", index=False)

    # Build HTML
    html = build_dg_html(df, breakpoints, meseros, mesas)
    out_html = "output/presentation/dg_presentation.html"
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)

    print("\n✅ DG presentation generated:")
    print(f"- HTML: {out_html}")
    print("- CSVs: output/presentation/breakpoints.csv, meseros_monthly.csv, mesas_monthly.csv")
    print("- Figure: output/figures/heatmap_sales_dow_hour.png")


if __name__ == "__main__":
    main()