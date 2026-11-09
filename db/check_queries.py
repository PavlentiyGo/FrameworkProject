"""Выполнить все запросы sql/queries.sql с демонстрационными параметрами."""

import argparse
from contextlib import closing
from datetime import date

from db.database import DB_PATH, get_connection
from db.queries import fetch_all, load_queries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default=str(DB_PATH))
    args = parser.parse_args()
    parameters = {
        "room": (1,), "device": (1,), "room_devices": (1,),
        "search_devices": ("%", "%", "%", None, None, None, None, None, None),
        "room_statistics": (0,), "service_due": (date.today().year,),
    }
    with closing(get_connection(args.database)) as connection:
        for name in load_queries():
            rows = fetch_all(connection, name, parameters.get(name, ()))
            print(f"{name}: OK, строк: {len(rows)}")
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Нарушения внешних ключей: {violations}")
    print("Все запросы выполнены. Внешние ключи корректны.")


if __name__ == "__main__":
    main()
