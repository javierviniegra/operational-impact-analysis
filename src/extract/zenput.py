from pathlib import Path
import pandas as pd
from config.analysis import get_scope
from db.mysql_connection import get_zenput_connection


def _read_sql(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _query_df(sql_path: str, params: dict) -> pd.DataFrame:
    conn = get_zenput_connection()
    try:
        sql = _read_sql(sql_path)
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


def resolve_zenput_account_name() -> str:
    """
    Resolves the Zenput account_name used for tasks.
    Priority:
    1) ANALYSIS_ZENPUT_ACCOUNT_NAME (explicit)
    2) Keyword lookup on zenput_tasks.account_name (ANALYSIS_ZENPUT_ACCOUNT_KEYWORD)
    """
    s = get_scope()

    if s.zenput_account_name:
        return s.zenput_account_name

    if not s.zenput_account_keyword:
        raise ValueError("Missing ANALYSIS_ZENPUT_ACCOUNT_NAME and ANALYSIS_ZENPUT_ACCOUNT_KEYWORD")

    conn = get_zenput_connection()
    try:
        sql = """
        SELECT DISTINCT account_name
        FROM zenput_tasks
        WHERE account_name LIKE %(kw)s
        ORDER BY account_name
        LIMIT 50;
        """
        df = pd.read_sql(sql, conn, params={"kw": f"%{s.zenput_account_keyword}%"})
        if df.empty:
            raise ValueError(f"No Zenput account_name matches for keyword: {s.zenput_account_keyword}")
        return str(df.iloc[0]["account_name"])
    finally:
        conn.close()


def load_submissions():
    """
    Submissions are still filtered by location_name (your current design).
    """
    s = get_scope()
    return _query_df(
        "db/queries/zenput/submissions.sql",
        {"location_name": s.zenput_location_name, "start_date": s.start_date, "end_date": s.end_date},
    )


def load_tasks():
    """
    Tasks are filtered by account_name (resolved).
    """
    s = get_scope()
    account_name = resolve_zenput_account_name()
    return _query_df(
        "db/queries/zenput/tasks.sql",
        {"account_name": account_name, "start_date": s.start_date, "end_date": s.end_date},
    )
