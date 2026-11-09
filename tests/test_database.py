import json
import shutil
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path
from typing import cast

import pytest
from django.http import HttpResponse
from django.test import Client
from pytest_django.asserts import assertContains

from db.database import (
    BASE_DIR, get_connection, initialize_database,
)
from db.import_json import import_data
from db.queries import fetch_all, fetch_one, load_queries


def get_response(
    client: Client, url: str, parameters: dict[str, str] | None = None,
) -> HttpResponse:
    return cast(HttpResponse, client.get(url, parameters or {}))


def test_import_preserves_ids_relations_and_is_repeatable(
    web_database: Path,
) -> None:
    assert import_data(BASE_DIR / "data", web_database) == {
        "rooms": 0, "users": 0, "conditions": 0, "devices": 0,
    }
    with closing(get_connection(web_database)) as connection:
        device = fetch_one(connection, "device", (1,))
        assert device is not None
        assert device["room_id"] == 1
        assert device["room_name"] == "Кухня"
        assert device["condition"] == "требует обслуживания"
        assert len(fetch_all(connection, "conditions")) == 4
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_all_twelve_catalog_queries_execute(web_database: Path) -> None:
    arguments = {
        "room": (1,), "device": (1,), "room_devices": (1,),
        "search_devices": ("%", "%", "%", None, None, None, None, None, None),
        "room_statistics": (0,), "service_due": (date.today().year,),
    }
    assert len(load_queries()) == 12
    with closing(get_connection(web_database)) as connection:
        for name in load_queries():
            rows = fetch_all(connection, name, arguments.get(name, ()))
            assert isinstance(rows, list)
        totals = fetch_one(connection, "device_totals")
        assert totals is not None
        assert totals["total_devices"] == 3
        assert totals["total_price"] == pytest.approx(146970.5)


def test_foreign_keys_and_constraints_are_enforced(web_database: Path) -> None:
    with closing(get_connection(web_database)) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        for sql in (
            "UPDATE devices SET room_id = 999 WHERE id = 1",
            "DELETE FROM rooms WHERE id = 1",
            "UPDATE devices SET price = -1 WHERE id = 1",
            "UPDATE devices SET condition_id = 999 WHERE id = 1",
        ):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(sql)
            connection.rollback()


def test_missing_database_is_not_created_silently(tmp_path: Path) -> None:
    path = tmp_path / "missing.sqlite"
    with pytest.raises(FileNotFoundError):
        get_connection(path)
    assert not path.exists()


@pytest.fixture
def import_source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    source.mkdir()
    for name in ("rooms", "devices", "conditions", "users"):
        shutil.copy2(BASE_DIR / "data" / f"{name}.json", source)
    return source


def test_conflicting_import_does_not_overwrite_or_partly_insert(
    web_database: Path, import_source: Path,
) -> None:
    rooms_path = import_source / "rooms.json"
    rooms = json.loads(rooms_path.read_text(encoding="utf-8"))
    rooms.insert(0, {"id": 10, "name": "Новая комната"})
    rooms_path.write_text(json.dumps(rooms), encoding="utf-8")
    with closing(get_connection(web_database)) as connection:
        connection.execute("UPDATE users SET login = 'changed' WHERE id = 1")
        connection.commit()
    with pytest.raises(ValueError, match="Конфликт"):
        import_data(import_source, web_database)
    with closing(get_connection(web_database)) as connection:
        assert fetch_one(connection, "room", (10,)) is None
        assert connection.execute(
            "SELECT login FROM users WHERE id = 1"
        ).fetchone()[0] == "changed"


def test_duplicate_source_ids_roll_back_whole_import(
    tmp_path: Path, import_source: Path,
) -> None:
    path = import_source / "devices.json"
    devices = json.loads(path.read_text(encoding="utf-8"))
    devices.append(devices[0])
    path.write_text(json.dumps(devices), encoding="utf-8")
    database = tmp_path / "duplicate.sqlite"
    with pytest.raises(ValueError, match="Повторяющиеся идентификаторы"):
        import_data(import_source, database)
    with closing(get_connection(database)) as connection:
        assert fetch_all(connection, "rooms") == []


def test_missing_source_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="rooms.json"):
        import_data(tmp_path, tmp_path / "missing.sqlite")


def test_empty_database_has_zero_statistics(tmp_path: Path) -> None:
    database = tmp_path / "empty.sqlite"
    initialize_database(database)
    with closing(get_connection(database)) as connection:
        totals = fetch_one(connection, "device_totals")
        assert totals is not None
        assert totals["total_devices"] == totals["total_price"] == 0
        assert totals["average_price"] == 0
        assert totals["oldest_year"] is None
        assert fetch_all(connection, "room_statistics", (0,)) == []


def test_empty_and_retired_only_rooms_are_available(
    web_database: Path,
) -> None:
    with closing(get_connection(web_database)) as connection:
        connection.execute("INSERT INTO rooms VALUES (4, 'Кладовая')")
        connection.execute(
            "UPDATE devices SET condition_id = "
            "(SELECT id FROM conditions WHERE name = 'списано') WHERE id = 1"
        )
        connection.commit()
        available = fetch_all(connection, "empty_rooms")
        assert {r["id"] for r in available} == {1, 4}
        stats = fetch_all(connection, "room_statistics", (0,))
        empty = next(row for row in stats if row["id"] == 4)
        assert empty["device_count"] == 0
        totals = fetch_one(connection, "device_totals")
        assert totals is not None
        assert totals["total_price"] == pytest.approx(100980)
        assert {row["id"] for row in fetch_all(
            connection, "room_statistics", (1,)
        )} == {1, 2, 3}


@pytest.mark.usefixtures("web_database")
@pytest.mark.parametrize("url", [
    "/devices/search/", "/devices/statistics/", "/rooms/available/",
])
def test_new_pages_work(client: Client, url: str) -> None:
    assert get_response(client, url).status_code == 200


@pytest.mark.usefixtures("web_database")
def test_search_combines_filters_and_uses_sql(client: Client) -> None:
    response = get_response(client, "/devices/search/", {
        "q": "Samsung", "room_id": "2", "condition": "исправно",
        "max_price": "53000",
    })
    assertContains(response, "Телевизор в гостиной")
    assert "Холодильник на кухне" not in response.content.decode()
    response = get_response(client, "/devices/search/", {"q": "' OR 1=1 --"})
    assertContains(response, "По заданным условиям устройства не найдены.")
    # % и _ ищутся как пользовательский текст, а не как шаблоны SQL.
    for value in ("%", "_"):
        assertContains(get_response(client, "/devices/search/", {"q": value}),
                       "По заданным условиям устройства не найдены.")


@pytest.mark.usefixtures("web_database")
@pytest.mark.parametrize("parameters", [
    {"max_price": "-1"}, {"max_price": "abc"},
    {"room_id": "abc"}, {"room_id": "999"},
    {"condition": "unknown"}, {"q": "x" * 151},
])
def test_bad_search_parameters_are_displayed(
    client: Client, parameters: dict[str, str],
) -> None:
    response = get_response(client, "/devices/search/", parameters)
    assert response.status_code == 200
    assert 'class="errorlist"' in response.content.decode()


@pytest.mark.usefixtures("web_database")
def test_statistics_having_filter_and_invalid_input(client: Client) -> None:
    assertContains(get_response(client, "/devices/statistics/?min_count=2"),
                   "Нет помещений, соответствующих условиям.")
    response = get_response(client, "/devices/statistics/?min_count=-1")
    assert response.status_code == 200
    assert 'class="errorlist"' in response.content.decode()


def test_web_pages_show_changes_from_sqlite(
    client: Client, web_database: Path,
) -> None:
    with closing(get_connection(web_database)) as connection:
        connection.execute("UPDATE rooms SET name = 'Офис' WHERE id = 1")
        connection.commit()
    assertContains(get_response(client, "/rooms/"), "Офис")
    assertContains(get_response(client, "/devices/1/"), "Офис")


def test_service_query_matches_domain_rules(web_database: Path) -> None:
    with closing(get_connection(web_database)) as connection:
        due_now = fetch_all(connection, "service_due", (2026,))
        assert {row["id"] for row in due_now} == {1}
        due_later = fetch_all(connection, "service_due", (2035,))
        assert {row["id"] for row in due_later} == {1, 2}
        # Даже при большом возрасте устройство в ремонте исключено.
        connection.execute(
            "UPDATE devices SET condition_id = "
            "(SELECT id FROM conditions WHERE name = 'списано') WHERE id = 1"
        )
        due_after_retirement = fetch_all(connection, "service_due", (2035,))
        assert {row["id"] for row in due_after_retirement} == {2}
