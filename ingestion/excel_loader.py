from pathlib import Path

import pandas as pd


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def load_reviews(path: str | Path) -> list[dict]:
    df = pd.read_excel(path)
    rows: list[dict] = []
    for _, row in df.iterrows():
        rows.append(
            {
                "branch_id": _normalize_text(str(row.get("branch_id", "")).strip()),
                "user_id": _normalize_text(str(row.get("user_id", "")).strip()),
                "comment": _normalize_text(str(row.get("comment", "")).strip()),
            }
        )
    return rows
