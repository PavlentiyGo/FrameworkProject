from __future__ import annotations

from datetime import date
from typing import Any


CONDITIONS = (
    "исправно",
    "требует обслуживания",
    "в ремонте",
    "списано",
)


class Room:
    def __init__(self, room_id: int, name: str) -> None:
        if room_id <= 0:
            raise ValueError("ID помещения должен быть положительным")
        if not name.strip():
            raise ValueError("Название помещения не может быть пустым")

        self.id = room_id
        self.name = name.strip()

    def __str__(self) -> str:
        return f"{self.name} (ID: {self.id})"

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Room:
        return cls(room_id=int(data["id"]), name=str(data["name"]))


class User:
    def __init__(
        self,
        user_id: int,
        login: str,
        password: str,
    ) -> None:
        if user_id <= 0:
            raise ValueError("ID пользователя должен быть положительным")
        if not login.strip() or not password:
            raise ValueError("Логин и пароль не могут быть пустыми")

        self.id = user_id
        self.login = login.strip()
        self._password = password

    def __str__(self) -> str:
        return f"Пользователь {self.login} (ID: {self.id})"

    def check_password(self, password: str) -> bool:
        return self._password == password

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "login": self.login,
            "password": self._password,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> User:
        return cls(
            user_id=int(data["id"]),
            login=str(data["login"]),
            password=str(data["password"]),
        )


class Device:
    def __init__(
        self,
        device_id: int,
        name: str,
        device_type: str,
        manufacturer: str,
        model: str,
        purchase_year: int,
        price: float,
        room: Room,
        condition: str = "исправно",
        service_interval: int = 3,
    ) -> None:
        current_year = date.today().year
        text_values = (name, device_type, manufacturer, model)
        if device_id <= 0:
            raise ValueError("ID устройства должен быть положительным")
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

        self.id = device_id
        self.name = name.strip()
        self.device_type = device_type.strip()
        self.manufacturer = manufacturer.strip()
        self.model = model.strip()
        self.purchase_year = purchase_year
        self.price = round(price, 2)
        self.room = room
        self._condition = condition
        self.service_interval = service_interval

    @property
    def condition(self) -> str:
        return self._condition

    def __str__(self) -> str:
        return (
            f"{self.name} ({self.device_type}), {self.room.name}, "
            f"состояние: {self.condition}"
        )

    def assign_to_room(self, room: Room) -> None:
        self.room = room

    def change_condition(self, new_condition: str) -> None:
        if new_condition not in CONDITIONS:
            raise ValueError("Указано неизвестное состояние устройства")
        self._condition = new_condition

    def is_available(self) -> bool:
        return self.condition == "исправно"

    def get_service_status(self, current_year: int | None = None) -> str:
        year = current_year if current_year is not None else date.today().year
        if self.purchase_year > year:
            raise ValueError("Год покупки не может быть позднее текущего года")

        if self.condition == "списано":
            return "Устройство снято с эксплуатации"
        if self.condition == "в ремонте":
            return "Диагностика уже выполняется"
        device_age = year - self.purchase_year
        if (
            self.condition == "требует обслуживания"
            or device_age >= self.service_interval
        ):
            return "Рекомендуется провести техническое обслуживание"
        return "Техническое обслуживание пока не требуется"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "device_type": self.device_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "purchase_year": self.purchase_year,
            "price": self.price,
            "room_name": self.room.name,
            "condition": self.condition,
            "service_interval": self.service_interval,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        room: Room,
    ) -> Device:
        return cls(
            device_id=int(data["id"]),
            name=str(data["name"]),
            device_type=str(data["device_type"]),
            manufacturer=str(data["manufacturer"]),
            model=str(data["model"]),
            purchase_year=int(data["purchase_year"]),
            price=float(data["price"]),
            room=room,
            condition=str(data["condition"]),
            service_interval=int(data["service_interval"]),
        )
