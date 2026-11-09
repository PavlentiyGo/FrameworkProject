from contextlib import closing

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import get_connection
from db.queries import fetch_all, fetch_one


def room_list(request: HttpRequest) -> HttpResponse:
    with closing(get_connection(settings.APPLIANCES_DB_PATH)) as connection:
        rooms_list = fetch_all(connection, "rooms")
    room_cards = [
        {
            "room": room,
            "device_count": room["device_count"],
        }
        for room in rooms_list
    ]
    context = {"rooms": rooms_list, "room_cards": room_cards}
    return render(request, "rooms/room_list.html", context)


def room_detail(
    request: HttpRequest,
    room_id: int,
) -> HttpResponse:
    with closing(get_connection(settings.APPLIANCES_DB_PATH)) as connection:
        room = fetch_one(connection, "room", (room_id,))
        room_devices = fetch_all(connection, "room_devices", (room_id,))
    context = {"room": room, "devices": room_devices}
    return render(
        request,
        "rooms/room_detail.html",
        context,
        status=404 if room is None else 200,
    )


def available_rooms(request: HttpRequest) -> HttpResponse:
    with closing(get_connection(settings.APPLIANCES_DB_PATH)) as connection:
        rooms = fetch_all(connection, "empty_rooms")
    return render(request, "rooms/available.html", {"rooms": rooms})
