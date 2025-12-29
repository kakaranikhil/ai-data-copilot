from datetime import datetime
import pandas as pd
from app.core.warehouse import _conn


def save_report(project_id: int, title: str, markdown: str) -> int:
    con = _conn()
    report_id = int(con.execute("SELECT COALESCE(MAX(report_id),0)+1 FROM reports").fetchone()[0])
    con.execute(
        "INSERT INTO reports VALUES (?, ?, ?, ?, ?)",
        [report_id, project_id, title, markdown, datetime.utcnow()],
    )
    con.close()
    return report_id


def list_reports(project_id: int) -> pd.DataFrame:
    con = _conn()
    df = con.execute(
        "SELECT report_id, title, created_at FROM reports WHERE project_id=? ORDER BY created_at DESC",
        [project_id],
    ).df()
    con.close()
    return df


def get_report(report_id: int) -> dict | None:
    con = _conn()
    row = con.execute(
        "SELECT report_id, project_id, title, markdown, created_at FROM reports WHERE report_id=?",
        [report_id],
    ).fetchone()
    con.close()
    if not row:
        return None
    return {
        "report_id": row[0],
        "project_id": row[1],
        "title": row[2],
        "markdown": row[3],
        "created_at": row[4],
    }
