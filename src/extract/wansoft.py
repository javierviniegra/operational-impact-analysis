from pathlib import Path
import pandas as pd
from config.analysis import get_scope
from db.mysql_connection import get_wansoft_connection


def _read_sql(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _query_df(sql_path: str, params: dict) -> pd.DataFrame:
    conn = get_wansoft_connection()
    try:
        sql = _read_sql(sql_path)
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()

def resolve_branch_name_for_text_tables() -> str:
    """
    Resolves the branch name used in text-based tables (Sucursal column),
    using ANALYSIS_WANSOFT_BRANCH_NAME first, and falling back to a keyword search.
    """
    s = get_scope()
    if s.wansoft_branch_name:
        return s.wansoft_branch_name

    if not s.branch_keyword:
        raise ValueError("Missing ANALYSIS_WANSOFT_BRANCH_NAME and ANALYSIS_BRANCH_KEYWORD")

    conn = get_wansoft_connection()
    try:
        # Prefer payments table because it often includes the operational naming used for delivery/platform logic
        sql = """
        SELECT DISTINCT Sucursal
        FROM getallordenesbyday_new_pago
        WHERE Sucursal LIKE %(kw)s
        LIMIT 50;
        """
        df = pd.read_sql(sql, conn, params={"kw": f"%{s.branch_keyword}%"})
        if df.empty:
            raise ValueError(f"No branch matches for keyword: {s.branch_keyword}")
        # Choose the first match deterministically
        return str(df.iloc[0]["Sucursal"])
    finally:
        conn.close()


def load_cashclosing():
    s = get_scope()
    return _query_df(
        "db/queries/wansoft/sales_cashclosing.sql",
        {"subsidiary_id": s.wansoft_subsidiary_id, "start_date": s.start_date, "end_date": s.end_date},
    )


def load_orders():
    s = get_scope()
    branch_name = resolve_branch_name_for_text_tables()
    return _query_df(
        "db/queries/wansoft/sales_orders.sql",
        {"branch_name": branch_name, "start_date": s.start_date, "end_date": s.end_date},
    )

def load_sales_detail():
    s = get_scope()
    branch_name = resolve_branch_name_for_text_tables()
    return _query_df(
        "db/queries/wansoft/sales_detail.sql",
        {"branch_name": branch_name, "start_date": s.start_date, "end_date": s.end_date},
    )

def load_payments():
    s = get_scope()
    branch_name = resolve_branch_name_for_text_tables()
    return _query_df(
        "db/queries/wansoft/payments.sql",
        {"branch_name": branch_name, "start_date": s.start_date, "end_date": s.end_date},
    )


def load_purchases_invoices():
    s = get_scope()
    return _query_df(
        "db/queries/wansoft/purchases_invoices.sql",
        {
            "subsidiary_id": s.wansoft_subsidiary_id,
            "start_date": s.start_date,
            "end_date": s.end_date,
        },
    )


def load_tablajeria():
    s = get_scope()
    return _query_df(
        "db/queries/wansoft/tablajeria.sql",
        {"subsidiary_id": s.wansoft_subsidiary_id, "start_date": s.start_date, "end_date": s.end_date},
    )


def load_cost_monthly():
    s = get_scope()
    start_month = s.start_date[:7]  # YYYY-MM
    end_month = s.end_date[:7]      # YYYY-MM
    return _query_df(
        "db/queries/wansoft/cost_monthly.sql",
        {"subsidiary_id": s.wansoft_subsidiary_id, "start_month": start_month, "end_month": end_month},
    )