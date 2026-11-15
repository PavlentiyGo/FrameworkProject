from django.db.models import Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from equipment.queries import empty_rooms
from rooms.models import Room
from rooms.forms import RoomPhotoForm


def room_list(request: HttpRequest) -> HttpResponse:
    rooms = Room.objects.annotate(device_count=Count("devices"))
    room_cards = [
        {"room": room, "device_count": getattr(room, "device_count")}
        for room in rooms
    ]
    return render(request, "rooms/room_list.html", {
        "rooms": rooms, "room_cards": room_cards,
    })


def room_detail(
    request: HttpRequest, room_id: int | None = None, slug: str | None = None,
) -> HttpResponse:
    try:
        lookup = {"slug": slug} if slug is not None else {"pk": room_id}
        room = get_object_or_404(Room, **lookup)
    except Http404:
        room = None
    devices = room.devices.select_related("room", "condition") if room else []
    return render(request, "rooms/room_detail.html", {
        "room": room, "devices": devices,
    }, status=404 if room is None else 200)


def available_rooms(request: HttpRequest) -> HttpResponse:
    return render(request, "rooms/available.html", {"rooms": empty_rooms()})


@login_required(login_url="admin:login")
@permission_required("rooms.change_room", raise_exception=True)
@require_http_methods(["GET", "POST"])
def room_photo(request: HttpRequest, slug: str) -> HttpResponse:
    room = get_object_or_404(Room, slug=slug)
    form = RoomPhotoForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        instance=room,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Фотография помещения обновлена.")
        return redirect(room)
    return render(request, "rooms/room_photo_form.html", {
        "form": form, "room": room,
    })
