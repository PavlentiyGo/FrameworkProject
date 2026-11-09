"""ORM-запросы пользовательских сценариев ПР9."""

from decimal import Decimal
from typing import Any

from django.db.models import Avg, Count, F, Max, Min, Q, QuerySet, Sum

from conditions.models import Condition
from equipment.models import Device
from equipment.managers import DeviceQuerySet
from rooms.models import Room


SORT_FIELDS = {
    "name": ("name", "pk"),
    "price": ("price", "pk"),
    "price_desc": ("-price", "pk"),
    "room": ("room__name", "name", "pk"),
    "newest": ("-purchase_year", "name", "pk"),
}


def device_queryset() -> DeviceQuerySet:
    return Device.objects.with_related()


def get_device(device_id: int) -> Device:
    return device_queryset().get(pk=device_id)


def filter_devices(data: dict[str, Any]) -> DeviceQuerySet:
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
        devices = devices.active()
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
    devices: DeviceQuerySet | None = None,
    current_year: int | None = None,
) -> DeviceQuerySet:
    devices = devices if devices is not None else device_queryset()
    return devices.needs_service(current_year).order_by(
        "purchase_year", "name", "pk"
    )


def service_due_rows():
    """Проекция связанных полей одним SQL-запросом, без N+1."""
    return Device.objects.needs_service().annotate(
        room_name=F("room__name"), condition_label=F("condition__name"),
    ).values("id", "name", "room_name", "condition_label", "next_service_year")


def device_totals() -> dict[str, Any]:
    active = ~Q(condition__code=Condition.Code.RETIRED)
    return Device.objects.aggregate(
        total_devices=Count("pk"),
        total_price=Sum("price", filter=active, default=Decimal("0")),
        average_price=Avg("price", filter=active, default=Decimal("0")),
        oldest_year=Min("purchase_year"), newest_year=Max("purchase_year"),
        available_count=Count("pk", filter=Q(
            condition__code=Condition.Code.WORKING,
        )),
        service_count=Count("pk", filter=Q(
            condition__code=Condition.Code.SERVICE,
        )),
        repair_count=Count("pk", filter=Q(
            condition__code=Condition.Code.REPAIR,
        )),
        retired_count=Count("pk", filter=Q(
            condition__code=Condition.Code.RETIRED,
        )),
    )


def room_statistics(min_count: int = 0) -> QuerySet[Room]:
    return Room.objects.annotate(
        device_count=Count("devices"),
        total_price=Sum(
            "devices__price", filter=~Q(
                devices__condition__code=Condition.Code.RETIRED,
            ),
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
    active_room_ids = Device.objects.active().values("room_id")
    return Room.objects.exclude(pk__in=active_room_ids).order_by("name", "pk")
