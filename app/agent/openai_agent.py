import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _safe_select_only(sql_text: str) -> bool:
    """Allow only simple SELECT queries for safety."""
    if not sql_text:
        return False
    s = sql_text.strip().lower()
    if not s.startswith("select"):
        return False
    banned = ["insert", "update", "delete", "drop", "alter", "create", "attach", "copy", "pragma"]
    return not any(b in s for b in banned)

def generate_sql_and_answer(prompt: str, table_name: str, columns: list[str], sample_csv: str) -> dict:
    """
    Returns dict with:
    - answer (str)
    - sql (str or "")
    - chart (dict or null)  e.g. {"type":"bar","x":"col","y":"col"} optional
    """
    schema = ", ".join(columns)

    instruction = f"""
You are a data analyst. You have a DuckDB table named: {table_name}
Columns: {schema}

User question: {prompt}

You MUST respond as STRICT JSON with keys:
- "answer": string (plain English)
- "sql": string (a single SELECT query) OR "" if not needed
- "chart": either null OR an object with:
    - "type": one of ["bar","line"]
    - "x": column name
    - "y": column name

Rules:
- SQL must be SELECT only.
- Prefer LIMIT 200 for large outputs.
- If the user asks for "top" or "most common", use GROUP BY + COUNT.
- If you produce sql, make it run directly in DuckDB.
- If chart is provided, it must match the SQL output columns.

Here are sample rows (CSV):
{sample_csv}
"""

    resp = client.responses.create(
        model="gpt-5.2",
        input=instruction,
    )

    text = resp.output_text.strip()

    # Try strict JSON parse; fallback to safe default
    try:
        data = json.loads(text)
    except Exception:
        data = {"answer": text, "sql": "", "chart": None}

    # Normalize keys
    data.setdefault("answer", "")
    data.setdefault("sql", "")
    data.setdefault("chart", None)

    # Safety gate SQL
    if data["sql"] and not _safe_select_only(data["sql"]):
        data["answer"] += "\n\n(Refused unsafe SQL. Only SELECT is allowed.)"
        data["sql"] = ""
        data["chart"] = None

    return data
