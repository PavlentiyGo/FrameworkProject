from datetime import date
from pathlib import Path

from auth import authorize_user
from devices import (
    SORT_FIELDS,
    add_device,
    assign_device_to_room,
    filter_devices_by_condition,
    find_devices,
    get_device,
    get_device_statistics,
    get_or_create_room,
    remove_device,
    sort_devices,
    update_device_condition,
)
from models import CONDITIONS, Device, Room, User
from storage import (
    load_devices,
    load_rooms,
    load_users,
    save_devices,
    save_rooms,
)
from utils import input_choice, input_float, input_int, input_non_empty


DATA_DIRECTORY = Path(__file__).parent / "data"
DEVICES_FILE = DATA_DIRECTORY / "devices.json"
ROOMS_FILE = DATA_DIRECTORY / "rooms.json"
USERS_FILE = DATA_DIRECTORY / "users.json"

MENU = """
=== Сервис учёта бытовой техники ===
1. Показать все устройства
2. Добавить устройство
3. Найти устройство
4. Отфильтровать по состоянию
5. Отсортировать устройства
6. Назначить помещение
7. Изменить состояние
8. Проверить доступность и обслуживание
9. Снять устройство с учёта
10. Показать статистику
0. Выход
"""


def show_devices(devices: list[Device]) -> None:
    if not devices:
        print("Устройства не найдены.")
        return
    print(
        f"{'ID':<4} {'Название':<24} {'Тип':<18} "
        f"{'Помещение':<16} {'Состояние':<24} {'Стоимость':>12}"
    )
    print("-" * 106)
    for device in devices:
        print(
            f"{device.id:<4} {device.name:<24.24} "
            f"{device.device_type:<18.18} "
            f"{device.room.name:<16.16} "
            f"{device.condition:<24.24} "
            f"{device.price:>10.2f} ₽"
        )


def _save(devices: list[Device], rooms: list[Room]) -> None:
    save_devices(DEVICES_FILE, devices)
    save_rooms(ROOMS_FILE, rooms)
    print("Изменения сохранены.")


def _add_device(devices: list[Device], rooms: list[Room]) -> None:
    current_year = date.today().year
    room, _ = get_or_create_room(
        rooms,
        input_non_empty("Помещение: "),
    )
    device = add_device(
        devices,
        input_non_empty("Название: "),
        input_non_empty("Тип устройства: "),
        input_non_empty("Производитель: "),
        input_non_empty("Модель: "),
        input_int("Год покупки: ", 1900, current_year),
        input_float("Стоимость: ", 0),
        room,
        service_interval=input_int(
            "Интервал обслуживания в годах: ", 1
        ),
    )
    _save(devices, rooms)
    print(f"Устройство «{device.name}» добавлено с ID {device.id}.")


def _find_devices(devices: list[Device]) -> None:
    query = input_non_empty("Строка поиска: ")
    show_devices(find_devices(devices, query))


def _filter_devices(devices: list[Device]) -> None:
    for number, condition in enumerate(CONDITIONS, start=1):
        print(f"{number}. {condition}")
    number = input_int("Номер состояния: ", 1, len(CONDITIONS))
    show_devices(filter_devices_by_condition(devices, CONDITIONS[number - 1]))


def _sort_devices(devices: list[Device]) -> None:
    fields = tuple(SORT_FIELDS)
    for number, field in enumerate(fields, start=1):
        print(f"{number}. По {SORT_FIELDS[field]}")
    number = input_int("Поле сортировки: ", 1, len(fields))
    direction = input_choice(
        "Порядок (1 — по возрастанию, 2 — по убыванию): ",
        ("1", "2"),
    )
    show_devices(
        sort_devices(devices, fields[number - 1], direction == "2")
    )


def _assign_room(devices: list[Device], rooms: list[Room]) -> None:
    device_id = input_int("ID устройства: ", 1)
    room, _ = get_or_create_room(
        rooms,
        input_non_empty("Новое помещение: "),
    )
    device = assign_device_to_room(devices, device_id, room)
    _save(devices, rooms)
    print(f"Устройство «{device.name}» размещено в «{room.name}».")


def _update_condition(devices: list[Device], rooms: list[Room]) -> None:
    device_id = input_int("ID устройства: ", 1)
    for number, condition in enumerate(CONDITIONS, start=1):
        print(f"{number}. {condition}")
    number = input_int("Новое состояние: ", 1, len(CONDITIONS))
    device = update_device_condition(
        devices,
        device_id,
        CONDITIONS[number - 1],
    )
    _save(devices, rooms)
    print(f"Состояние устройства «{device.name}» обновлено.")


def _show_status(devices: list[Device]) -> None:
    device = get_device(devices, input_int("ID устройства: ", 1))
    availability = (
        "доступно к эксплуатации"
        if device.is_available()
        else "недоступно к обычной эксплуатации"
    )
    print(f"Устройство «{device.name}» {availability}.")
    print(device.get_service_status())


def _remove_device(devices: list[Device], rooms: list[Room]) -> None:
    device_id = input_int("ID устройства: ", 1)
    device = get_device(devices, device_id)
    confirmation = input_choice(
        f"Снять «{device.name}» с учёта? (да/нет): ",
        ("да", "нет"),
    )
    if confirmation == "нет":
        print("Операция отменена.")
        return
    remove_device(devices, device_id)
    _save(devices, rooms)
    print(f"Устройство «{device.name}» снято с учёта.")


def _show_statistics(devices: list[Device]) -> None:
    statistics = get_device_statistics(devices)
    print(f"Всего устройств: {statistics['count']}")
    print(f"Доступно к эксплуатации: {statistics['available_count']}")
    print(f"Требуют обслуживания: {statistics['service_due_count']}")
    print(f"Общая стоимость: {statistics['total_value']:.2f} ₽")
    print(f"Средний возраст: {statistics['average_age']:.1f} года")
    print("По состояниям:")
    for condition, count in statistics["by_condition"].items():
        print(f"  {condition}: {count}")
    print("По помещениям:")
    for room_name, count in statistics["by_room"].items():
        print(f"  {room_name}: {count}")


def _authenticate(users: list[User]) -> User | None:
    print("Для входа введите данные владельца.")
    login = input_non_empty("Логин: ")
    password = input_non_empty("Пароль: ")
    return authorize_user(users, login, password)


def main() -> None:
    try:
        users = load_users(USERS_FILE)
        rooms = load_rooms(ROOMS_FILE)
        devices = load_devices(DEVICES_FILE, rooms)
    except RuntimeError as error:
        print(f"Ошибка загрузки данных: {error}")
        return

    user = _authenticate(users)
    if user is None:
        print("Ошибка авторизации: проверьте логин и пароль.")
        return

    print(f"Авторизация выполнена успешно: {user.login}.")
    actions = {
        "1": lambda: show_devices(devices),
        "2": lambda: _add_device(devices, rooms),
        "3": lambda: _find_devices(devices),
        "4": lambda: _filter_devices(devices),
        "5": lambda: _sort_devices(devices),
        "6": lambda: _assign_room(devices, rooms),
        "7": lambda: _update_condition(devices, rooms),
        "8": lambda: _show_status(devices),
        "9": lambda: _remove_device(devices, rooms),
        "10": lambda: _show_statistics(devices),
    }

    while True:
        print(MENU)
        choice = input("Выберите действие: ").strip()
        if choice == "0":
            print("Работа программы завершена.")
            return
        action = actions.get(choice)
        if action is None:
            print("Неизвестная команда. Повторите ввод.")
            continue
        try:
            action()
        except (LookupError, RuntimeError, ValueError) as error:
            print(f"Операция не выполнена: {error}")


if __name__ == "__main__":
    main()
