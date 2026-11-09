from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from equipment.queries import empty_rooms
from rooms.models import Room


def room_list(request: HttpRequest) -> HttpResponse:
    rooms = Room.objects.annotate(device_count=Count("devices"))
    room_cards = [
        {"room": room, "device_count": getattr(room, "device_count")}
        for room in rooms
    ]
    return render(request, "rooms/room_list.html", {
        "rooms": rooms, "room_cards": room_cards,
    })


def room_detail(request: HttpRequest, room_id: int) -> HttpResponse:
    try:
        room = Room.objects.get(pk=room_id)
    except Room.DoesNotExist:
        room = None
    devices = room.devices.select_related("room", "condition") if room else []
    return render(request, "rooms/room_detail.html", {
        "room": room, "devices": devices,
    }, status=404 if room is None else 200)


def available_rooms(request: HttpRequest) -> HttpResponse:
    return render(request, "rooms/available.html", {"rooms": empty_rooms()})
