import pytest

from devices import (
    Device,
    add_device,
    assign_device_to_room,
    filter_devices_by_condition,
    find_devices,
    get_device_statistics,
    get_service_status,
    is_device_available,
    iter_devices_due_for_service,
    remove_device,
    sort_devices,
    update_device_condition,
)


def test_add_device_assigns_next_id(sample_devices: list[Device]) -> None:
    device = add_device(
        sample_devices,
        "Пылесос",
        "Мелкая техника",
        "Bosch",
        "BGS21",
        2025,
        19990,
        "Кладовая",
    )

    assert device["id"] == 3
    assert sample_devices[-1]["name"] == "Пылесос"


def test_add_device_rejects_invalid_year(
    sample_devices: list[Device],
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
            "Кладовая",
        )


def test_find_devices_ignores_case(sample_devices: list[Device]) -> None:
    result = find_devices(sample_devices, "SAMSUNG")

    assert [device["id"] for device in result] == [2]


def test_filter_devices_by_condition(
    sample_devices: list[Device],
) -> None:
    result = filter_devices_by_condition(sample_devices, "исправно")

    assert [device["name"] for device in result] == ["Телевизор"]


def test_sort_devices_does_not_change_source(
    sample_devices: list[Device],
) -> None:
    result = sort_devices(sample_devices, "price", reverse=True)

    assert [device["id"] for device in result] == [2, 1]
    assert [device["id"] for device in sample_devices] == [1, 2]


def test_assign_room_and_update_condition(
    sample_devices: list[Device],
) -> None:
    assign_device_to_room(sample_devices, 2, "Спальня")
    update_device_condition(sample_devices, 2, "в ремонте")

    assert sample_devices[1]["room_name"] == "Спальня"
    assert sample_devices[1]["condition"] == "в ремонте"
    assert not is_device_available(sample_devices, 2)


def test_missing_device_raises_domain_error(
    sample_devices: list[Device],
) -> None:
    with pytest.raises(LookupError):
        assign_device_to_room(sample_devices, 999, "Кухня")


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
    status = get_service_status(2025, 3, condition, current_year=2026)

    assert expected in status


def test_generator_returns_only_service_due_devices(
    sample_devices: list[Device],
) -> None:
    result = list(iter_devices_due_for_service(sample_devices, 2026))

    assert [device["id"] for device in result] == [1]


def test_remove_device(sample_devices: list[Device]) -> None:
    removed = remove_device(sample_devices, 1)

    assert removed["name"] == "Холодильник"
    assert [device["id"] for device in sample_devices] == [2]


def test_device_statistics(sample_devices: list[Device]) -> None:
    statistics = get_device_statistics(sample_devices, current_year=2026)

    assert statistics["count"] == 2
    assert statistics["total_value"] == 98980.5
    assert statistics["average_age"] == 3.0
    assert statistics["available_count"] == 1
    assert statistics["service_due_count"] == 1
    assert statistics["by_room"] == {"Кухня": 1, "Гостиная": 1}
