import pandas as pd


def quality_report(df: pd.DataFrame) -> dict:
    """
    Beginner-friendly quality checks.
    Works on full df, but you can pass a sample if needed.
    """
    out = {}
    out["rows"] = int(df.shape[0])
    out["cols"] = int(df.shape[1])
    out["duplicate_rows"] = int(df.duplicated().sum())

    missing = {}
    for c in df.columns:
        missing[c] = {
            "missing_pct": float(df[c].isna().mean() * 100.0),
            "missing_count": int(df[c].isna().sum()),
        }
    out["missing"] = missing

    # simple numeric outlier scan (IQR) for top 10 numeric cols
    outliers = {}
    num_cols = df.select_dtypes(include="number").columns.tolist()[:10]
    for c in num_cols:
        s = df[c].dropna()
        if s.empty:
            continue
        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        low = q1 - 1.5 * iqr
        high = q3 + 1.5 * iqr
        outliers[c] = int(((s < low) | (s > high)).sum())

    out["outliers_iqr_top10_numeric"] = outliers
    return out
