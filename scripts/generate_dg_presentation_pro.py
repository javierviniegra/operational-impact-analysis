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


# =========================
# IO / Setup
# =========================
def ensure_dirs():
    os.makedirs("output/presentation", exist_ok=True)
    os.makedirs("output/figures", exist_ok=True)
    os.makedirs("output/presentation/data", exist_ok=True)

def read_csv_safe(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing required file: {path}")
    return pd.read_csv(path)

def safe_num(s):
    return pd.to_numeric(s, errors="coerce")

def month_to_dt(m):
    return pd.to_datetime(m + "-01", errors="coerce")


# =========================
# Load inputs produced by validate_all
# =========================
def load_inputs():
    kpis = read_csv_safe("output/datasets/kpis_monthly.csv")
    recon_m = read_csv_safe("output/datasets/reconciliation_monthly.csv")
    recon_d = read_csv_safe("output/datasets/reconciliation_daily.csv")
    ops = read_csv_safe("output/datasets/kpis_operational.csv")
    return kpis, recon_m, recon_d, ops


# =========================
# Prepare monthly executive frame
# =========================
def prepare_monthly_frame(kpis, recon_m, ops):
    # Ensure columns exist
    if "delta_ventas_pct" not in recon_m.columns:
        recon_m["delta_ventas_pct"] = np.nan
    if "source_flag" not in recon_m.columns:
        recon_m["source_flag"] = "OK"
    if "status" not in recon_m.columns:
        recon_m["status"] = "OK"
    if "note" not in recon_m.columns:
        recon_m["note"] = ""

    df = kpis.merge(
        recon_m[["month", "branch", "status", "source_flag", "note", "delta_ventas_pct"]],
        on="month",
        how="left"
    ).merge(
        ops, on="month", how="left"
    )

    # Numeric coercion for core KPIs
    num_cols = [
        "Ventas", "Tickets", "Personas", "Ticket_Promedio", "Cheque_Promedio",
        "CostoTotal", "COGS_%", "Margen", "Margen_%",
        "delta_ventas_pct",
        "cortesias_en_platillos", "cancelaciones_en_platillos",
        "anulaciones_en_platillos", "descuentos_en_platillos"
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = safe_num(df[c])

    # Derived safety
    if "COGS_%" not in df.columns or df["COGS_%"].isna().all():
        df["COGS_%"] = df["CostoTotal"] / df["Ventas"]
    if "Margen" not in df.columns or df["Margen"].isna().all():
        df["Margen"] = df["Ventas"] - df["CostoTotal"]
    if "Margen_%" not in df.columns or df["Margen_%"].isna().all():
        df["Margen_%"] = df["Margen"] / df["Ventas"]

    df["month_dt"] = month_to_dt(df["month"])
    df = df.sort_values("month_dt")

    # Real issue months: REVIEW excluding known system migrations
    df["is_real_issue"] = (df["status"] == "REVIEW") & (df["source_flag"] == "OK")

    return df


# =========================
# Breakpoints (inflection points)
# =========================
def compute_breakpoints(df):
    out = df[["month", "month_dt", "Ventas", "COGS_%", "Margen_%", "delta_ventas_pct", "status", "source_flag", "note", "is_real_issue"]].copy()
    out = out.sort_values("month_dt")

    out["ventas_mom_pct"] = out["Ventas"].pct_change()
    out["cogs_mom_pp"] = out["COGS_%"].diff() * 100
    out["margen_mom_pp"] = out["Margen_%"].diff() * 100

    out["break_score"] = (
        out["ventas_mom_pct"].abs().fillna(0) * 1.0 +
        (out["cogs_mom_pp"].abs().fillna(0) / 10.0) * 0.7 +
        (out["margen_mom_pp"].abs().fillna(0) / 10.0) * 0.7 +
        out["delta_ventas_pct"].abs().fillna(0) * 1.2
    )

    # Top 10% as breakpoints
    q = out["break_score"].quantile(0.90) if out["break_score"].notna().any() else 0
    out["is_breakpoint"] = out["break_score"] >= q
    return out


# =========================
# Orders-based operational analytics (meseros / mesas / horarios)
# =========================
def load_orders_for_ops():
    orders = load_orders()

    # Parse date/time
    orders["Fecha_dt"] = pd.to_datetime(orders["Fecha"], errors="coerce")
    orders["month"] = orders["Fecha_dt"].dt.to_period("M").astype(str)

    # Core numeric
    orders["Total_num"] = safe_num(orders["Total"]).fillna(0)
    orders["Personas_num"] = safe_num(orders["Personas"]).fillna(0)

    # Parse hora apertura/cierre
    orders["HoraApertura_dt"] = pd.to_datetime(orders["HoraApertura"], errors="coerce")
    orders["HoraCierre_dt"] = pd.to_datetime(orders["HoraCierre"], errors="coerce")

    return orders


def build_meseros_monthly(orders):
    # Mesero monthly
    if "Movimento" in orders.columns:
        ticket_key = "Movimento"
    else:
        ticket_key = "Orden"

    m = (orders.groupby(["month", "Mesero"], as_index=False)
         .agg(
             ventas=("Total_num", "sum"),
             tickets=(ticket_key, "nunique"),
             personas=("Personas_num", "sum"),
             mesas=("Mesa", "nunique")
         ))

    m["ticket_promedio"] = m["ventas"] / m["tickets"].replace({0: np.nan})
    m["personas_por_mesa"] = m["personas"] / m["mesas"].replace({0: np.nan})
    m["month_dt"] = month_to_dt(m["month"])
    m = m.sort_values(["Mesero", "month_dt"])

    # Evolution signals
    m["ventas_mom_pct"] = m.groupby("Mesero")["ventas"].pct_change()
    m["drop_flag"] = m["ventas_mom_pct"] <= -0.20  # -20% MoM (configurable)

    return m


def build_mesas_monthly(orders):
    if "Movimento" in orders.columns:
        ticket_key = "Movimento"
    else:
        ticket_key = "Orden"

    t = (orders.groupby(["month"], as_index=False)
         .agg(
             ventas=("Total_num", "sum"),
             tickets=(ticket_key, "nunique"),
             personas=("Personas_num", "sum"),
             mesas=("Mesa", "nunique")
         ))
    t["personas_por_mesa"] = t["personas"] / t["mesas"].replace({0: np.nan})
    t["ticket_promedio"] = t["ventas"] / t["tickets"].replace({0: np.nan})
    t["month_dt"] = month_to_dt(t["month"])
    return t.sort_values("month_dt")


def heatmap_dow_hour(orders, metric="ventas"):
    o = orders.dropna(subset=["HoraApertura_dt"]).copy()
    o["dow"] = o["HoraApertura_dt"].dt.day_name()
    o["hour"] = o["HoraApertura_dt"].dt.hour

    if metric == "ventas":
        o["value"] = o["Total_num"]
        title = "Heatmap: Ventas por día de semana vs hora"
        fname = "heatmap_sales_dow_hour.png"
    elif metric == "tickets":
        o["value"] = 1
        title = "Heatmap: Tickets por día de semana vs hora"
        fname = "heatmap_tickets_dow_hour.png"
    elif metric == "personas":
        o["value"] = o["Personas_num"]
        title = "Heatmap: Personas por día de semana vs hora"
        fname = "heatmap_people_dow_hour.png"
    else:
        return

    piv = (o.groupby(["dow", "hour"])["value"].sum()
           .reset_index()
           .pivot(index="dow", columns="hour", values="value")
           .fillna(0))

    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    piv = piv.reindex(dow_order)

    plt.figure(figsize=(18, 6))
    sns.heatmap(piv, cmap="YlOrRd")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(f"output/figures/{fname}", dpi=150)
    plt.close()


def heatmap_waiters_month(meseros, top_n=25):
    # Select top N waiters by total sales
    total_by_waiter = meseros.groupby("Mesero")["ventas"].sum().sort_values(ascending=False).head(top_n)
    m = meseros[meseros["Mesero"].isin(total_by_waiter.index)].copy()

    piv = m.pivot_table(index="Mesero", columns="month", values="ventas", aggfunc="sum").fillna(0)

    plt.figure(figsize=(18, 10))
    sns.heatmap(piv, cmap="viridis")
    plt.title(f"Heatmap: Ventas por Mesero vs Mes (Top {top_n})")
    plt.tight_layout()
    plt.savefig("output/figures/heatmap_waiters_sales_by_month.png", dpi=150)
    plt.close()


# =========================
# Executive decisions (auto)
# =========================
def generate_executive_decisions(df_monthly, breakpoints):
    """
    Produces bullets (recommendations) based on:
    - Real issue months
    - Breakpoints
    - Operational driver spikes
    """
    bullets = []

    total_months = len(df_monthly)
    clean_months = (df_monthly["status"] != "REVIEW").mean()
    real_issues = df_monthly[df_monthly["is_real_issue"]].copy()

    bullets.append(f"Months analyzed: {total_months}. Clean months: {clean_months:.1%}.")
    bullets.append(f"Real issue months (excluding migrations): {len(real_issues)}.")

    # Top anomalies by abs delta
    if "delta_ventas_pct" in df_monthly.columns:
        a = df_monthly[df_monthly["is_real_issue"]].copy()
        a["abs_delta"] = a["delta_ventas_pct"].abs()
        a = a.sort_values("abs_delta", ascending=False).head(3)
        if not a.empty:
            bullets.append("Top deviations (Orders vs CashClosing): " +
                           ", ".join([f"{r['month']} ({r['delta_ventas_pct']:.1%})" for _, r in a.iterrows()]))

    # Suggest operational focus based on drivers
    # (No claims; only rule-based recommendations)
    if not real_issues.empty:
        worst = real_issues.copy()
        worst["abs_delta"] = worst["delta_ventas_pct"].abs()
        worst = worst.sort_values("abs_delta", ascending=False).head(1).iloc[0]
        m = worst["month"]

        drivers = df_monthly[df_monthly["month"] == m][[
            "cortesias_en_platillos", "cancelaciones_en_platillos", "anulaciones_en_platillos", "descuentos_en_platillos"
        ]].fillna(0).iloc[0]

        # Heuristic recommendations
        if drivers["anulaciones_en_platillos"] >= 5000:
            bullets.append(f"Decision: Investigate high anulaciones in {m} (process discipline, voiding workflow, training).")
        if drivers["cancelaciones_en_platillos"] >= 1000:
            bullets.append(f"Decision: Review cancellations in {m} (kitchen/service coordination, delivery fulfillment, rework).")
        if drivers["cortesias_en_platillos"] >= 2000:
            bullets.append(f"Decision: Audit cortesías policy and approvals in {m} (leakage control).")
        if drivers["descuentos_en_platillos"] >= 3000:
            bullets.append(f"Decision: Validate discount strategy and operational controls in {m} (promo vs leakage).")

    # Breakpoints: flag for review sessions
    bp = breakpoints[breakpoints["is_breakpoint"]].copy()
    bp_real = bp[(bp["status"] == "REVIEW") & (bp["source_flag"] == "OK")].head(3)
    if not bp_real.empty:
        bullets.append("Decision: Run deep-dive sessions on breakpoints: " +
                       ", ".join([f"{x}" for x in bp_real["month"].tolist()]))

    return bullets


# =========================
# Build DG Presentation HTML (deck style)
# =========================
def build_presentation_html(df, breakpoints, meseros, mesas):
    s = get_scope()
    title = f"Executive Operational Report — Branch Evolution"
    subtitle = f"Branch scope keyword: {s.branch_keyword} | Wansoft subsidiary_id: {s.wansoft_subsidiary_id} | Period: {s.start_date} → {s.end_date}"

    # Latest month snapshot
    latest = df.dropna(subset=["month_dt"]).iloc[-1]

    # KPI Cards
    fig_cards = make_subplots(rows=2, cols=4, specs=[[{"type":"indicator"}]*4,[{"type":"indicator"}]*4],
                              subplot_titles=("Ventas","COGS %","Margen %","Ticket Promedio",
                                             "Cheque Promedio","Personas","% Delivery","Δ Ventas %"))

    def add_indicator(r, c, label, value, fmt=",.2f", suffix=""):
        fig_cards.add_trace(go.Indicator(
            mode="number",
            value=float(value) if pd.notna(value) else 0,
            title={"text": f"<b>{label}</b><br><span style='font-size:0.8em;color:gray'>{suffix}</span>"},
            number={"valueformat": fmt}
        ), row=r, col=c)

    add_indicator(1,1,"Ventas", latest["Ventas"], ",.0f", "Total")
    add_indicator(1,2,"COGS %", latest["COGS_%"]*100, ",.2f", "Costs / Sales")
    add_indicator(1,3,"Margen %", latest["Margen_%"]*100, ",.2f", "Sales - Costs")
    add_indicator(1,4,"Ticket", latest.get("Ticket_Promedio", np.nan), ",.0f", "Ventas / Tickets")
    add_indicator(2,1,"Cheque", latest.get("Cheque_Promedio", np.nan), ",.0f", "Ventas / Personas")
    add_indicator(2,2,"Personas", latest.get("Personas", np.nan), ",.0f", "Monthly")
    add_indicator(2,3,"% Delivery", latest.get("%_Delivery", 0)*100, ",.2f", "Sales share")
    add_indicator(2,4,"Δ Ventas %", latest.get("delta_ventas_pct", 0)*100, ",.2f", "Orders vs CashClosing")

    fig_cards.update_layout(height=520, title="KPI Snapshot (Latest Month)")

    # Timeline: Sales / COGS / Margin + breakpoints
    fig_ts = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                           specs=[[{"secondary_y": True}], [{"secondary_y": True}]],
                           subplot_titles=("Ventas vs COGS% (Monthly)", "Margen% + Mix"))

    fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df["Ventas"], mode="lines+markers", name="Ventas"), row=1, col=1, secondary_y=False)
    fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df["COGS_%"]*100, mode="lines+markers", name="COGS %"), row=1, col=1, secondary_y=True)

    bp = breakpoints[breakpoints["is_breakpoint"]].copy()
    if not bp.empty:
        fig_ts.add_trace(go.Scatter(
            x=bp["month_dt"],
            y=df.set_index("month_dt").loc[bp["month_dt"], "Ventas"].values,
            mode="markers",
            marker=dict(size=10, symbol="x", color="red"),
            name="Breakpoints"
        ), row=1, col=1, secondary_y=False)

    fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df["Margen_%"]*100, mode="lines+markers", name="Margen %"), row=2, col=1, secondary_y=False)
    for col, label in [("%_Delivery","% Delivery"),("%_Salon","% Salón"),("%_Llevar","% Llevar")]:
        if col in df.columns:
            fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df[col]*100, mode="lines", name=label), row=2, col=1, secondary_y=True)

    fig_ts.update_layout(height=820, title="Monthly Evolution & Inflection Points")

    # Scatter: Ticket vs COGS% colored by % Delivery
    fig_scatter = px.scatter(
        df,
        x="Ticket_Promedio",
        y=df["COGS_%"]*100,
        size="Ventas",
        color=df.get("%_Delivery", 0),
        hover_data=["month","status","source_flag","delta_ventas_pct","note"],
        title="Scatter: Ticket vs COGS% (size=Ventas, color=%Delivery)",
        labels={"y":"COGS (%)", "color":"% Delivery"}
    )

    # Operational drivers
    fig_ops = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            subplot_titles=("Anulaciones/Cancelaciones", "Cortesías/Descuentos"))
    fig_ops.add_trace(go.Bar(x=df["month_dt"], y=df["anulaciones_en_platillos"], name="Anulaciones"), row=1, col=1)
    fig_ops.add_trace(go.Bar(x=df["month_dt"], y=df["cancelaciones_en_platillos"], name="Cancelaciones"), row=1, col=1)
    fig_ops.add_trace(go.Bar(x=df["month_dt"], y=df["cortesias_en_platillos"], name="Cortesías"), row=2, col=1)
    fig_ops.add_trace(go.Bar(x=df["month_dt"], y=df["descuentos_en_platillos"], name="Descuentos"), row=2, col=1)
    fig_ops.update_layout(barmode="group", height=820, title="Operational Drivers (CashClosing)")

    # Meseros: evolution (top N)
    last_month = df.iloc[-1]["month"]
    total_by_waiter = meseros.groupby("Mesero")["ventas"].sum().sort_values(ascending=False).head(15).index
    m_top = meseros[meseros["Mesero"].isin(total_by_waiter)].copy()
    fig_waiter_ts = px.line(
        m_top, x="month_dt", y="ventas", color="Mesero",
        title="Meseros: evolución de ventas (Top 15)",
        labels={"ventas":"Ventas"}
    )

    # Meseros: who dropped (flag)
    drops = meseros[meseros["drop_flag"]].copy()
    fig_waiter_drops = px.scatter(
        drops, x="month_dt", y="ventas_mom_pct", color="Mesero",
        title="Meseros: caídas fuertes (MoM <= -20%)",
        labels={"ventas_mom_pct":"Cambio MoM"}
    )

    # Meseros: ranking last month
    m_last = meseros[meseros["month"] == last_month].copy().sort_values("ventas", ascending=False).head(10)
    fig_waiter_rank = px.bar(
        m_last, x="Mesero", y="ventas",
        title=f"Top 10 Meseros por ventas — {last_month}"
    )

    # Meseros: boxplot ticket promedio last month
    fig_waiter_box = px.box(
        meseros[meseros["month"] == last_month],
        x="Mesero", y="ticket_promedio",
        title=f"Distribución: Ticket promedio por Mesero — {last_month}"
    )

    # Tables/clients evolution
    fig_tables = px.line(
        mesas, x="month_dt", y="personas_por_mesa", markers=True,
        title="Clientes por mesa (monthly)",
        labels={"personas_por_mesa":"Personas por mesa"}
    )

    # Data quality
    fig_quality = px.bar(
        df, x="month", y=df["delta_ventas_pct"]*100, color="status",
        title="Data Quality: Δ Ventas % (Orders vs CashClosing)",
        labels={"y":"Δ Ventas %"}
    )

    # Executive decisions bullets
    decisions = generate_executive_decisions(df, breakpoints)

    # CSS presentation style
    css = """
    <style>
      body { font-family: Arial, sans-serif; margin:0; background:#0b0f19; color:#e6e6e6; }
      .slide { padding: 34px 56px; page-break-after: always; }
      .title { font-size: 36px; font-weight: 800; margin-bottom: 8px; }
      .subtitle { font-size: 14px; color: #b6b6b6; margin-bottom: 18px; }
      .section { font-size: 22px; margin: 26px 0 10px 0; font-weight: 700; }
      .bullets { font-size: 16px; line-height: 1.5; }
      .chip { display:inline-block; padding:6px 10px; border-radius:14px; margin-right:6px; background:#1b2440; color:#e6e6e6; font-size:12px; }
      hr { border:0; height:1px; background:#27314f; margin:18px 0; }
      .note { font-size: 12px; color:#b6b6b6; margin-top:10px; }
    </style>
    """

    # Build HTML slides
    html = css

    # Slide 1: cover + executive highlights + decisions
    html += f"""
    <div class='slide'>
      <div class='title'>{title}</div>
      <div class='subtitle'>{subtitle}</div>
      <div>
        <span class='chip'>Branch keyword: {s.branch_keyword}</span>
        <span class='chip'>subsidiary_id: {s.wansoft_subsidiary_id}</span>
        <span class='chip'>Start: {s.start_date}</span>
        <span class='chip'>End: {s.end_date}</span>
      </div>
      <hr>
      <div class='section'>Executive Summary</div>
      <ul class='bullets'>
        {''.join([f"<li>{d}</li>" for d in decisions])}
      </ul>
      <div class='note'>
        Methodology: Sales reported as totals. Costs from <b>costeomensual</b> (monthly cumulative; final-of-month value). Operational KPIs from <b>getglobalcashclosing</b> (cortesías/cancelaciones/anulaciones/descuentos). 【1-0e2255】【2-dbd516】
      </div>
    </div>
    """

    # Slide 2: KPI Cards
    html += f"<div class='slide'><div class='section'>KPI Snapshot (Latest Month)</div>{fig_cards.to_html(full_html=False, include_plotlyjs='cdn')}</div>"

    # Slide 3: Evolution + breakpoints
    html += f"<div class='slide'><div class='section'>Evolution & Breakpoints</div>{fig_ts.to_html(full_html=False, include_plotlyjs=False)}</div>"

    # Slide 4: Ticket vs COGS scatter
    html += f"<div class='slide'><div class='section'>Relationship: Ticket vs COGS</div>{fig_scatter.to_html(full_html=False, include_plotlyjs=False)}</div>"

    # Slide 5: Operational drivers
    html += f"<div class='slide'><div class='section'>Operational Drivers (CashClosing)</div>{fig_ops.to_html(full_html=False, include_plotlyjs=False)}</div>"

    # Slide 6: Waiters (evolution + drops)
    html += f"<div class='slide'><div class='section'>Meseros — Evolution</div>{fig_waiter_ts.to_html(full_html=False, include_plotlyjs=False)}<hr>{fig_waiter_drops.to_html(full_html=False, include_plotlyjs=False)}</div>"

    # Slide 7: Waiters (ranking + distribution)
    html += f"<div class='slide'><div class='section'>Meseros — Ranking & Distribution</div>{fig_waiter_rank.to_html(full_html=False, include_plotlyjs=False)}<hr>{fig_waiter_box.to_html(full_html=False, include_plotlyjs=False)}</div>"

    # Slide 8: Tables/clients
    html += f"<div class='slide'><div class='section'>Mesas & Clientes</div>{fig_tables.to_html(full_html=False, include_plotlyjs=False)}</div>"

    # Slide 9: Data quality
    html += f"<div class='slide'><div class='section'>Data Quality (Reconciliation)</div>{fig_quality.to_html(full_html=False, include_plotlyjs=False)}<div class='note'>Months flagged SYSTEM_MIGRATION should be interpreted with caution (system transition).</div></div>"

    # Slide 10: Appendices (static heatmaps links)
    html += f"""
    <div class='slide'>
      <div class='section'>Appendix — Heatmaps & Files</div>
      <ul class='bullets'>
        <li>Heatmap ventas (dow x hour): <b>output/figures/heatmap_sales_dow_hour.png</b></li>
        <li>Heatmap tickets (dow x hour): <b>output/figures/heatmap_tickets_dow_hour.png</b></li>
        <li>Heatmap personas (dow x hour): <b>output/figures/heatmap_people_dow_hour.png</b></li>
        <li>Heatmap meseros ventas vs mes: <b>output/figures/heatmap_waiters_sales_by_month.png</b></li>
      </ul>
      <div class='note'>You can paste these images directly into PowerPoint if needed.</div>
    </div>
    """

    return html


# =========================
# Main
# =========================
def main():
    ensure_dirs()

    # Load monthly sources
    kpis, recon_m, recon_d, ops = load_inputs()
    df_monthly = prepare_monthly_frame(kpis, recon_m, ops)
    breakpoints = compute_breakpoints(df_monthly)

    # Load orders for ops analytics
    orders = load_orders_for_ops()
    meseros = build_meseros_monthly(orders)
    mesas = build_mesas_monthly(orders)

    # Save operational tables for reuse
    breakpoints.to_csv("output/presentation/data/breakpoints.csv", index=False)
    meseros.to_csv("output/presentation/data/meseros_monthly.csv", index=False)
    mesas.to_csv("output/presentation/data/mesas_monthly.csv", index=False)

    # Generate static heatmaps (required by your request)
    heatmap_dow_hour(orders, metric="ventas")
    heatmap_dow_hour(orders, metric="tickets")
    heatmap_dow_hour(orders, metric="personas")
    heatmap_waiters_month(meseros, top_n=25)

    # Build HTML deck
    html = build_presentation_html(df_monthly, breakpoints, meseros, mesas)
    out_html = "output/presentation/dg_presentation_pro.html"
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)

    print("\n✅ DG PRO presentation generated:")
    print(f"- HTML: {out_html}")
    print("- Data: output/presentation/data/*.csv")
    print("- Figures: output/figures/*.png")


if __name__ == "__main__":
    main()
