"""Предметные выборки без скрытого исключения записей из objects.all()."""

from datetime import date
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import Q
from typing_extensions import Self

from conditions.models import Condition

if TYPE_CHECKING:
    from equipment.models import Device


class DeviceQuerySet(models.QuerySet["Device"]):
    if TYPE_CHECKING:
        model: type[Device]

    def with_related(self) -> Self:
        return self.select_related("room", "condition")

    def active(self) -> Self:
        return self.exclude(condition__code=Condition.Code.RETIRED)

    def working(self) -> Self:
        return self.filter(condition__code=Condition.Code.WORKING)

    def in_repair(self) -> Self:
        return self.filter(condition__code=Condition.Code.REPAIR)

    def retired(self) -> Self:
        return self.filter(condition__code=Condition.Code.RETIRED)

    def for_room(self, room_id: int) -> Self:
        return self.filter(room_id=room_id)

    def needs_service(self, year: int | None = None) -> Self:
        year = year if year is not None else date.today().year
        return self.exclude(condition__code__in=(
            Condition.Code.RETIRED, Condition.Code.REPAIR,
        )).filter(
            Q(condition__code=Condition.Code.SERVICE)
            | Q(next_service_year__lte=year)
        )


class DeviceManager(models.Manager["Device"]):
    def get_queryset(self) -> DeviceQuerySet:
        return DeviceQuerySet(self.model, using=self._db)

    def with_related(self) -> DeviceQuerySet:
        return self.get_queryset().with_related()

    def active(self) -> DeviceQuerySet:
        return self.get_queryset().active()

    def working(self) -> DeviceQuerySet:
        return self.get_queryset().working()

    def in_repair(self) -> DeviceQuerySet:
        return self.get_queryset().in_repair()

    def retired(self) -> DeviceQuerySet:
        return self.get_queryset().retired()

    def for_room(self, room_id: int) -> DeviceQuerySet:
        return self.get_queryset().for_room(room_id)

    def needs_service(self, year: int | None = None) -> DeviceQuerySet:
        return self.get_queryset().needs_service(year)
