from collections.abc import Iterator
from datetime import date
from typing import Any


Device = dict[str, Any]

CONDITIONS = (
    "исправно",
    "требует обслуживания",
    "в ремонте",
    "списано",
)
SORT_FIELDS = {
    "name": "названию",
    "purchase_year": "году покупки",
    "price": "стоимости",
}


def _next_device_id(devices: list[Device]) -> int:
    return max((int(device["id"]) for device in devices), default=0) + 1


def add_device(
    devices: list[Device],
    name: str,
    device_type: str,
    manufacturer: str,
    model: str,
    purchase_year: int,
    price: float,
    room_name: str,
    condition: str = "исправно",
    service_interval: int = 3,
) -> Device:
    current_year = date.today().year
    text_values = (name, device_type, manufacturer, model, room_name)
    if any(not value.strip() for value in text_values):
        raise ValueError("Текстовые поля устройства не могут быть пустыми")
    if purchase_year < 1900 or purchase_year > current_year:
        raise ValueError("Указан некорректный год покупки")
    if price < 0:
        raise ValueError("Стоимость не может быть отрицательной")
    if service_interval <= 0:
        raise ValueError("Интервал обслуживания должен быть положительным")
    if condition not in CONDITIONS:
        raise ValueError("Указано неизвестное состояние устройства")

    device = {
        "id": _next_device_id(devices),
        "name": name.strip(),
        "device_type": device_type.strip(),
        "manufacturer": manufacturer.strip(),
        "model": model.strip(),
        "purchase_year": purchase_year,
        "price": round(price, 2),
        "room_name": room_name.strip(),
        "condition": condition,
        "service_interval": service_interval,
    }
    devices.append(device)
    return device


def get_device(devices: list[Device], device_id: int) -> Device:
    for device in devices:
        if device["id"] == device_id:
            return device
    raise LookupError(f"Устройство с ID {device_id} не найдено")


def find_devices(devices: list[Device], query: str) -> list[Device]:
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return []

    fields = ("name", "device_type", "manufacturer", "model", "room_name")
    return [
        device
        for device in devices
        if any(
            normalized_query in str(device[field]).casefold()
            for field in fields
        )
    ]


def filter_devices_by_condition(
    devices: list[Device],
    condition: str,
) -> list[Device]:
    if condition not in CONDITIONS:
        raise ValueError("Указано неизвестное состояние устройства")
    return [
        device for device in devices if device["condition"] == condition
    ]


def sort_devices(
    devices: list[Device],
    field: str = "name",
    reverse: bool = False,
) -> list[Device]:
    if field not in SORT_FIELDS:
        raise ValueError("Указано неизвестное поле сортировки")
    return sorted(
        devices,
        key=lambda device: (
            str(device[field]).casefold()
            if field == "name"
            else device[field]
        ),
        reverse=reverse,
    )


def assign_device_to_room(
    devices: list[Device],
    device_id: int,
    room_name: str,
) -> Device:
    if not room_name.strip():
        raise ValueError("Название помещения не может быть пустым")
    device = get_device(devices, device_id)
    device["room_name"] = room_name.strip()
    return device


def update_device_condition(
    devices: list[Device],
    device_id: int,
    new_condition: str,
) -> Device:
    if new_condition not in CONDITIONS:
        raise ValueError("Указано неизвестное состояние устройства")
    device = get_device(devices, device_id)
    device["condition"] = new_condition
    return device


def is_device_available(devices: list[Device], device_id: int) -> bool:
    return get_device(devices, device_id)["condition"] == "исправно"


def get_service_status(
    purchase_year: int,
    service_interval: int,
    current_condition: str,
    current_year: int | None = None,
) -> str:
    year = current_year if current_year is not None else date.today().year
    if purchase_year > year:
        raise ValueError("Год покупки не может быть позднее текущего года")
    if service_interval <= 0:
        raise ValueError("Интервал обслуживания должен быть положительным")
    if current_condition not in CONDITIONS:
        raise ValueError("Указано неизвестное состояние устройства")

    if current_condition == "списано":
        return "Устройство снято с эксплуатации"
    if current_condition == "в ремонте":
        return "Диагностика уже выполняется"
    device_age = year - purchase_year
    if (
        current_condition == "требует обслуживания"
        or device_age >= service_interval
    ):
        return "Рекомендуется провести техническое обслуживание"
    return "Техническое обслуживание пока не требуется"


def iter_devices_due_for_service(
    devices: list[Device],
    current_year: int | None = None,
) -> Iterator[Device]:
    for device in devices:
        status = get_service_status(
            device["purchase_year"],
            device["service_interval"],
            device["condition"],
            current_year,
        )
        if status.startswith("Рекомендуется"):
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
        condition = str(device["condition"])
        room_name = str(device["room_name"])
        by_condition[condition] = by_condition.get(condition, 0) + 1
        by_room[room_name] = by_room.get(room_name, 0) + 1
        total_value += float(device["price"])
        total_age += year - int(device["purchase_year"])

    count = len(devices)
    return {
        "count": count,
        "total_value": round(total_value, 2),
        "average_age": round(total_age / count, 1) if count else 0.0,
        "available_count": sum(
            device["condition"] == "исправно" for device in devices
        ),
        "service_due_count": sum(
            1 for _ in iter_devices_due_for_service(devices, year)
        ),
        "by_condition": by_condition,
        "by_room": by_room,
    }
