"""Подключение к предметной базе SQLite, отдельной от служебной базы Django."""

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "appliances.sqlite"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


def get_connection(
    db_path: str | Path = DB_PATH,
    *,
    create: bool = False,
) -> sqlite3.Connection:
    path = Path(db_path).resolve()
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
    elif not path.is_file():
        raise FileNotFoundError(
            f"База {path} не найдена. Выполните python -m db.import_json"
        )
    # mode=rw не позволяет случайно создать пустую базу при ошибке пути.
    uri = path.as_uri() + ("?mode=rwc" if create else "?mode=rw")
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(db_path: str | Path = DB_PATH) -> None:
    connection = get_connection(db_path, create=True)
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.commit()
    finally:
        connection.close()
