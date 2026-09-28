import json
from pathlib import Path
from typing import Any

from models import Device, Room, User


def _load_json_list(filename: str | Path) -> list[dict[str, Any]]:
    path = Path(filename)
    if not path.exists():
        return []

    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Файл {path} содержит некорректный JSON"
        ) from error
    except OSError as error:
        raise RuntimeError(f"Не удалось прочитать файл {path}") from error

    if not isinstance(data, list) or not all(
        isinstance(item, dict) for item in data
    ):
        raise RuntimeError("Файл данных должен содержать список объектов")
    return data


def _save_json_list(
    filename: str | Path,
    data: list[dict[str, Any]],
) -> None:
    path = Path(filename)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
    except OSError as error:
        raise RuntimeError(f"Не удалось сохранить файл {path}") from error


def load_rooms(filename: str | Path) -> list[Room]:
    try:
        return [Room.from_dict(item) for item in _load_json_list(filename)]
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError("Некорректные данные помещений") from error


def save_rooms(filename: str | Path, rooms: list[Room]) -> None:
    _save_json_list(filename, [room.to_dict() for room in rooms])


def load_users(filename: str | Path) -> list[User]:
    try:
        return [User.from_dict(item) for item in _load_json_list(filename)]
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError("Некорректные данные пользователей") from error


def save_users(filename: str | Path, users: list[User]) -> None:
    _save_json_list(filename, [user.to_dict() for user in users])


def load_devices(
    filename: str | Path,
    rooms: list[Room],
) -> list[Device]:
    rooms_by_name = {room.name.casefold(): room for room in rooms}
    devices: list[Device] = []
    try:
        for item in _load_json_list(filename):
            room_name = str(item["room_name"])
            room = rooms_by_name.get(room_name.casefold())
            if room is None:
                raise ValueError(f"Неизвестное помещение: {room_name}")
            devices.append(Device.from_dict(item, room))
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError("Некорректные данные устройств") from error
    return devices


def save_devices(filename: str | Path, devices: list[Device]) -> None:
    _save_json_list(filename, [device.to_dict() for device in devices])
