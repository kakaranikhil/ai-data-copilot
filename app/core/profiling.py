import pandas as pd


def basic_profile(df: pd.DataFrame) -> dict:
    """
    Fast, lightweight profiling. Works on a sample df.
    """
    out = {}
    out["rows"] = int(df.shape[0])
    out["cols"] = int(df.shape[1])

    missing_pct = {}
    dtypes = {}
    nunique = {}

    for c in df.columns:
        dtypes[c] = str(df[c].dtype)
        missing_pct[c] = float(df[c].isna().mean() * 100.0)
        try:
            nunique[c] = int(df[c].nunique(dropna=True))
        except Exception:
            nunique[c] = None

    out["missing_pct"] = missing_pct
    out["dtypes"] = dtypes
    out["nunique"] = nunique
    return out
