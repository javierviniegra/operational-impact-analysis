import numpy as np
import pandas as pd
import plotly.graph_objects as go

def _to_num(s):
    return pd.to_numeric(s, errors="coerce")

def quadrant_lines(fig, x_med, y_med, row=None, col=None):
    # Líneas de mediana
    fig.add_vline(x=x_med, line_width=2, line_dash="dash", line_color="white", row=row, col=col)
    fig.add_hline(y=y_med, line_width=2, line_dash="dash", line_color="white", row=row, col=col)

def quadrant_scatter_plotly(
    df: pd.DataFrame,
    x: str,
    y: str,
    label: str,
    title: str,
    color: str | None = None,
    size: str | None = None,
    hover: list[str] | None = None,
    median_scope_df: pd.DataFrame | None = None,
    show_colorbar: bool = False
) -> tuple[go.Figure, float, float]:
    """
    Scatter 2x2 usando MEDIANA (robusto a outliers).
    Devuelve (fig, x_median, y_median)
    """
    d = df.copy()

    d[x] = _to_num(d[x])
    d[y] = _to_num(d[y])

    base = median_scope_df if median_scope_df is not None else d
    x_med = _to_num(base[x]).median()
    y_med = _to_num(base[y]).median()

    marker = dict(size=10, opacity=0.85, color="deepskyblue")

    if size and size in d.columns:
        marker["size"] = _to_num(d[size]).fillna(10)
        marker["sizemode"] = "area"
        mx = marker["size"].max()
        marker["sizeref"] = 2.0 * mx / (40.0**2) if mx and mx > 0 else 1

    if color and color in d.columns:
        # Color continuo (por ejemplo año como número)
        marker["color"] = _to_num(d[color])
        marker["colorscale"] = "Viridis"
        marker["showscale"] = bool(show_colorbar)
        if show_colorbar:
            marker["colorbar"] = dict(title=color)

    # Hover
    hover_text = None
    if hover:
        cols = [c for c in hover if c in d.columns]
        if cols:
            hover_text = d[cols].astype(str).agg("<br>".join, axis=1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d[x],
        y=d[y],
        mode="markers+text",
        text=d[label].astype(str),
        textposition="top center",
        marker=marker,
        hovertext=hover_text,
        hoverinfo="text" if hover_text is not None else "x+y+text",
        name="Puntos"
    ))

    # Línea de trayectoria (para ver movimiento temporal si label es mes y df está ordenado)
    if label in d.columns and d[label].nunique() == len(d):
        fig.add_trace(go.Scatter(
            x=d[x],
            y=d[y],
            mode="lines",
            line=dict(color="rgba(200,200,200,0.35)", width=2),
            name="Trayectoria"
        ))

    quadrant_lines(fig, x_med, y_med)

    fig.update_layout(
        title=f"{title}<br><span style='font-size:12px;color:gray'>Cortes por mediana: X={x_med:,.2f}, Y={y_med:,.2f}</span>",
        xaxis_title=x,
        yaxis_title=y,
        height=620,
        margin=dict(l=40, r=20, t=80, b=40),
        legend=dict(orientation="h")
    )
    return fig, x_med, y_med


def quadrant_scatter_matplotlib(
    df: pd.DataFrame,
    x: str,
    y: str,
    label: str,
    title: str,
    color: str | None = None,
    median_scope_df: pd.DataFrame | None = None,
    ax=None
):
    """
    Versión matplotlib para exportar a PNG (Word).
    Corta por mediana de X e Y.
    """
    d = df.copy()
    d[x] = _to_num(d[x])
    d[y] = _to_num(d[y])

    base = median_scope_df if median_scope_df is not None else d
    x_med = _to_num(base[x]).median()
    y_med = _to_num(base[y]).median()

    if ax is None:
        import matplotlib.pyplot as plt
        ax = plt.gca()

    if color and color in d.columns:
        cvals = _to_num(d[color])
        sc = ax.scatter(d[x], d[y], c=cvals, cmap="viridis", alpha=0.85)
    else:
        ax.scatter(d[x], d[y], alpha=0.85)

    # Etiquetas pequeñas (mes o mesero)
    for _, r in d.iterrows():
        ax.text(r[x], r[y], str(r[label]), fontsize=7, alpha=0.85)

    ax.axvline(x_med, linestyle="--", linewidth=1.5)
    ax.axhline(y_med, linestyle="--", linewidth=1.5)

    ax.set_title(title, fontsize=10)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.grid(alpha=0.2)

    return x_med, y_med