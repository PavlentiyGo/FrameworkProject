"""Загрузка именованных SQL-запросов из общего с SQLite CLI файла."""

import re
import sqlite3
from functools import lru_cache
from typing import Any

from db.database import BASE_DIR


@lru_cache(maxsize=1)
def load_queries() -> dict[str, str]:
    source = (BASE_DIR / "sql" / "queries.sql").read_text(encoding="utf-8")
    parts = re.split(r"(?m)^-- name: ([a-z_]+)\s*$", source)
    return {
        parts[index]: parts[index + 1].strip()
        for index in range(1, len(parts), 2)
    }


def fetch_all(
    connection: sqlite3.Connection,
    name: str,
    parameters: tuple[Any, ...] = (),
) -> list[sqlite3.Row]:
    return connection.execute(load_queries()[name], parameters).fetchall()


def fetch_one(
    connection: sqlite3.Connection,
    name: str,
    parameters: tuple[Any, ...] = (),
) -> sqlite3.Row | None:
    return connection.execute(load_queries()[name], parameters).fetchone()
