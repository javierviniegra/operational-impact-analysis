from datetime import datetime
import pandas as pd

from config.analysis import get_scope
from src.extract.wansoft import (
    load_cashclosing, load_orders, load_sales_detail, load_payments,
    load_purchases_invoices, load_tablajeria, load_cost_monthly,
    resolve_branch_name_for_text_tables,
)
from src.extract.zenput import load_tasks, resolve_zenput_account_name


def _safe_minmax_date(df: pd.DataFrame, col: str):
    if col not in df.columns or df.empty:
        return None, None
    try:
        series = pd.to_datetime(df[col], errors="coerce")
        return series.min(), series.max()
    except Exception:
        return None, None


def _print_df_info(name: str, df: pd.DataFrame, date_cols: list[str]):
    print(f"\n=== {name} ===")
    print(f"Rows: {len(df):,} | Cols: {len(df.columns)}")
    if len(df.columns) > 0:
        print("Columns:", ", ".join(df.columns[:20]) + (" ..." if len(df.columns) > 20 else ""))
    for c in date_cols:
        mn, mx = _safe_minmax_date(df, c)
        if mn is not None or mx is not None:
            print(f"Date range ({c}): {mn}  ->  {mx}")


def main():
    s = get_scope()
    print("=== Analysis Scope ===")
    print(s)

    # Resolve names used in text-based tables
    w_branch = resolve_branch_name_for_text_tables()
    z_account = resolve_zenput_account_name()
    print("\n=== Resolved Identifiers ===")
    print("Wansoft text-branch name (Sucursal):", w_branch)
    print("Zenput account_name (Tasks):", z_account)

    # Load Wansoft datasets
    df_cash = load_cashclosing()
    df_orders = load_orders()
    df_detail = load_sales_detail()
    df_pay = load_payments()
    df_purch = load_purchases_invoices()
    df_tab = load_tablajeria()
    df_cost = load_cost_monthly()

    # Load Zenput dataset (tasks only for this check)
    df_tasks = load_tasks()

    # Print summaries
    _print_df_info("Wansoft | Cash Closing", df_cash, ["fecha_corte", "created_at"])
    _print_df_info("Wansoft | Orders", df_orders, ["Fecha", "HoraApertura", "HoraCierre"])
    _print_df_info("Wansoft | Sales Detail", df_detail, ["Hora"])
    _print_df_info("Wansoft | Payments", df_pay, ["Fecha"])
    _print_df_info("Wansoft | Purchases (Invoice)", df_purch, ["FechaReal", "Fecha", "created_at"])
    _print_df_info("Wansoft | Tablajeria", df_tab, ["InputDate", "created_at"])
    _print_df_info("Wansoft | Monthly Cost", df_cost, ["mes_ano", "created_at"])
    _print_df_info("Zenput | Tasks", df_tasks, ["date_due", "date_completed", "created_at"])

    # Minimal assertions (fail fast)
    failures = []
    if df_cash.empty: failures.append("Cash Closing is empty")
    if df_orders.empty: failures.append("Orders is empty")
    if df_pay.empty: failures.append("Payments is empty")
    if df_cost.empty: failures.append("Monthly Cost is empty")
    if df_tasks.empty: failures.append("Zenput Tasks is empty")

    print("\n=== Validation Result ===")
    if failures:
        print("FAILED:")
        for f in failures:
            print("-", f)
        raise SystemExit(1)

    print("OK: core datasets loaded successfully.")


if __name__ == "__main__":
    main()