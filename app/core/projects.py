from datetime import datetime
import pandas as pd
from app.core.warehouse import _conn


def create_project(name: str, objective: str, dataset_id: int | None) -> int:
    con = _conn()
    project_id = int(con.execute("SELECT COALESCE(MAX(project_id),0)+1 FROM projects").fetchone()[0])
    con.execute(
        "INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?)",
        [project_id, name, objective, dataset_id, datetime.utcnow(), datetime.utcnow()],
    )
    con.close()
    return project_id


def list_projects() -> pd.DataFrame:
    con = _conn()
    df = con.execute(
        "SELECT project_id, name, objective, dataset_id, created_at, updated_at FROM projects ORDER BY updated_at DESC"
    ).df()
    con.close()
    return df


def update_project(project_id: int, name: str, objective: str, dataset_id: int | None):
    con = _conn()
    con.execute(
        "UPDATE projects SET name=?, objective=?, dataset_id=?, updated_at=? WHERE project_id=?",
        [name, objective, dataset_id, datetime.utcnow(), project_id],
    )
    con.close()
