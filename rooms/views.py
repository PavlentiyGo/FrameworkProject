from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from devices import find_room_by_id
from models import Device, Room
from storage import load_devices, load_rooms


def _load_room_data() -> tuple[list[Room], list[Device]]:
    rooms_file = settings.BASE_DIR / "data" / "rooms.json"
    devices_file = settings.BASE_DIR / "data" / "devices.json"
    rooms_list = load_rooms(rooms_file)
    return rooms_list, load_devices(devices_file, rooms_list)


def room_list(request: HttpRequest) -> HttpResponse:
    rooms_list, devices_list = _load_room_data()
    room_cards = [
        {
            "room": room,
            "device_count": sum(
                device.room.id == room.id for device in devices_list
            ),
        }
        for room in rooms_list
    ]
    context = {"rooms": rooms_list, "room_cards": room_cards}
    return render(request, "rooms/room_list.html", context)


def room_detail(
    request: HttpRequest,
    room_id: int,
) -> HttpResponse:
    rooms_list, devices_list = _load_room_data()
    room = find_room_by_id(rooms_list, room_id)
    room_devices = [
        device for device in devices_list if device.room.id == room_id
    ]
    context = {"room": room, "devices": room_devices}
    return render(
        request,
        "rooms/room_detail.html",
        context,
        status=404 if room is None else 200,
    )
