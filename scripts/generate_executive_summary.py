import pandas as pd
import os


def main():
    print("\n🔹 EXECUTIVE SUMMARY GENERATION")

    # ------------------------
    # Load datasets
    # ------------------------
    kpis = pd.read_csv("output/datasets/kpis_monthly.csv")
    recon = pd.read_csv("output/datasets/reconciliation_monthly.csv")
    ops = pd.read_csv("output/datasets/kpis_operational.csv")

    print(f"KPIs: {len(kpis)} rows")
    print(f"Reconciliation: {len(recon)} rows")
    print(f"Operational KPIs: {len(ops)} rows")

    # ------------------------
    # Merge core data
    # ------------------------
    df = kpis.merge(
        recon[["month", "status", "source_flag", "delta_ventas_pct"]],
        on="month",
        how="left"
    )

    df["delta_ventas_pct"] = pd.to_numeric(df["delta_ventas_pct"], errors="coerce")

    df = df.merge(ops, on="month", how="left")

    # ------------------------
    # Core KPIs
    # ------------------------
    df["COGS_%"] = df["CostoTotal"] / df["Ventas"]
    df["Margen"] = df["Ventas"] - df["CostoTotal"]
    df["Margen_%"] = df["Margen"] / df["Ventas"]

    # ------------------------
    # Calidad de datos
    # ------------------------
    df["is_real_issue"] = (df["status"] == "REVIEW") & (df["source_flag"] == "OK")
    df["health_score"] = 100 - (df["delta_ventas_pct"].abs() * 100)
    df["severity"] = "LOW"
    df.loc[df["delta_ventas_pct"].abs() > 0.02, "severity"] = "MEDIUM"
    df.loc[df["delta_ventas_pct"].abs() > 0.05, "severity"] = "HIGH"

    # ------------------------
    # Insights
    # ------------------------
    df["insight"] = ""

    df.loc[df["anulaciones_en_platillos"] > 5000, "insight"] = "High cancellations affecting sales"
    df.loc[df["cancelaciones_en_platillos"] > 1000, "insight"] = "Operational cancellation spike"

    # ------------------------
    # Summary stats
    # ------------------------
    total_months = len(df)
    review_months = df[df["status"] == "REVIEW"]
    real_issues = df[df["is_real_issue"]]

    print("\n📊 SUMMARY")
    print(f"Total months: {total_months}")
    print(f"Months with REVIEW: {len(review_months)}")
    print(f"Real issues (excluding migrations): {len(real_issues)}")

    # ------------------------
    # Top anomalies
    # ------------------------
    anomalies = df[
        (df["status"] == "REVIEW") &
        (df["source_flag"] == "OK")
    ].copy()

    if "delta_ventas_pct" not in df.columns:
        print("⚠️ delta_ventas_pct not found — skipping anomalies")
        anomalies = pd.DataFrame()
    else:
        anomalies = df[
            (df["status"] == "REVIEW") &
            (df["source_flag"] == "OK")
        ].copy()

    anomalies["abs_delta"] = anomalies["delta_ventas_pct"].abs()
    anomalies = anomalies.sort_values("abs_delta", ascending=False)

    print("\n⚠️ TOP ANOMALIES")
    print(anomalies[["month", "delta_ventas_pct"]].head(5))

    # ------------------------
    # Operational drivers
    # ------------------------
    if not anomalies.empty:
        print("\n🔎 POTENTIAL DRIVERS (Top month)")
        top_month = anomalies.iloc[0]["month"]

        drivers = df[df["month"] == top_month][[
            "cortesias_en_platillos",
            "cancelaciones_en_platillos",
            "anulaciones_en_platillos",
            "descuentos_en_platillos"
        ]]

        print(f"Month: {top_month}")
        print(drivers)

    # ------------------------
    # Save executive dataset
    # ------------------------
    os.makedirs("output/summary", exist_ok=True)

    df.to_csv("output/summary/executive_monthly_summary.csv", index=False)
    anomalies.to_csv("output/summary/anomalies.csv", index=False)

    print("\n✅ Files saved in output/summary")

    # ------------------------
    # Executive Text Summary
    # ------------------------
    print("\n📄 EXECUTIVE SUMMARY\n")

    print(f"✔ Months analyzed: {total_months}")
    print(f"✔ % clean months: {(1 - len(review_months)/total_months):.2%}")
    print(f"⚠ % months with issues: {(len(real_issues)/total_months):.2%}")

    if not anomalies.empty:
        worst = anomalies.iloc[0]
        print("\n🚨 Biggest deviation:")
        print(f"- Month: {worst['month']}")
        print(f"- Δ ventas: {worst['delta_ventas_pct']:.2%}")

    print("\n✅ GENERATION COMPLETE")


if __name__ == "__main__":
    main()