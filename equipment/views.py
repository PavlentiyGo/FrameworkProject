from html import escape

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from devices import get_device
from homepage.views import html_response, page
from models import Device
from storage import load_devices, load_rooms


def _load_device_data() -> list[Device]:
    rooms_file = settings.BASE_DIR / "data" / "rooms.json"
    devices_file = settings.BASE_DIR / "data" / "devices.json"
    rooms_list = load_rooms(rooms_file)
    return load_devices(devices_file, rooms_list)


def _condition_badge(condition: str) -> str:
    return {
        "исправно": "text-bg-success",
        "требует обслуживания": "text-bg-warning",
        "в ремонте": "text-bg-danger",
        "списано": "text-bg-secondary",
    }.get(condition, "text-bg-secondary")


def device_list(request: HttpRequest) -> HttpResponse:
    """Показать устройства из JSON-хранилища."""
    items = ""
    for device in _load_device_data():
        badge = _condition_badge(device.condition)
        items += f"""
        <a href="/devices/{device.id}/"
           class="list-group-item list-group-item-action">
            <div class="d-flex justify-content-between align-items-center">
                <strong>{escape(device.name)}</strong>
                <span class="badge {badge}">
                    {escape(device.condition)}
                </span>
            </div>
            <small class="text-secondary">
                {escape(device.device_type)} · {escape(device.room.name)}
            </small>
        </a>
        """

    if not items:
        items = '<div class="alert alert-info">Устройства не найдены.</div>'

    content = f"""
    <h1 class="mb-3">Устройства</h1>
    <p class="text-secondary">
        Данные загружены из <code>data/devices.json</code>.
    </p>
    <div class="list-group shadow-sm">{items}</div>
    """
    return html_response(page("Устройства", content))


def device_detail(
    request: HttpRequest,
    device_id: int,
) -> HttpResponse:
    """Показать устройство или вернуть HTTP 404."""
    try:
        device = get_device(_load_device_data(), device_id)
    except LookupError:
        content = """
        <div class="alert alert-danger">
            <h1>Устройство не найдено</h1>
            <a href="/devices/" class="btn btn-outline-secondary">
                К списку устройств
            </a>
        </div>
        """
        return html_response(
            page("Устройство не найдено", content),
            status=404,
        )

    badge = _condition_badge(device.condition)
    service_status = escape(device.get_service_status())
    content = f"""
    <h1 class="mb-3">{escape(device.name)}</h1>
    <div class="card shadow-sm">
        <div class="card-body">
            <dl class="row mb-0">
                <dt class="col-sm-4">ID</dt>
                <dd class="col-sm-8">{device.id}</dd>
                <dt class="col-sm-4">Тип</dt>
                <dd class="col-sm-8">{escape(device.device_type)}</dd>
                <dt class="col-sm-4">Производитель и модель</dt>
                <dd class="col-sm-8">
                    {escape(device.manufacturer)} {escape(device.model)}
                </dd>
                <dt class="col-sm-4">Год покупки</dt>
                <dd class="col-sm-8">{device.purchase_year}</dd>
                <dt class="col-sm-4">Стоимость</dt>
                <dd class="col-sm-8">{device.price:.2f} ₽</dd>
                <dt class="col-sm-4">Помещение</dt>
                <dd class="col-sm-8">
                    <a href="/rooms/{device.room.id}/">
                        {escape(device.room.name)}
                    </a>
                </dd>
                <dt class="col-sm-4">Состояние</dt>
                <dd class="col-sm-8">
                    <span class="badge {badge}">
                        {escape(device.condition)}
                    </span>
                </dd>
                <dt class="col-sm-4">Обслуживание</dt>
                <dd class="col-sm-8">{service_status}</dd>
            </dl>
        </div>
    </div>
    <a href="/devices/" class="btn btn-outline-secondary mt-3">
        К списку устройств
    </a>
    """
    return html_response(page(device.name, content))
