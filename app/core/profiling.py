import pandas as pd

def basic_profile(df: pd.DataFrame) -> dict:
    n_rows, n_cols = df.shape
    missing_pct = (df.isna().mean() * 100).round(2)
    dtypes = df.dtypes.astype(str)

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    stats = df[numeric_cols].describe().T if numeric_cols else pd.DataFrame()

    top_values = {}
    for c in df.columns[:50]:
        try:
            vc = df[c].astype(str).value_counts(dropna=False).head(5)
            top_values[c] = vc.to_dict()
        except Exception:
            top_values[c] = {}

    return {
        "rows": int(n_rows),
        "cols": int(n_cols),
        "dtypes": dtypes.to_dict(),
        "missing_pct": missing_pct.to_dict(),
        "numeric_stats": stats.reset_index().rename(columns={"index": "column"}).to_dict(orient="records"),
        "top_values": top_values,
    }
