import os
import duckdb
import pandas as pd
from datetime import datetime

DB_PATH = os.path.join("data", "workspace.duckdb")

def conn():
    return duckdb.connect(DB_PATH)

def init_db():
    with conn() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS dataset_registry (
            dataset_id VARCHAR PRIMARY KEY,
            name VARCHAR,
            created_at TIMESTAMP,
            active_version_id VARCHAR
        );
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS dataset_versions (
            version_id VARCHAR PRIMARY KEY,
            dataset_id VARCHAR,
            created_at TIMESTAMP,
            source_filename VARCHAR,
            table_name VARCHAR,
            row_count BIGINT,
            col_count BIGINT,
            transform_recipe_json VARCHAR
        );
        """)

def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def register_new_dataset(name: str) -> str:
    dataset_id = f"ds_{int(datetime.utcnow().timestamp()*1000)}"
    with conn() as con:
        con.execute(
            "INSERT INTO dataset_registry VALUES (?, ?, ?, ?)",
            [dataset_id, name, _now(), None]
        )
    return dataset_id

def create_version_from_df(dataset_id: str, df: pd.DataFrame, source_filename: str, recipe_json: str = "[]") -> str:
    version_id = f"v_{int(datetime.utcnow().timestamp()*1000)}"
    table_name = f"{dataset_id}__{version_id}"

    with conn() as con:
        con.register("tmp_df", df)
        con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM tmp_df;")
        row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        col_count = len(df.columns)

        con.execute("""
            INSERT INTO dataset_versions
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [version_id, dataset_id, _now(), source_filename, table_name, row_count, col_count, recipe_json])

        con.execute(
            "UPDATE dataset_registry SET active_version_id=? WHERE dataset_id=?",
            [version_id, dataset_id]
        )

    return version_id

def list_datasets():
    with conn() as con:
        return con.execute("""
            SELECT dataset_id, name, created_at, active_version_id
            FROM dataset_registry
            ORDER BY created_at DESC
        """).df()

def get_active_table(dataset_id: str) -> str:
    with conn() as con:
        row = con.execute("""
            SELECT v.table_name
            FROM dataset_registry r
            JOIN dataset_versions v ON r.active_version_id = v.version_id
            WHERE r.dataset_id=?
        """, [dataset_id]).fetchone()

    if not row:
        raise ValueError("No active version found for dataset.")
    return row[0]

def sql(query: str) -> pd.DataFrame:
    with conn() as con:
        return con.execute(query).df()
