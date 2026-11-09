from typing import TYPE_CHECKING

from django.db import models

from models import CONDITIONS

if TYPE_CHECKING:
    from equipment.models import Device


class Condition(models.Model):
    name = models.CharField(
        "Состояние", max_length=50, unique=True,
        choices=[(name, name) for name in CONDITIONS],
    )
    objects = models.Manager["Condition"]()
    if TYPE_CHECKING:
        devices: models.Manager["Device"]

    class Meta:
        ordering = ["pk"]
        verbose_name = "состояние"
        verbose_name_plural = "состояния"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(name__in=CONDITIONS),
                name="known_device_condition",
            ),
        ]

    def __str__(self) -> str:
        return self.name
