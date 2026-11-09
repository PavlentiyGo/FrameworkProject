"""python -m db.import_json: перенос JSON в SQLite без удаления данных."""

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from db.database import BASE_DIR, DB_PATH, get_connection, initialize_database
from models import CONDITIONS
from storage import load_devices, load_rooms, load_users


def _read_conditions(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or any(
        not isinstance(row, dict) for row in data
    ):
        raise ValueError("Состояния должны быть списком объектов")
    rows = [{"id": int(row["id"]), "name": str(row["name"])} for row in data]
    if any(row["id"] <= 0 or row["name"] not in CONDITIONS for row in rows):
        raise ValueError("Некорректное состояние устройства")
    if len({row["name"] for row in rows}) != len(rows):
        raise ValueError("Повторяющиеся названия состояний")
    # Старые JSON содержат три состояния; четвёртое уже поддерживает ПР3.
    next_id = max((row["id"] for row in rows), default=0) + 1
    for name in CONDITIONS:
        if not any(row["name"] == name for row in rows):
            rows.append({"id": next_id, "name": name})
            next_id += 1
    return rows


def _insert_rows(
    connection: sqlite3.Connection,
    select_sql: str,
    insert_sql: str,
    rows: list[tuple[Any, ...]],
) -> int:
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError("Повторяющиеся идентификаторы в JSON")
    pending = []
    for row in rows:
        existing = connection.execute(select_sql, (row[0],)).fetchone()
        if existing is None:
            pending.append(row)
        elif tuple(existing) != row:
            raise ValueError(
                f"Конфликт записи ID={row[0]}: база отличается от JSON. "
                "Существующая запись не перезаписана."
            )
    connection.executemany(insert_sql, pending)
    return len(pending)


def import_data(
    data_dir: Path = BASE_DIR / "data",
    db_path: Path = DB_PATH,
) -> dict[str, int]:
    for name in ("rooms", "users", "devices", "conditions"):
        if not (data_dir / f"{name}.json").is_file():
            raise FileNotFoundError(f"Отсутствует {name}.json в {data_dir}")
    rooms = load_rooms(data_dir / "rooms.json")
    users = load_users(data_dir / "users.json")
    devices = load_devices(data_dir / "devices.json", rooms)
    conditions = _read_conditions(data_dir / "conditions.json")
    condition_ids = {row["name"]: row["id"] for row in conditions}
    initialize_database(db_path)
    connection = get_connection(db_path)
    try:
        counts = {}
        counts["rooms"] = _insert_rows(
            connection,
            "SELECT id, name FROM rooms WHERE id = ?",
            "INSERT INTO rooms (id, name) VALUES (?, ?)",
            [(room.id, room.name) for room in rooms],
        )
        counts["users"] = _insert_rows(
            connection,
            "SELECT id, login, password FROM users WHERE id = ?",
            "INSERT INTO users (id, login, password) VALUES (?, ?, ?)",
            [
                (user.id, user.login, user.to_dict()["password"])
                for user in users
            ],
        )
        counts["conditions"] = _insert_rows(
            connection,
            "SELECT id, name FROM conditions WHERE id = ?",
            "INSERT INTO conditions (id, name) VALUES (?, ?)",
            [(row["id"], row["name"]) for row in conditions],
        )
        counts["devices"] = _insert_rows(
            connection,
            "SELECT id, name, device_type, manufacturer, model, "
            "purchase_year, price, room_id, condition_id, service_interval "
            "FROM devices WHERE id = ?",
            "INSERT INTO devices (id, name, device_type, manufacturer, model, "
            "purchase_year, price, room_id, condition_id, service_interval) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    device.id, device.name, device.device_type,
                    device.manufacturer, device.model, device.purchase_year,
                    device.price, device.room.id,
                    condition_ids[device.condition], device.service_interval,
                )
                for device in devices
            ],
        )
        connection.commit()
        return counts
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=BASE_DIR / "data")
    parser.add_argument("--database", type=Path, default=DB_PATH)
    args = parser.parse_args()
    counts = import_data(args.data_dir, args.database)
    print(f"База данных: {args.database}")
    print("Добавлено: " + ", ".join(f"{k}={v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
