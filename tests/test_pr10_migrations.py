import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


@pytest.mark.django_db(transaction=True)
def test_pr10_data_migrations_preserve_ids_labels_and_links():
    previous = [
        ("rooms", "0001_initial"), ("conditions", "0001_initial"),
        ("equipment", "0001_initial"),
    ]
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    try:
        executor.migrate(previous)
        apps = executor.loader.project_state(previous).apps
        Room = apps.get_model("rooms", "Room")
        Condition = apps.get_model("conditions", "Condition")
        Device = apps.get_model("equipment", "Device")
        room = Room.objects.create(id=10, name="Аудитория 301")
        labels = ("исправно", "требует обслуживания", "в ремонте", "списано")
        for pk, label in enumerate(labels, start=10):
            Condition.objects.create(id=pk, name=label)
        Device.objects.create(
            id=10, name="Дрель", device_type="Инструмент", manufacturer="Test",
            model="T", purchase_year=2022, price=100, service_interval=3,
            room_id=room.pk, condition_id=10,
        )
        executor = MigrationExecutor(connection)
        executor.migrate(latest)
        apps = executor.loader.project_state(latest).apps
        Room = apps.get_model("rooms", "Room")
        Condition = apps.get_model("conditions", "Condition")
        Device = apps.get_model("equipment", "Device")
        assert Room.objects.get(pk=10).slug.endswith("-10")
        assert list(Condition.objects.order_by("pk").values_list(
            "code", flat=True
        )) == ["working", "service", "repair", "retired"]
        device = Device.objects.get(pk=10)
        assert device.room_id == 10
        assert device.condition_id == 10
        assert device.next_service_year == 2025
    finally:
        MigrationExecutor(connection).migrate(latest)
