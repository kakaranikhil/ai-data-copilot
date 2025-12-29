import json
import re
import numpy as np
import pandas as pd

# =========================================================
# BASIC CLEANING OPS (EXISTING + SAFE)
# =========================================================

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df

def trim_strings(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in df.select_dtypes(include=["object"]).columns:
        df[c] = df[c].astype(str).str.strip()
    return df

def drop_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates().copy()

def parse_dates_best_effort(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in df.columns:
        name = c.lower()
        if "date" in name or "time" in name:
            try:
                df[c] = pd.to_datetime(df[c], errors="coerce", infer_datetime_format=True)
            except Exception:
                pass
    return df


# =========================================================
# OPTION C — FEATURE ENGINEERING OPS (UNIVERSAL)
# =========================================================

def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    new_cols = []
    for c in df.columns:
        c2 = str(c).strip().lower()
        c2 = re.sub(r"\s+", "_", c2)
        c2 = re.sub(r"[^a-z0-9_]", "", c2)
        if c2 == "":
            c2 = "col"
        new_cols.append(c2)
    df.columns = new_cols
    return df

def parse_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse date-like object columns and add *_year, *_month, *_day, *_dow features
    """
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == "object":
            sample = df[col].dropna().astype(str).head(30)
            if sample.empty:
                continue

            looks_like_date = sample.str.contains(r"[-/]").mean() > 0.4
            if not looks_like_date:
                continue

            parsed = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True)
            good_ratio = parsed.notna().mean()

            if good_ratio >= 0.6:
                df[col] = parsed
                df[f"{col}_year"] = parsed.dt.year
                df[f"{col}_month"] = parsed.dt.month
                df[f"{col}_day"] = parsed.dt.day
                df[f"{col}_dow"] = parsed.dt.dayofweek
    return df

def add_missing_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        df[f"{col}_is_missing"] = df[col].isna().astype(int)
    return df

def add_text_length_features(df: pd.DataFrame, max_unique: int = 200) -> pd.DataFrame:
    """
    Add *_len features for low-cardinality text columns
    """
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == "object":
            nunique = df[col].nunique(dropna=True)
            if 0 < nunique <= max_unique:
                df[f"{col}_len"] = df[col].astype(str).str.len()
    return df

def clip_outliers_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clip numeric outliers using 1st / 99th percentile
    """
    df = df.copy()
    for col in df.select_dtypes(include="number").columns:
        s = df[col].dropna()
        if s.empty:
            continue
        lo = s.quantile(0.01)
        hi = s.quantile(0.99)
        df[col] = df[col].clip(lo, hi)
    return df


# =========================================================
# RECIPES
# =========================================================

DEFAULT_RECIPE = [
    {"op": "normalize_columns"},
    {"op": "trim_strings"},
    {"op": "drop_duplicate_rows"},
    {"op": "parse_dates_best_effort"},
]

FEATURE_RECIPE = [
    {"op": "normalize_column_names"},
    {"op": "parse_date_columns"},
    {"op": "add_missing_flags"},
    {"op": "add_text_length_features"},
    {"op": "clip_outliers_numeric"},
]


# =========================================================
# OP REGISTRY
# =========================================================

OPS = {
    # cleaning
    "normalize_columns": normalize_columns,
    "trim_strings": trim_strings,
    "drop_duplicate_rows": drop_duplicate_rows,
    "parse_dates_best_effort": parse_dates_best_effort,

    # feature engineering
    "normalize_column_names": normalize_column_names,
    "parse_date_columns": parse_date_columns,
    "add_missing_flags": add_missing_flags,
    "add_text_length_features": add_text_length_features,
    "clip_outliers_numeric": clip_outliers_numeric,
}


# =========================================================
# EXECUTION HELPERS
# =========================================================

def apply_recipe(df: pd.DataFrame, recipe: list) -> pd.DataFrame:
    out = df.copy()
    for step in recipe:
        op = step["op"]
        if op not in OPS:
            raise ValueError(f"Unknown op: {op}")
        out = OPS[op](out)
    return out

def recipe_to_json(recipe: list) -> str:
    return json.dumps(recipe)
