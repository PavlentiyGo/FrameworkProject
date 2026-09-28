import pytest

from devices import (
    add_device,
    assign_device_to_room,
    filter_devices_by_condition,
    find_devices,
    get_device_statistics,
    get_or_create_room,
    iter_devices_due_for_service,
    remove_device,
    sort_devices,
    update_device_condition,
)
from models import Device, Room


def test_add_device_assigns_next_id(
    sample_devices: list[Device],
    sample_rooms: list[Room],
) -> None:
    device = add_device(
        sample_devices,
        "Пылесос",
        "Мелкая техника",
        "Bosch",
        "BGS21",
        2025,
        19990,
        sample_rooms[0],
    )

    assert device.id == 3
    assert sample_devices[-1].name == "Пылесос"
    assert device.room is sample_rooms[0]


def test_add_device_rejects_invalid_year(
    sample_devices: list[Device],
    sample_rooms: list[Room],
) -> None:
    with pytest.raises(ValueError):
        add_device(
            sample_devices,
            "Пылесос",
            "Мелкая техника",
            "Bosch",
            "BGS21",
            2999,
            19990,
            sample_rooms[0],
        )


def test_find_devices_ignores_case(sample_devices: list[Device]) -> None:
    result = find_devices(sample_devices, "SAMSUNG")

    assert [device.id for device in result] == [2]


def test_filter_devices_by_condition(
    sample_devices: list[Device],
) -> None:
    result = filter_devices_by_condition(sample_devices, "исправно")

    assert [device.name for device in result] == ["Телевизор"]


def test_sort_devices_does_not_change_source(
    sample_devices: list[Device],
) -> None:
    result = sort_devices(sample_devices, "price", reverse=True)

    assert [device.id for device in result] == [2, 1]
    assert [device.id for device in sample_devices] == [1, 2]


def test_assign_room_and_update_condition(
    sample_devices: list[Device],
) -> None:
    bedroom = Room(3, "Спальня")
    assign_device_to_room(sample_devices, 2, bedroom)
    update_device_condition(sample_devices, 2, "в ремонте")

    assert sample_devices[1].room is bedroom
    assert sample_devices[1].condition == "в ремонте"
    assert not sample_devices[1].is_available()


def test_get_or_create_room_reuses_existing_room(
    sample_rooms: list[Room],
) -> None:
    room, created = get_or_create_room(sample_rooms, " кухня ")

    assert room is sample_rooms[0]
    assert not created


def test_missing_device_raises_domain_error(
    sample_devices: list[Device],
) -> None:
    with pytest.raises(LookupError):
        assign_device_to_room(sample_devices, 999, Room(3, "Спальня"))


@pytest.mark.parametrize(
    ("condition", "expected"),
    [
        ("исправно", "пока не требуется"),
        ("требует обслуживания", "Рекомендуется"),
        ("в ремонте", "Диагностика"),
        ("списано", "снято с эксплуатации"),
    ],
)
def test_get_service_status_for_each_condition(
    condition: str,
    expected: str,
) -> None:
    device = Device(
        1,
        "Устройство",
        "Техника",
        "Производитель",
        "Модель",
        2025,
        1000,
        Room(1, "Комната"),
        condition,
        3,
    )

    assert expected in device.get_service_status(current_year=2026)


def test_generator_returns_only_service_due_devices(
    sample_devices: list[Device],
) -> None:
    result = list(iter_devices_due_for_service(sample_devices, 2026))

    assert [device.id for device in result] == [1]


def test_remove_device(sample_devices: list[Device]) -> None:
    removed = remove_device(sample_devices, 1)

    assert removed.name == "Холодильник"
    assert [device.id for device in sample_devices] == [2]


def test_device_statistics(sample_devices: list[Device]) -> None:
    statistics = get_device_statistics(sample_devices, current_year=2026)

    assert statistics["count"] == 2
    assert statistics["total_value"] == 98980.5
    assert statistics["average_age"] == 3.0
    assert statistics["available_count"] == 1
    assert statistics["service_due_count"] == 1
    assert statistics["by_room"] == {"Кухня": 1, "Гостиная": 1}


def test_str_contains_main_device_data(sample_devices: list[Device]) -> None:
    text = str(sample_devices[0])

    assert "Холодильник" in text
    assert "Кухня" in text
