from datetime import date

def authorize_user(saved_login, saved_password, entered_login, entered_password):
    if entered_login == saved_login and entered_password == saved_password:
        return True
    return False


def add_device(name, device_type, manufacturer, model, purchase_year, price):
    return (
        f"{device_type} «{name}», производитель: {manufacturer}, "
        f"модель: {model}, год покупки: {purchase_year}, "
        f"стоимость: {price:.2f} руб."
    )


def assign_device_to_room(device_name, room_name):
    if room_name == "":
        return f"Для устройства «{device_name}» помещение не указано"
    return f"Устройство «{device_name}» размещено в помещении «{room_name}»"


def update_device_condition(device_name, new_condition):
    if new_condition == "исправно":
        return f"Устройство «{device_name}» исправно"
    if new_condition == "требует обслуживания":
        return f"Устройство «{device_name}» необходимо обслужить"
    if new_condition == "в ремонте":
        return f"Устройство «{device_name}» находится в ремонте"
    return f"Для устройства «{device_name}» указано неизвестное состояние"


def get_service_status(purchase_year, service_interval, current_condition):
    current_year = date.today().year
    device_age = current_year - purchase_year
    service_is_due = device_age >= service_interval
    if current_condition == "в ремонте":
        return "Диагностика уже выполняется"
    if current_condition == "требует обслуживания" or service_is_due:
        return "Рекомендуется провести техническое обслуживание"
    return "Техническое обслуживание пока не требуется"

saved_login = "owner@example.com"
saved_password = "home2026"
entered_login = "owner@example.com"
entered_password = "home2026"

device_name = "Холодильник на кухне"
device_type = "Холодильник"
manufacturer = "Atlant"
model = "ХМ-4425"
room_name = "Кухня"
condition = "требует обслуживания"

purchase_year = 2022
service_interval = 3
price = 45990.50

print("СЕРВИС УЧЕТА БЫТОВОЙ ТЕХНИКИ")

is_authorized = authorize_user(
    saved_login,
    saved_password,
    entered_login,
    entered_password,
)

if is_authorized:
    print("Авторизация выполнена успешно")
    print("Добавлено устройство:")
    print(
        add_device(
            device_name,
            device_type,
            manufacturer,
            model,
            purchase_year,
            price,
        )
    )
    print(assign_device_to_room(device_name, room_name))
    print(update_device_condition(device_name, condition))
    print(get_service_status(purchase_year, service_interval, condition))
else:
    print("Ошибка авторизации: проверьте логин и пароль")
