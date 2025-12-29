import os
import json
import duckdb
import pandas as pd
from datetime import datetime

DB_PATH = os.path.join("data", "workspace.duckdb")


def _conn():
    os.makedirs("data", exist_ok=True)
    return duckdb.connect(DB_PATH)


def init_db():
    con = _conn()

    # Datasets + versions
    con.execute("""
    CREATE TABLE IF NOT EXISTS datasets (
        dataset_id BIGINT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TIMESTAMP
    );
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS dataset_versions (
        version_id BIGINT PRIMARY KEY,
        dataset_id BIGINT NOT NULL,
        table_name TEXT NOT NULL,
        source_filename TEXT,
        recipe_json TEXT,
        created_at TIMESTAMP,
        FOREIGN KEY(dataset_id) REFERENCES datasets(dataset_id)
    );
    """)

    # Projects (objective/workspace)
    con.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        project_id BIGINT PRIMARY KEY,
        name TEXT NOT NULL,
        objective TEXT,
        dataset_id BIGINT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    );
    """)

    # Saved insights (notes + optionally SQL used)
    con.execute("""
    CREATE TABLE IF NOT EXISTS insights (
        insight_id BIGINT PRIMARY KEY,
        project_id BIGINT NOT NULL,
        title TEXT NOT NULL,
        note TEXT,
        sql_text TEXT,
        chart_json TEXT,
        created_at TIMESTAMP,
        FOREIGN KEY(project_id) REFERENCES projects(project_id)
    );
    """)

    # Reports (simple markdown export)
    con.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        report_id BIGINT PRIMARY KEY,
        project_id BIGINT NOT NULL,
        title TEXT NOT NULL,
        markdown TEXT NOT NULL,
        created_at TIMESTAMP,
        FOREIGN KEY(project_id) REFERENCES projects(project_id)
    );
    """)

    con.close()


def _new_id(con, table: str, col: str) -> int:
    row = con.execute(f"SELECT COALESCE(MAX({col}), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


def register_new_dataset(name: str) -> int:
    con = _conn()
    dataset_id = _new_id(con, "datasets", "dataset_id")
    con.execute(
        "INSERT INTO datasets VALUES (?, ?, ?)",
        [dataset_id, name, datetime.utcnow()],
    )
    con.close()
    return dataset_id


def list_datasets() -> pd.DataFrame:
    con = _conn()
    df = con.execute("SELECT * FROM datasets ORDER BY created_at DESC").df()
    con.close()
    return df


def create_version_from_df(dataset_id: int, df: pd.DataFrame, source_filename: str, recipe_json: str) -> int:
    con = _conn()
    version_id = _new_id(con, "dataset_versions", "version_id")

    # table name unique per version
    safe_id = str(dataset_id).replace("-", "_")
    table_name = f"ds_{safe_id}_v_{version_id}"

    con.register("tmp_df", df)
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM tmp_df")

    con.execute(
        "INSERT INTO dataset_versions VALUES (?, ?, ?, ?, ?, ?)",
        [version_id, dataset_id, table_name, source_filename, recipe_json, datetime.utcnow()],
    )
    con.close()
    return version_id


def get_active_table(dataset_id: int) -> str:
    con = _conn()
    row = con.execute(
        """
        SELECT table_name
        FROM dataset_versions
        WHERE dataset_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        [dataset_id],
    ).fetchone()
    con.close()
    return row[0] if row else None


def list_versions(dataset_id: int) -> pd.DataFrame:
    con = _conn()
    df = con.execute(
        """
        SELECT version_id, table_name, source_filename, recipe_json, created_at
        FROM dataset_versions
        WHERE dataset_id = ?
        ORDER BY created_at DESC
        """,
        [dataset_id],
    ).df()
    con.close()
    return df


def set_active_version(dataset_id: int, version_id: int) -> str:
    """
    We keep "active" as "latest created".
    For beginner simplicity: when user chooses a version,
    we just return its table (UI will use it).
    """
    con = _conn()
    row = con.execute(
        "SELECT table_name FROM dataset_versions WHERE dataset_id=? AND version_id=?",
        [dataset_id, version_id],
    ).fetchone()
    con.close()
    return row[0] if row else None


def sql(query: str, params=None) -> pd.DataFrame:
    con = _conn()
    if params is None:
        df = con.execute(query).df()
    else:
        df = con.execute(query, params).df()
    con.close()
    return df


def sql_scalar(query: str, params=None):
    con = _conn()
    if params is None:
        val = con.execute(query).fetchone()
    else:
        val = con.execute(query, params).fetchone()
    con.close()
    return val[0] if val else None
