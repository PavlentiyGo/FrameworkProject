from html import escape

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from devices import find_room_by_id
from homepage.views import html_response, page
from models import Device, Room
from storage import load_devices, load_rooms


def _load_room_data() -> tuple[list[Room], list[Device]]:
    rooms_file = settings.BASE_DIR / "data" / "rooms.json"
    devices_file = settings.BASE_DIR / "data" / "devices.json"
    rooms_list = load_rooms(rooms_file)
    return rooms_list, load_devices(devices_file, rooms_list)


def room_list(request: HttpRequest) -> HttpResponse:
    """Показать помещения из JSON-хранилища."""
    rooms_list, devices_list = _load_room_data()
    items = ""
    for room in rooms_list:
        count = sum(device.room is room for device in devices_list)
        items += f"""
        <a href="/rooms/{room.id}/"
           class="list-group-item list-group-item-action
                  d-flex justify-content-between align-items-center">
            <span>{escape(room.name)}</span>
            <span class="badge text-bg-primary rounded-pill">
                устройств: {count}
            </span>
        </a>
        """

    if not items:
        items = '<div class="alert alert-info">Помещения не найдены.</div>'

    content = f"""
    <h1 class="mb-3">Помещения</h1>
    <p class="text-secondary">
        Данные загружены из <code>data/rooms.json</code>.
    </p>
    <div class="list-group shadow-sm">{items}</div>
    """
    return html_response(page("Помещения", content))


def room_detail(
    request: HttpRequest,
    room_id: int,
) -> HttpResponse:
    """Показать помещение или вернуть HTTP 404."""
    rooms_list, devices_list = _load_room_data()
    room = find_room_by_id(rooms_list, room_id)

    if room is None:
        content = """
        <div class="alert alert-danger">
            <h1>Помещение не найдено</h1>
            <a href="/rooms/" class="btn btn-outline-secondary">
                К списку помещений
            </a>
        </div>
        """
        return html_response(
            page("Помещение не найдено", content),
            status=404,
        )

    items = ""
    for device in devices_list:
        if device.room is room:
            items += f"""
            <a href="/devices/{device.id}/"
               class="list-group-item list-group-item-action">
                {escape(device.name)}
                <small class="text-secondary">
                    — {escape(device.condition)}
                </small>
            </a>
            """

    if not items:
        items = '<div class="alert alert-info">Устройств пока нет.</div>'

    content = f"""
    <h1 class="mb-3">{escape(room.name)}</h1>
    <div class="card shadow-sm mb-3">
        <div class="card-body">
            <p class="card-text"><strong>ID:</strong> {room.id}</p>
            <p class="card-text mb-0">
                <strong>Устройства в помещении:</strong>
            </p>
        </div>
        <div class="list-group list-group-flush">{items}</div>
    </div>
    <a href="/rooms/" class="btn btn-outline-secondary">
        К списку помещений
    </a>
    """
    return html_response(page(room.name, content))
