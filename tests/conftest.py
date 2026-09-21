
import pytest

from devices import Device


@pytest.fixture
def sample_devices() -> list[Device]:
    return [
        {
            "id": 1,
            "name": "Холодильник",
            "device_type": "Крупная техника",
            "manufacturer": "Atlant",
            "model": "ХМ-4425",
            "purchase_year": 2022,
            "price": 45990.5,
            "room_name": "Кухня",
            "condition": "требует обслуживания",
            "service_interval": 3,
        },
        {
            "id": 2,
            "name": "Телевизор",
            "device_type": "Электроника",
            "manufacturer": "Samsung",
            "model": "UE43",
            "purchase_year": 2024,
            "price": 52990.0,
            "room_name": "Гостиная",
            "condition": "исправно",
            "service_interval": 5,
        },
    ]
