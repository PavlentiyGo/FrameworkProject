"""Помещения, управляемые миграциями Django."""

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from equipment.models import Device


class Room(models.Model):
    name = models.CharField("Название", max_length=150, unique=True)
    objects = models.Manager["Room"]()
    if TYPE_CHECKING:
        devices: models.Manager["Device"]

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "помещение"
        verbose_name_plural = "помещения"
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(name=""), name="room_name_not_empty",
            ),
        ]

    def __str__(self) -> str:
        return self.name
