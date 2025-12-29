import os
import json
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def generate_sql_and_answer(prompt: str, table_name: str, columns: list[str], sample_csv: str) -> dict:
    """
    Returns:
      { "answer": str, "sql": str|None, "chart": dict|None, "error": str|None }
    Never raises -> UI should not crash.
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or not OpenAI:
        return {
            "answer": "AI chat is disabled (missing API key or OpenAI library). You can still use Quick Analysis + SQL.",
            "sql": None,
            "chart": None,
            "error": "ai_disabled",
        }

    client = OpenAI(api_key=api_key)

    system = f"""
You are a data analyst copilot.
You must output STRICT JSON only with keys:
- answer (string)
- sql (string or null)
- chart (object or null). Example: {{"type":"bar","x":"col1","y":"metric"}}

Rules:
- If you produce SQL: ONLY SELECT/WITH. No write operations.
- SQL must query the table: {table_name}
- Use only these columns: {columns}
- Prefer aggregations; avoid returning huge raw rows.
"""

    user = f"""
User question:
{prompt}

Table: {table_name}
Columns: {columns}

Sample CSV (first rows):
{sample_csv}
"""

    try:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        text = resp.output_text
        data = json.loads(text)

        return {
            "answer": data.get("answer", ""),
            "sql": data.get("sql"),
            "chart": data.get("chart"),
            "error": None,
        }

    except Exception as e:
        return {
            "answer": "AI chat failed (key/quota/network). Use Quick Analysis or run SQL manually.",
            "sql": None,
            "chart": None,
            "error": str(e),
        }
