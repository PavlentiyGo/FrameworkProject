import pytest

from models import Device, Room


@pytest.fixture
def sample_rooms() -> list[Room]:
    return [Room(1, "Кухня"), Room(2, "Гостиная")]


@pytest.fixture
def sample_devices(sample_rooms: list[Room]) -> list[Device]:
    return [
        Device(
            1,
            "Холодильник",
            "Крупная техника",
            "Atlant",
            "ХМ-4425",
            2022,
            45990.5,
            sample_rooms[0],
            "требует обслуживания",
            3,
        ),
        Device(
            2,
            "Телевизор",
            "Электроника",
            "Samsung",
            "UE43",
            2024,
            52990.0,
            sample_rooms[1],
            "исправно",
            5,
        ),
    ]
