"""Техника с внешними ключами на помещение и состояние."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, ClassVar

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from conditions.models import Condition
from equipment.managers import DeviceManager
from models import Device as LegacyDevice
from models import Room as LegacyRoom


def validate_purchase_year(value: int) -> None:
    if value < 1900 or value > date.today().year:
        raise ValidationError("Год покупки должен быть от 1900 до текущего.")


class Device(models.Model):
    name = models.CharField("Название", max_length=200)
    notes = models.TextField("Примечание", blank=True, default="")
    device_type = models.CharField("Тип", max_length=100)
    manufacturer = models.CharField("Производитель", max_length=100)
    model = models.CharField("Модель", max_length=100)
    purchase_year = models.PositiveIntegerField(
        "Год покупки", validators=[validate_purchase_year],
    )
    price = models.DecimalField(
        "Стоимость", max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    room = models.ForeignKey(
        "rooms.Room", on_delete=models.PROTECT, related_name="devices",
        verbose_name="Помещение",
    )
    condition = models.ForeignKey(
        "conditions.Condition", on_delete=models.PROTECT,
        related_name="devices", verbose_name="Состояние",
    )
    service_interval = models.PositiveIntegerField(
        "Интервал обслуживания, лет", default=3,
        validators=[MinValueValidator(1)],
        help_text="Плановый интервал по возрасту, не история ремонтов.",
    )
    next_service_year = models.GeneratedField(
        expression=models.F("purchase_year") + models.F("service_interval"),
        output_field=models.PositiveIntegerField(), db_persist=True,
        verbose_name="Плановый год обслуживания",
    )
    # Узкое исключение для invariant Model.objects в django-stubs.
    objects: ClassVar[DeviceManager] = DeviceManager()  # type: ignore
    if TYPE_CHECKING:
        room_id: int
        condition_id: int

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "устройство"
        verbose_name_plural = "устройства"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="device_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(service_interval__gt=0),
                name="device_service_interval_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(purchase_year__gte=1900),
                name="device_purchase_year_minimum",
            ),
        ]

    def is_available(self) -> bool:
        return self.condition.code == Condition.Code.WORKING

    def get_service_status(self, current_year: int | None = None) -> str:
        # Сохраняем проверенную предметную логику консольной версии ПР3.
        device = LegacyDevice(
            self.pk, self.name, self.device_type,
            self.manufacturer, self.model,
            self.purchase_year, float(self.price),
            LegacyRoom(self.room_id, self.room.name),
            self.condition.name, self.service_interval,
        )
        return device.get_service_status(current_year)

    def change_condition(self, name: str) -> None:
        """Изменить состояние в памяти; save() сохраняет его в базе."""
        self.condition = Condition.objects.get(name=name)

    def __str__(self) -> str:
        return self.name
