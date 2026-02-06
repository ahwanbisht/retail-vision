from __future__ import annotations

import pathlib

from sqlalchemy import create_engine

from app.config import settings


def split_sql_statements(sql_text: str) -> list[str]:
    chunks = []
    current = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            chunks.append("\n".join(current).strip())
            current = []
    if current:
        chunks.append("\n".join(current).strip())
    return chunks


def main() -> None:
    schema_path = pathlib.Path("app/db/schema.sql")
    sql_text = schema_path.read_text(encoding="utf-8")
    statements = split_sql_statements(sql_text)

    engine = create_engine(settings.postgres_url, future=True)
    with engine.begin() as conn:
        for stmt in statements:
            conn.exec_driver_sql(stmt)

    print(f"Applied {len(statements)} SQL statements to {settings.postgres_url}")


if __name__ == "__main__":
    main()
