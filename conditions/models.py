from typing import TYPE_CHECKING

from django.db import models

from models import CONDITIONS

if TYPE_CHECKING:
    from equipment.models import Device


class Condition(models.Model):
    class Code(models.TextChoices):
        WORKING = "working", "исправно"
        SERVICE = "service", "требует обслуживания"
        REPAIR = "repair", "в ремонте"
        RETIRED = "retired", "списано"

    code = models.CharField(
        "Код состояния", max_length=12, choices=Code.choices, unique=True,
        help_text="Постоянный код; название определяется автоматически.",
    )
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
            models.CheckConstraint(
                condition=models.Q(code__in=(
                    "working", "service", "repair", "retired",
                )), name="known_condition_code",
            ),
        ]

    @classmethod
    def code_for_name(cls, name: str) -> str:
        return next(
            (code.value for code in cls.Code if code.label == name), ""
        )

    def clean(self) -> None:
        super().clean()
        if self.code in self.Code.values:
            self.name = str(self.Code(self.code).label)

    def save(self, *args, **kwargs) -> None:
        if not self.code:
            self.code = self.code_for_name(str(self.name))
        if self.code in self.Code.values:
            self.name = str(self.Code(self.code).label)
            if kwargs.get("update_fields") is not None:
                fields = set(kwargs["update_fields"]) | {"name"}
                kwargs["update_fields"] = fields
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return str(self.name)
