from collections.abc import Iterator
from datetime import date
from typing import Any

from models import CONDITIONS, Device, Room


SORT_FIELDS = {
    "name": "названию",
    "purchase_year": "году покупки",
    "price": "стоимости",
}


def _next_device_id(devices: list[Device]) -> int:
    return max((device.id for device in devices), default=0) + 1


def get_or_create_room(rooms: list[Room], name: str) -> tuple[Room, bool]:
    normalized_name = name.strip().casefold()
    if not normalized_name:
        raise ValueError("Название помещения не может быть пустым")

    for room in rooms:
        if room.name.casefold() == normalized_name:
            return room, False

    next_id = max((room.id for room in rooms), default=0) + 1
    room = Room(next_id, name)
    rooms.append(room)
    return room, True


def find_room_by_id(rooms: list[Room], room_id: int) -> Room | None:
    """Найти помещение по идентификатору."""
    for room in rooms:
        if room.id == room_id:
            return room
    return None


def add_device(
    devices: list[Device],
    name: str,
    device_type: str,
    manufacturer: str,
    model: str,
    purchase_year: int,
    price: float,
    room: Room,
    condition: str = "исправно",
    service_interval: int = 3,
) -> Device:
    device = Device(
        device_id=_next_device_id(devices),
        name=name,
        device_type=device_type,
        manufacturer=manufacturer,
        model=model,
        purchase_year=purchase_year,
        price=price,
        room=room,
        condition=condition,
        service_interval=service_interval,
    )
    devices.append(device)
    return device


def get_device(devices: list[Device], device_id: int) -> Device:
    for device in devices:
        if device.id == device_id:
            return device
    raise LookupError(f"Устройство с ID {device_id} не найдено")


def find_devices(devices: list[Device], query: str) -> list[Device]:
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return []

    return [
        device
        for device in devices
        if any(
            normalized_query in value.casefold()
            for value in (
                device.name,
                device.device_type,
                device.manufacturer,
                device.model,
                device.room.name,
            )
        )
    ]


def filter_devices_by_condition(
    devices: list[Device],
    condition: str,
) -> list[Device]:
    if condition not in CONDITIONS:
        raise ValueError("Указано неизвестное состояние устройства")
    return [device for device in devices if device.condition == condition]


def sort_devices(
    devices: list[Device],
    field: str = "name",
    reverse: bool = False,
) -> list[Device]:
    if field not in SORT_FIELDS:
        raise ValueError("Указано неизвестное поле сортировки")

    if field == "name":
        return sorted(
            devices,
            key=lambda device: device.name.casefold(),
            reverse=reverse,
        )
    if field == "purchase_year":
        return sorted(
            devices,
            key=lambda device: device.purchase_year,
            reverse=reverse,
        )
    return sorted(
        devices,
        key=lambda device: device.price,
        reverse=reverse,
    )


def assign_device_to_room(
    devices: list[Device],
    device_id: int,
    room: Room,
) -> Device:
    device = get_device(devices, device_id)
    device.assign_to_room(room)
    return device


def update_device_condition(
    devices: list[Device],
    device_id: int,
    new_condition: str,
) -> Device:
    device = get_device(devices, device_id)
    device.change_condition(new_condition)
    return device


def iter_devices_due_for_service(
    devices: list[Device],
    current_year: int | None = None,
) -> Iterator[Device]:
    for device in devices:
        if device.get_service_status(current_year).startswith("Рекомендуется"):
            yield device


def remove_device(devices: list[Device], device_id: int) -> Device:
    device = get_device(devices, device_id)
    devices.remove(device)
    return device


def get_device_statistics(
    devices: list[Device],
    current_year: int | None = None,
) -> dict[str, Any]:
    year = current_year if current_year is not None else date.today().year
    by_condition = {condition: 0 for condition in CONDITIONS}
    by_room: dict[str, int] = {}
    total_value = 0.0
    total_age = 0

    for device in devices:
        by_condition[device.condition] += 1
        by_room[device.room.name] = by_room.get(device.room.name, 0) + 1
        total_value += device.price
        total_age += year - device.purchase_year

    count = len(devices)
    return {
        "count": count,
        "total_value": round(total_value, 2),
        "average_age": round(total_age / count, 1) if count else 0.0,
        "available_count": sum(device.is_available() for device in devices),
        "service_due_count": sum(
            1 for _ in iter_devices_due_for_service(devices, year)
        ),
        "by_condition": by_condition,
        "by_room": by_room,
    }
