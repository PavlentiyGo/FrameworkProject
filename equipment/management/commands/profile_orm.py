"""Воспроизводимый анализ SQL на реальных страницах без изменения записей."""

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from equipment.models import Device
from rooms.models import Room


def capture(callable_) -> dict[str, Any]:
    with CaptureQueriesContext(connection) as context:
        callable_()
    return {
        "count": len(context),
        "sql": [query["sql"] for query in context.captured_queries],
    }


class Command(BaseCommand):
    help = "Сравнить N+1 и select_related, измерить SQL веб-страниц"

    def add_arguments(self, parser):
        parser.add_argument("--output", type=Path)

    def handle(self, *args, **options):
        def naive():
            return [(item.name, item.room.name, item.condition.name)
                    for item in Device.objects.all()]

        def optimized():
            return [(item.name, item.room.name, item.condition.name)
                    for item in Device.objects.with_related()]

        report = {"naive": capture(naive), "optimized": capture(optimized)}
        client = Client(HTTP_HOST="localhost")
        device = Device.objects.first()
        room = Room.objects.first()
        paths = ["/", "/devices/", "/devices/?page_size=2&page=2",
                 "/devices/search/?condition=исправно", "/devices/statistics/",
                 "/rooms/", "/rooms/available/"]
        if device:
            paths.append(f"/devices/{device.pk}/")
        if room:
            paths.append(room.get_absolute_url())
        for path in paths:
            def visit():
                response = client.get(path)
                if getattr(response, "status_code") != 200:
                    raise CommandError(f"Страница {path} не вернула HTTP 200")
            report[path] = capture(visit)
        for name, result in report.items():
            self.stdout.write(f"{name}: {result['count']} SQL-запросов")
        output = options.get("output")
        if output:
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                              encoding="utf-8")
