from pathlib import Path

import pytest

from models import Device, Room, User
from storage import (
    load_devices,
    load_rooms,
    load_users,
    save_devices,
    save_rooms,
    save_users,
)


def test_save_and_load_devices(
    tmp_path: Path,
    sample_devices: list[Device],
    sample_rooms: list[Room],
) -> None:
    filename = tmp_path / "nested" / "devices.json"

    save_devices(filename, sample_devices)
    loaded = load_devices(filename, sample_rooms)

    assert [device.to_dict() for device in loaded] == [
        device.to_dict() for device in sample_devices
    ]
    assert loaded[0].room is sample_rooms[0]


def test_save_and_load_rooms(tmp_path: Path) -> None:
    filename = tmp_path / "rooms.json"
    rooms = [Room(1, "Кухня")]

    save_rooms(filename, rooms)

    assert [room.to_dict() for room in load_rooms(filename)] == [
        room.to_dict() for room in rooms
    ]


def test_save_and_load_users(tmp_path: Path) -> None:
    filename = tmp_path / "users.json"
    users = [User(1, "owner", "secret")]

    save_users(filename, users)
    loaded = load_users(filename)

    assert loaded[0].login == "owner"
    assert loaded[0].check_password("secret")


def test_missing_file_returns_empty_list(tmp_path: Path) -> None:
    assert load_rooms(tmp_path / "missing.json") == []


def test_invalid_json_raises_data_file_error(tmp_path: Path) -> None:
    filename = tmp_path / "devices.json"
    filename.write_text("not-json", encoding="utf-8")

    with pytest.raises(RuntimeError, match="некорректный JSON"):
        load_devices(filename, [])


def test_non_list_json_raises_data_file_error(tmp_path: Path) -> None:
    filename = tmp_path / "rooms.json"
    filename.write_text('{"id": 1}', encoding="utf-8")

    with pytest.raises(RuntimeError, match="список объектов"):
        load_rooms(filename)


def test_device_with_unknown_room_is_rejected(tmp_path: Path) -> None:
    filename = tmp_path / "devices.json"
    filename.write_text(
        '[{"id": 1, "room_name": "Неизвестная"}]',
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="Некорректные данные устройств"):
        load_devices(filename, [])
