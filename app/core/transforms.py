import json
import pandas as pd


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def trim_strings(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in df.select_dtypes(include=["object"]).columns:
        df[c] = df[c].astype(str).str.strip()
    return df


def drop_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates().copy()


def parse_dates_best_effort(df: pd.DataFrame, sample_n: int = 200) -> pd.DataFrame:
    """
    Parse columns that look like date/time. Uses a small sample to avoid
    converting every column and slowing down big data.
    """
    df = df.copy()
    for c in df.columns:
        name = str(c).lower()
        if ("date" in name) or ("time" in name):
            try:
                sample = df[c].head(sample_n)
                parsed = pd.to_datetime(sample, errors="coerce")
                # only convert if at least 50% sample parses
                if parsed.notna().mean() >= 0.5:
                    df[c] = pd.to_datetime(df[c], errors="coerce")
            except Exception:
                pass
    return df


def add_missing_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates boolean flags for columns with missing values.
    """
    df = df.copy()
    for c in df.columns:
        if df[c].isna().any():
            df[f"{c}__is_missing"] = df[c].isna()
    return df


def add_simple_numeric_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds log1p for positive numeric columns + z-score versions (safe).
    """
    df = df.copy()
    num_cols = df.select_dtypes(include="number").columns.tolist()
    for c in num_cols:
        s = df[c]
        if (s.dropna() > 0).all():
            df[f"{c}__log1p"] = (s).apply(lambda x: None if pd.isna(x) else pd.np.log1p(x))  # simple + safe
        # z-score (avoid division by zero)
        mean = s.mean()
        std = s.std()
        if std and std > 0:
            df[f"{c}__z"] = (s - mean) / std
    return df


DEFAULT_RECIPE = [
    {"op": "normalize_columns"},
    {"op": "trim_strings"},
    {"op": "drop_duplicate_rows"},
    {"op": "parse_dates_best_effort"},
]

FEATURE_RECIPE = [
    {"op": "normalize_columns"},
    {"op": "trim_strings"},
    {"op": "parse_dates_best_effort"},
    {"op": "add_missing_flags"},
    {"op": "add_simple_numeric_features"},
]

OPS = {
    "normalize_columns": normalize_columns,
    "trim_strings": trim_strings,
    "drop_duplicate_rows": drop_duplicate_rows,
    "parse_dates_best_effort": parse_dates_best_effort,
    "add_missing_flags": add_missing_flags,
    "add_simple_numeric_features": add_simple_numeric_features,
}


def apply_recipe(df: pd.DataFrame, recipe: list) -> pd.DataFrame:
    out = df.copy()
    for step in recipe:
        op = step["op"]
        out = OPS[op](out)
    return out


def recipe_to_json(recipe: list) -> str:
    return json.dumps(recipe)
