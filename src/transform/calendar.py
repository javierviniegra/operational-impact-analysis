import pandas as pd

def create_calendar(start_date: str, end_date: str) -> pd.DataFrame:
    df = pd.DataFrame({
        "date": pd.date_range(start=start_date, end=end_date)
    })

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%B")
    df["week"] = df["date"].dt.isocalendar().week
    df["day"] = df["date"].dt.day
    df["day_of_week"] = df["date"].dt.day_name()
    df["is_weekend"] = df["day_of_week"].isin(["Saturday", "Sunday"])

    return df