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

# ✅ helper central de cuadrantes (mediana)
from src.transform.quadrant_scatter import quadrant_scatter_plotly


# -----------------------------
# Utils
# -----------------------------
def ensure_dirs():
    os.makedirs("output/presentation", exist_ok=True)
    os.makedirs("output/figures", exist_ok=True)
    os.makedirs("output/presentation/data", exist_ok=True)

def safe_num(s):
    return pd.to_numeric(s, errors="coerce")

def month_to_dt(m):
    return pd.to_datetime(m + "-01", errors="coerce")

def read_csv(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Falta el archivo requerido: {path}")
    return pd.read_csv(path)


# -----------------------------
# Load datasets (from pipeline)
# -----------------------------
def load_inputs():
    kpis = read_csv("output/datasets/kpis_monthly.csv")
    recon_m = read_csv("output/datasets/reconciliation_monthly.csv")
    ops = read_csv("output/datasets/kpis_operational.csv")
    return kpis, recon_m, ops


def prepare_monthly_frame(kpis, recon_m, ops):
    # defensivo
    if "delta_ventas_pct" not in recon_m.columns:
        recon_m["delta_ventas_pct"] = np.nan
    if "source_flag" not in recon_m.columns:
        recon_m["source_flag"] = "OK"
    if "status" not in recon_m.columns:
        recon_m["status"] = "OK"
    if "note" not in recon_m.columns:
        recon_m["note"] = ""

    df = (
        kpis.merge(
            recon_m[["month", "branch", "status", "source_flag", "note", "delta_ventas_pct"]],
            on="month", how="left"
        )
        .merge(ops, on="month", how="left")
    )

    # numéricos
    for c in [
        "Ventas","Tickets","Personas","Ticket_Promedio","Cheque_Promedio","CostoTotal",
        "COGS_%","Margen","Margen_%","delta_ventas_pct",
        "cortesias_en_platillos","cancelaciones_en_platillos","anulaciones_en_platillos","descuentos_en_platillos",
        "Ventas_Salon","Ventas_Delivery","Ventas_Llevar","Ventas_Otros","Ventas_Unknown",
        "%_Salon","%_Delivery","%_Llevar","%_Otros","%_Unknown"
    ]:
        if c in df.columns:
            df[c] = safe_num(df[c])

    # derivados seguros
    if "COGS_%" not in df.columns or df["COGS_%"].isna().all():
        df["COGS_%"] = df["CostoTotal"] / df["Ventas"]
    if "Margen" not in df.columns or df["Margen"].isna().all():
        df["Margen"] = df["Ventas"] - df["CostoTotal"]
    if "Margen_%" not in df.columns or df["Margen_%"].isna().all():
        df["Margen_%"] = df["Margen"] / df["Ventas"]

    df["month_dt"] = month_to_dt(df["month"])
    df = df.sort_values("month_dt")
    df["is_real_issue"] = (df["status"] == "REVIEW") & (df["source_flag"] == "OK")
    return df


# -----------------------------
# Breakpoints
# -----------------------------
def compute_breakpoints(df):
    out = df[["month","month_dt","Ventas","COGS_%","Margen_%","delta_ventas_pct","status","source_flag","note"]].copy()
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
    q = out["break_score"].quantile(0.90) if out["break_score"].notna().any() else 0
    out["is_breakpoint"] = out["break_score"] >= q
    return out


# -----------------------------
# Orders analytics (meseros/mesas/horarios)
# -----------------------------
def load_orders_ops():
    orders = load_orders()
    orders["Fecha_dt"] = pd.to_datetime(orders["Fecha"], errors="coerce")
    orders["month"] = orders["Fecha_dt"].dt.to_period("M").astype(str)

    orders["Total_num"] = safe_num(orders["Total"]).fillna(0)
    orders["Personas_num"] = safe_num(orders["Personas"]).fillna(0)

    orders["HoraApertura_dt"] = pd.to_datetime(orders["HoraApertura"], errors="coerce")
    return orders


def build_meseros_monthly(orders):
    key = "Movimento" if "Movimento" in orders.columns else "Orden"
    m = (orders.groupby(["month","Mesero"], as_index=False)
         .agg(
             ventas=("Total_num","sum"),
             tickets=(key,"nunique"),
             personas=("Personas_num","sum"),
             mesas=("Mesa","nunique")
         ))

    m["ticket_promedio"] = m["ventas"] / m["tickets"].replace({0: np.nan})
    m["personas_por_mesa"] = m["personas"] / m["mesas"].replace({0: np.nan})
    m["month_dt"] = month_to_dt(m["month"])
    m = m.sort_values(["Mesero","month_dt"])

    m["ventas_mom_pct"] = m.groupby("Mesero")["ventas"].pct_change()
    m["drop_flag"] = m["ventas_mom_pct"] <= -0.20
    return m


def build_mesas_monthly(orders):
    key = "Movimento" if "Movimento" in orders.columns else "Orden"
    t = (orders.groupby(["month"], as_index=False)
         .agg(
             ventas=("Total_num","sum"),
             tickets=(key,"nunique"),
             personas=("Personas_num","sum"),
             mesas=("Mesa","nunique")
         ))

    t["personas_por_mesa"] = t["personas"] / t["mesas"].replace({0: np.nan})
    t["ticket_promedio"] = t["ventas"] / t["tickets"].replace({0: np.nan})
    t["month_dt"] = month_to_dt(t["month"])
    return t.sort_values("month_dt")


def save_heatmaps(orders):
    o = orders.dropna(subset=["HoraApertura_dt"]).copy()
    o["dow"] = o["HoraApertura_dt"].dt.day_name()
    o["hour"] = o["HoraApertura_dt"].dt.hour

    def heat(metric, title, fname):
        if metric == "ventas":
            o["value"] = o["Total_num"]
        elif metric == "tickets":
            o["value"] = 1
        else:
            o["value"] = o["Personas_num"]

        piv = (o.groupby(["dow","hour"])["value"].sum()
               .reset_index()
               .pivot(index="dow", columns="hour", values="value")
               .fillna(0))
        dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        piv = piv.reindex(dow_order)

        plt.figure(figsize=(18,6))
        sns.heatmap(piv, cmap="YlOrRd")
        plt.title(title)
        plt.tight_layout()
        plt.savefig(f"output/figures/{fname}", dpi=150)
        plt.close()

    heat("ventas",  "Heatmap: Ventas (día semana x hora)",   "heatmap_ventas_dow_hour.png")
    heat("tickets", "Heatmap: Tickets (día semana x hora)",  "heatmap_tickets_dow_hour.png")
    heat("personas","Heatmap: Personas (día semana x hora)", "heatmap_personas_dow_hour.png")


# -----------------------------
# Correlations (monthly)
# -----------------------------
def correlation_panel(df):
    cols = ["Ventas","Ticket_Promedio","Cheque_Promedio","COGS_%","Margen_%","%_Delivery","Personas"]
    cols = [c for c in cols if c in df.columns]
    corr = df[cols].corr(numeric_only=True)

    fig = px.imshow(
        corr,
        text_auto=True,
        title="Matriz de correlación (mensual)",
        aspect="auto",
        color_continuous_scale="RdBu",
        zmin=-1, zmax=1
    )
    fig.update_layout(height=650)
    return fig


# -----------------------------
# Scatter slides (mes / mesero) usando MEDIANA
# -----------------------------
def build_scatter_slides(df_monthly, mesas_df, meseros_df):
    # ---- Slide por MES ----
    dm = df_monthly.copy()
    dm["year"] = pd.to_datetime(dm["month"] + "-01").dt.year

    md = mesas_df.copy()
    md["year"] = pd.to_datetime(md["month"] + "-01").dt.year

    hover_mes = ["month","Ventas","Tickets","Personas","Ticket_Promedio","Cheque_Promedio","COGS_%","Margen_%","%_Delivery","status","source_flag"]

    f1,_,_ = quadrant_scatter_plotly(dm, "Tickets", "Ventas", "month",
        "Cuadrantes (mediana): Ventas vs Tickets (mensual)",
        color="year", size="Personas", hover=hover_mes, show_colorbar=True)

    f2,_,_ = quadrant_scatter_plotly(dm, "Tickets", "Ticket_Promedio", "month",
        "Cuadrantes (mediana): Ticket Promedio vs Tickets (mensual)",
        color="year", size="Ventas", hover=hover_mes)

    f3,_,_ = quadrant_scatter_plotly(dm, "Personas", "Cheque_Promedio", "month",
        "Cuadrantes (mediana): Cheque Promedio vs Personas (mensual)",
        color="year", size="Ventas", hover=hover_mes)

    # Mesas vs Personas (usa columnas de build_mesas_monthly)
    f4,_,_ = quadrant_scatter_plotly(md, "mesas", "personas", "month",
        "Cuadrantes (mediana): Mesas vs Personas (mensual)",
        color="year", size="ventas", hover=["month","mesas","personas","ventas"])

    f5,_,_ = quadrant_scatter_plotly(dm, "%_Delivery", "Ticket_Promedio", "month",
        "Cuadrantes (mediana): % Delivery vs Ticket Promedio (mensual)",
        color="year", size="Ventas", hover=hover_mes)

    f6,_,_ = quadrant_scatter_plotly(dm, "Ventas", "COGS_%", "month",
        "Cuadrantes (mediana): Ventas vs COGS% (mensual)",
        color="year", size="Tickets", hover=hover_mes)

    # ---- Slide por MESERO (último mes, activos desde 2025) ----
    m = meseros_df.copy()
    m["month_dt"] = month_to_dt(m["month"])
    m = m[m["month_dt"].dt.year >= 2025]
    m = m.groupby("Mesero").filter(lambda x: x["ventas"].sum() > 0)

    last_month = m["month"].max()
    ml = m[m["month"] == last_month].copy()

    hover_mesero = ["month","Mesero","ventas","tickets","personas","mesas","ticket_promedio","personas_por_mesa"]

    w1,_,_ = quadrant_scatter_plotly(ml, "personas", "ventas", "Mesero",
        f"Cuadrantes (mediana): Meseros — Ventas vs Clientes (último mes {last_month})",
        size="tickets", hover=hover_mesero, median_scope_df=ml)

    w2,_,_ = quadrant_scatter_plotly(ml, "personas_por_mesa", "ticket_promedio", "Mesero",
        f"Cuadrantes (mediana): Meseros — Ticket vs Personas/Mesa (último mes {last_month})",
        size="ventas", hover=hover_mesero, median_scope_df=ml)

    w3,_,_ = quadrant_scatter_plotly(ml, "tickets", "ticket_promedio", "Mesero",
        f"Cuadrantes (mediana): Meseros — Tickets vs Ticket (último mes {last_month})",
        size="ventas", hover=hover_mesero, median_scope_df=ml)

    w4,_,_ = quadrant_scatter_plotly(ml, "mesas", "ventas", "Mesero",
        f"Cuadrantes (mediana): Meseros — Ventas vs Mesas (último mes {last_month})",
        size="personas", hover=hover_mesero, median_scope_df=ml)

    return {"mes": [f1, f2, f3, f4, f5, f6], "mesero": [w1, w2, w3, w4], "last_month": last_month}


# -----------------------------
# Build FULL HTML deck
# -----------------------------
def build_html(df, breakpoints, meseros, mesas, orders):
    s = get_scope()

    css = """
    <style>
      body { font-family: Arial, sans-serif; margin:0; background:#0b0f19; color:#e6e6e6; }
      .slide { padding: 34px 56px; page-break-after: always; }
      .title { font-size: 36px; font-weight: 800; margin-bottom: 8px; }
      .subtitle { font-size: 14px; color: #b6b6b6; margin-bottom: 18px; }
      .section { font-size: 22px; margin: 26px 0 10px 0; font-weight: 700; }
      hr { border:0; height:1px; background:#27314f; margin:18px 0; }
      .note { font-size: 12px; color:#b6b6b6; margin-top:10px; }
    </style>
    """

    html = css
    html += f"""
    <div class='slide'>
      <div class='title'>Reporte Ejecutivo — Evolución de Sucursal (DG)</div>
      <div class='subtitle'>Sucursal (keyword): {s.branch_keyword} | subsidiary_id: {s.wansoft_subsidiary_id} | Periodo: {s.start_date} → {s.end_date}</div>
      <div class='note'>Cuadrantes: cortes por <b>mediana</b> (robusto a outliers). Heatmaps se guardan como PNG en output/figures.</div>
    </div>
    """

    # --- Evolución mensual (líneas + mix + breakpoints) ---
    fig_ts = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.10,
        specs=[[{"secondary_y": True}], [{"secondary_y": True}], [{"secondary_y": False}]],
        subplot_titles=("Ventas vs COGS%","Ticket/Cheque/Clientes","Mix por canal")
    )

    fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df["Ventas"], mode="lines+markers", name="Ventas"),
                     row=1, col=1, secondary_y=False)
    fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df["COGS_%"]*100, mode="lines+markers", name="COGS %"),
                     row=1, col=1, secondary_y=True)

    bp = breakpoints[breakpoints["is_breakpoint"]]
    if not bp.empty:
        fig_ts.add_trace(go.Scatter(
            x=bp["month_dt"],
            y=df.set_index("month_dt").loc[bp["month_dt"], "Ventas"].values,
            mode="markers",
            marker=dict(size=10, symbol="x", color="red"),
            name="Puntos de ruptura"
        ), row=1, col=1, secondary_y=False)

    fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df["Ticket_Promedio"], mode="lines", name="Ticket"),
                     row=2, col=1, secondary_y=False)
    fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df["Cheque_Promedio"], mode="lines", name="Cheque"),
                     row=2, col=1, secondary_y=False)
    fig_ts.add_trace(go.Scatter(x=df["month_dt"], y=df["Personas"], mode="lines", name="Clientes (Personas)"),
                     row=2, col=1, secondary_y=True)

    for col, label in [("Ventas_Salon","Salón"),("Ventas_Delivery","Delivery"),("Ventas_Llevar","Llevar"),("Ventas_Otros","Otros")]:
        if col in df.columns:
            fig_ts.add_trace(go.Bar(x=df["month_dt"], y=df[col], name=label), row=3, col=1)

    fig_ts.update_layout(height=1000, barmode="stack", title="Evolución mensual y puntos de inflexión")

    html += f"<div class='slide'><div class='section'>Evolución mensual (líneas + mix)</div>{fig_ts.to_html(full_html=False, include_plotlyjs='cdn')}</div>"

    # --- Correlaciones ---
    fig_corr = correlation_panel(df)
    html += f"<div class='slide'><div class='section'>Correlaciones (mensual)</div>{fig_corr.to_html(full_html=False, include_plotlyjs=False)}</div>"

    # --- Drivers operativos ---
    fig_ops = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            subplot_titles=("Anulaciones/Cancelaciones","Cortesías/Descuentos"))
    fig_ops.add_trace(go.Bar(x=df["month_dt"], y=df["anulaciones_en_platillos"], name="Anulaciones"), row=1, col=1)
    fig_ops.add_trace(go.Bar(x=df["month_dt"], y=df["cancelaciones_en_platillos"], name="Cancelaciones"), row=1, col=1)
    fig_ops.add_trace(go.Bar(x=df["month_dt"], y=df["cortesias_en_platillos"], name="Cortesías"), row=2, col=1)
    fig_ops.add_trace(go.Bar(x=df["month_dt"], y=df["descuentos_en_platillos"], name="Descuentos"), row=2, col=1)
    fig_ops.update_layout(barmode="group", height=800, title="Indicadores operativos (CashClosing)")

    html += f"<div class='slide'><div class='section'>Drivers operativos</div>{fig_ops.to_html(full_html=False, include_plotlyjs=False)}</div>"

    # --- Scatters por MES y por MESERO ---
    slides = build_scatter_slides(df, mesas, meseros)

    html += "<div class='slide'><div class='section'>Scatters 2×2 por MES (cortes por mediana)</div>"
    for i, fig in enumerate(slides["mes"], start=1):
        html += fig.to_html(full_html=False, include_plotlyjs=False)
        if i < len(slides["mes"]):
            html += "<hr>"
    html += "<div class='note'>Color = año. Tamaño = volumen. Cortes = medianas.</div></div>"

    html += f"<div class='slide'><div class='section'>Scatters 2×2 por MESERO (activos desde 2025) — {slides['last_month']}</div>"
    for i, fig in enumerate(slides["mesero"], start=1):
        html += fig.to_html(full_html=False, include_plotlyjs=False)
        if i < len(slides["mesero"]):
            html += "<hr>"
    html += "<div class='note'>Filtro: meseros con ventas > 0 desde 2025. Cortes = medianas.</div></div>"

    # --- Calidad de dato (reconciliación) ---
    fig_quality = px.bar(df, x="month", y=df["delta_ventas_pct"]*100, color="status",
                         title="Calidad de dato: Δ Ventas % (Órdenes vs Cierre)", labels={"y":"Δ Ventas %"})
    fig_quality.update_layout(height=650)
    html += f"<div class='slide'><div class='section'>Calidad de dato (reconciliación)</div>{fig_quality.to_html(full_html=False, include_plotlyjs=False)}</div>"

    # --- Apéndice heatmaps ---
    html += f"""
    <div class='slide'>
      <div class='section'>Apéndice — Heatmaps (PNG)</div>
      <ul>
        <li>Ventas (día semana x hora): <b>output/figures/heatmap_ventas_dow_hour.png</b></li>
        <li>Tickets (día semana x hora): <b>output/figures/heatmap_tickets_dow_hour.png</b></li>
        <li>Personas (día semana x hora): <b>output/figures/heatmap_personas_dow_hour.png</b></li>
      </ul>
      <div class='note'>Los heatmaps se generan con matplotlib/seaborn y quedan listos para pegar en Word/PPT.</div>
    </div>
    """

    return html


def main():
    ensure_dirs()

    kpis, recon_m, ops = load_inputs()
    df = prepare_monthly_frame(kpis, recon_m, ops)
    breakpoints = compute_breakpoints(df)

    orders = load_orders_ops()
    meseros = build_meseros_monthly(orders)
    mesas = build_mesas_monthly(orders)

    # Heatmaps
    save_heatmaps(orders)

    # HTML
    html = build_html(df, breakpoints, meseros, mesas, orders)
    out = "output/presentation/dg_presentation_pro_es.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    print("\n✅ Presentación DG (PRO) generada:")
    print(f"- HTML: {out}")
    print("✅ Heatmaps guardados en output/figures/")


if __name__ == "__main__":
    main()