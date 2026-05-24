from __future__ import annotations

from pathlib import Path
from typing import Iterable

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import settings


def get_engine() -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


def execute_sql_file(engine: Engine, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def execute_many(engine: Engine, statements: Iterable[str]) -> None:
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def fetch_scalar(engine: Engine, sql: str):
    with engine.connect() as conn:
        return conn.execute(text(sql)).scalar()
