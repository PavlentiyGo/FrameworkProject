from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from devices import get_device
from models import Device
from storage import load_devices, load_rooms


def _load_device_data() -> list[Device]:
    rooms_file = settings.BASE_DIR / "data" / "rooms.json"
    devices_file = settings.BASE_DIR / "data" / "devices.json"
    rooms_list = load_rooms(rooms_file)
    return load_devices(devices_file, rooms_list)


def device_list(request: HttpRequest) -> HttpResponse:
    """Передать устройства из JSON-хранилища в шаблон списка."""
    context = {"devices": _load_device_data()}
    return render(request, "equipment/device_list.html", context)


def device_detail(
    request: HttpRequest,
    device_id: int,
) -> HttpResponse:
    """Показать устройство или вернуть шаблон с HTTP 404."""
    try:
        device = get_device(_load_device_data(), device_id)
    except LookupError:
        device = None

    context = {
        "device": device,
        "service_status": device.get_service_status() if device else "",
        "is_available": device.is_available() if device else False,
    }
    return render(
        request,
        "equipment/device_detail.html",
        context,
        status=404 if device is None else 200,
    )
