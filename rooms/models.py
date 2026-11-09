"""Помещения, управляемые миграциями Django."""

from typing import TYPE_CHECKING
from uuid import uuid4

from django.db import models, transaction
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode

if TYPE_CHECKING:
    from equipment.models import Device


class Room(models.Model):
    name = models.CharField(
        "Название", max_length=150, unique=True,
        help_text="Название помещения, в котором размещена техника.",
    )
    slug = models.SlugField(
        "URL-идентификатор", max_length=180, unique=True,
        blank=True, editable=False,
    )
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

    def get_absolute_url(self) -> str:
        return reverse("rooms:room_detail_slug", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs) -> None:
        missing_slug = not self.slug
        if missing_slug:
            self.slug = f"pending-{uuid4().hex}"
        with transaction.atomic(using=kwargs.get("using") or self._state.db):
            super().save(*args, **kwargs)
            if missing_slug:
                base = slugify(unidecode(self.name))[:150].strip("-") or "room"
                self.slug = f"{base}-{self.pk}"
                type(self).objects.filter(pk=self.pk).update(slug=self.slug)
