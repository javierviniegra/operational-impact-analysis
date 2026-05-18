import pandas as pd

def build_order_level(df_orders_with_payments: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures one row per order (Movimento) and builds canonical channel fields.
    Assumes payments are already left-joined and there is no multi-payment per order.
    """

    df = df_orders_with_payments.copy()

    # Ensure key type
    df["Movimento"] = df["Movimento"].astype(str)

    # 1) One row per order:
    # If duplicates exist, keep the first occurrence deterministically.
    df = df.sort_values(["Movimento"]).drop_duplicates(subset=["Movimento"], keep="first")

    return df


def infer_channel_from_tipoorden(tipoorden: str):
    """
    Fallback channel inference when MetodoDePago is missing.
    This is intentionally conservative and can be refined later.
    """
    if tipoorden is None:
        return "Unknown", "Unknown"

    t = str(tipoorden).strip().lower()

    # Common Wansoft patterns (examples seen in other exports)
    if "uber" in t or "rappi" in t or "didi" in t or "delivery" in t or "ecommerce" in t:
        return "Delivery", "Unknown"
    if "llevar" in t or "take" in t or "para llevar" in t or "pickup" in t:
        return "Llevar", "Unknown"
    if "restaurant" in t or "salon" in t or "dine" in t:
        return "Salon", "Unknown"

    return "Unknown", "Unknown"


def apply_channel_fallback(df: pd.DataFrame) -> pd.DataFrame:
    """
    If MetodoDePago is NaN -> canal/subcanal become Unknown.
    We replace Unknown using TipoOrden inference.
    """
    df = df.copy()

    missing_payment = df["MetodoDePago"].isna()

    inferred = df.loc[missing_payment, "TipoOrden"].map(infer_channel_from_tipoorden)
    df.loc[missing_payment, "canal"] = inferred.map(lambda x: x[0])
    df.loc[missing_payment, "subcanal"] = inferred.map(lambda x: x[1])

    return df
