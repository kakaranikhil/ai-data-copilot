import re

FORBIDDEN = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bATTACH\b",
    r"\bDETACH\b",
]


def is_sql_safe(sql_text: str) -> (bool, str):
    if not sql_text or not isinstance(sql_text, str):
        return False, "Empty SQL."

    s = sql_text.strip().rstrip(";")
    upper = s.upper()

    for pat in FORBIDDEN:
        if re.search(pat, upper):
            return False, f"Forbidden SQL detected: {pat}"

    if not upper.startswith("SELECT") and not upper.startswith("WITH"):
        return False, "Only SELECT/WITH queries are allowed."

    return True, "OK"


def enforce_limit(sql_text: str, limit: int = 5000) -> str:
    """
    If no LIMIT exists, append LIMIT.
    Simple heuristic; good enough for V1.
    """
    s = sql_text.strip().rstrip(";")
    upper = s.upper()
    if " LIMIT " in upper:
        return s
    return f"{s} LIMIT {int(limit)}"
