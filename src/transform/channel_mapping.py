import pandas as pd

def classify_channel(metodo_pago):
    # Handle NaN / None / non-string values safely
    if metodo_pago is None or (isinstance(metodo_pago, float) and pd.isna(metodo_pago)):
        return "Unknown", "Unknown"

    # Convert to string safely
    m = str(metodo_pago).strip().lower()

    if m == "" or m == "nan":
        return "Unknown", "Unknown"

    # ✅ DELIVERY
    if "rappi" in m:
        return "Delivery", "Rappi"
    if "uber" in m:
        return "Delivery", "Uber"
    if "didi" in m:
        return "Delivery", "Didi"
    if "totalplay" in m or "total play" in m:
        return "Delivery", "Totalplay"

    # ✅ SALON
    if "tarjeta" in m or "amex" in m:
        return "Salon", "Tarjeta"
    if "clip" in m or "totalpay" in m:
        return "Salon", "TPV"
    if "efectivo" in m:
        return "Salon", "Efectivo"

    # ✅ OTROS
    if "transferencia" in m:
        return "Otros", "Transferencia"
    if "dolar" in m:
        return "Otros", "Dolares"
    if "cheque" in m:
        return "Otros", "Cheque"

    return "Otros", "Otros"