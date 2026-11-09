from django.http import HttpRequest

from rooms.models import Room


def site_context(request: HttpRequest) -> dict[str, str | int]:
    return {
        "site_name": "Учёт техники",
        "rooms_count": Room.objects.count(),
    }
