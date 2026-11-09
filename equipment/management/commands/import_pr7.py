import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from db.orm_import import import_pr7


class Command(BaseCommand):
    help = "Перенести данные SQLite ПР7 в ORM, сохранив ID и связи"

    def add_arguments(self, parser):
        parser.add_argument("--source", type=Path)

    def handle(self, *args, **options):
        source = options["source"] or settings.APPLIANCES_DB_PATH
        try:
            counts = import_pr7(Path(source))
        except (OSError, ValueError, sqlite3.Error,
                ValidationError, IntegrityError) as error:
            raise CommandError(str(error)) from error
        summary = ", ".join(f"{key}={value}" for key, value in counts.items())
        self.stdout.write(self.style.SUCCESS(f"Добавлено: {summary}"))
        self.stdout.write("Исходная база сохранена без изменений.")
