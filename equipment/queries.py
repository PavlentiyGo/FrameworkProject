"""ORM-запросы пользовательских сценариев ПР9."""

from datetime import date
from decimal import Decimal
from typing import Any

from django.db.models import Avg, Count, F, Max, Min, Q, QuerySet, Sum

from conditions.models import Condition
from equipment.models import Device
from rooms.models import Room


SORT_FIELDS = {
    "name": ("name", "pk"),
    "price": ("price", "pk"),
    "price_desc": ("-price", "pk"),
    "room": ("room__name", "name", "pk"),
    "newest": ("-purchase_year", "name", "pk"),
}


def device_queryset() -> QuerySet[Device]:
    return Device.objects.select_related("room", "condition")


def get_device(device_id: int) -> Device:
    return device_queryset().get(pk=device_id)


def filter_devices(data: dict[str, Any]) -> QuerySet[Device]:
    devices = device_queryset()
    room = data.get("room_id")
    condition = data.get("condition")
    if room and condition:
        devices = devices.filter(room=room, condition__name=condition)
    elif room:
        devices = devices.filter(room=room)
    elif condition:
        devices = devices.filter(condition__name=condition)
    if data.get("max_price") is not None:
        devices = devices.filter(price__lte=data["max_price"])
    if data.get("hide_retired"):
        devices = devices.exclude(condition__name="списано")
    term = data.get("q")
    if term:
        if data.get("scope") == "name":
            devices = devices.filter(name__icontains=term)
        else:
            devices = devices.filter(
                Q(name__icontains=term) | Q(device_type__icontains=term)
                | Q(manufacturer__icontains=term) | Q(model__icontains=term)
            )
    if data.get("needs_service"):
        devices = service_due(devices)
    # Пользователь выбирает ключ; произвольное имя поля в order_by не попадает.
    fields = SORT_FIELDS.get(data.get("sort") or "name", SORT_FIELDS["name"])
    return devices.order_by(*fields)


def service_due(
    devices: QuerySet[Device] | None = None,
    current_year: int | None = None,
) -> QuerySet[Device]:
    devices = devices if devices is not None else device_queryset()
    year = current_year if current_year is not None else date.today().year
    return devices.exclude(
        condition__name__in=("списано", "в ремонте")
    ).filter(
        Q(condition__name="требует обслуживания")
        | Q(purchase_year__lte=year - F("service_interval"))
    ).order_by("purchase_year", "name", "pk")


def device_totals() -> dict[str, Any]:
    active = ~Q(condition__name="списано")
    return Device.objects.aggregate(
        total_devices=Count("pk"),
        total_price=Sum("price", filter=active, default=Decimal("0")),
        average_price=Avg("price", filter=active, default=Decimal("0")),
        oldest_year=Min("purchase_year"), newest_year=Max("purchase_year"),
        available_count=Count("pk", filter=Q(condition__name="исправно")),
    )


def room_statistics(min_count: int = 0) -> QuerySet[Room]:
    return Room.objects.annotate(
        device_count=Count("devices"),
        total_price=Sum(
            "devices__price", filter=~Q(devices__condition__name="списано"),
            default=Decimal("0"),
        ),
    ).filter(device_count__gte=min_count).order_by(
        "-device_count", "name", "pk"
    )


def condition_statistics() -> QuerySet[Condition]:
    return Condition.objects.annotate(
        device_count=Count("devices"),
        total_price=Sum("devices__price", default=Decimal("0")),
    ).order_by("pk")


def empty_rooms() -> QuerySet[Room]:
    active_room_ids = Device.objects.exclude(
        condition__name="списано"
    ).values("room_id")
    return Room.objects.exclude(pk__in=active_room_ids).order_by("name", "pk")
