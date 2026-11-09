"""Однонаправленный перенос исходной SQLite-базы ПР7 в Django ORM."""

import sqlite3
from contextlib import closing
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.db import models, transaction

from conditions.models import Condition
from equipment.models import Device
from rooms.models import Room
from users.models import User


def _save_new(candidate: models.Model) -> int:
    if candidate.pk <= 0:
        raise ValueError("Исходный ID должен быть положительным")
    manager = type(candidate)._default_manager
    existing = manager.filter(pk=candidate.pk).first()
    if existing is not None:
        if any(
            getattr(existing, field.attname)
            != getattr(candidate, field.attname)
            for field in candidate._meta.fields
            if not field.generated and field.name != "slug"
        ):
            raise ValueError(
                f"Конфликт {candidate._meta.label} ID={candidate.pk}. "
                "Существующие данные не перезаписаны."
            )
        return 0
    candidate.full_clean()
    candidate.save(force_insert=True)
    return 1


@transaction.atomic
def import_pr7(source: Path) -> dict[str, int]:
    source = source.resolve()
    target = Path(settings.DATABASES["default"]["NAME"]).resolve()
    if source == target:
        raise ValueError("Исходная и целевая базы должны отличаться")
    if not source.is_file():
        raise FileNotFoundError(f"Исходная база не найдена: {source}")
    # Исходный файл открыт только на чтение. Структура известна из ПР7.
    source_connection = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
    with closing(source_connection) as conn:
        conn.row_factory = sqlite3.Row
        if conn.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("В исходной базе нарушены внешние ключи")
        rows: dict[str, list[Any]] = {
            "rooms": conn.execute("SELECT id, name FROM rooms").fetchall(),
            "conditions": conn.execute(
                "SELECT id, name FROM conditions"
            ).fetchall(),
            "users": conn.execute(
                "SELECT id, login, password FROM users"
            ).fetchall(),
            "devices": conn.execute("SELECT * FROM devices").fetchall(),
        }
    counts = dict.fromkeys(rows, 0)
    for row in rows["rooms"]:
        counts["rooms"] += _save_new(Room(id=row["id"], name=row["name"]))
    for row in rows["conditions"]:
        counts["conditions"] += _save_new(
            Condition(id=row["id"], name=row["name"],
                      code=Condition.code_for_name(row["name"]))
        )
    for row in rows["users"]:
        user = User(id=row["id"], login=row["login"])
        existing = User.objects.filter(pk=user.pk).first()
        if existing and existing.check_password(row["password"]):
            user.password = existing.password
        else:
            user.set_password(row["password"])
        counts["users"] += _save_new(user)
    for row in rows["devices"]:
        data = dict(row)
        data["price"] = Decimal(str(data["price"])).quantize(Decimal("0.01"))
        counts["devices"] += _save_new(Device(**data))
    return counts
