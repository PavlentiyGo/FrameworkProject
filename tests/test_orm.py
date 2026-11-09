import hashlib
import re
from contextlib import closing
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs, urlsplit
from html import unescape

import pytest
from django.contrib.auth.models import User as AdminUser
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.test import Client

from conditions.models import Condition
from db.database import get_connection
from db.orm_import import import_pr7
from equipment import queries
from equipment.models import Device
from rooms.models import Room
from users.admin import ProjectUserForm
from users.models import User


pytestmark = pytest.mark.usefixtures("web_database")


def response_for(
    client: Client, url: str, data: dict[str, Any] | None = None,
) -> HttpResponse:
    return cast(HttpResponse, client.get(url, data or {}))


def test_models_create_read_update_delete_and_protect_relations() -> None:
    room = Room.objects.create(name="Мастерская")
    device = Device.objects.create(
        name="Дрель", device_type="Инструмент", manufacturer="Bosch",
        model="GSR", purchase_year=2025, price=Decimal("5000.00"),
        room=room, condition=Condition.objects.get(name="исправно"),
    )
    assert room.devices.get().pk == device.pk
    assert device.condition.devices.filter(pk=device.pk).exists()
    device.name = "Шуруповёрт"
    assert Device.objects.get(pk=device.pk).name == "Дрель"
    device.save(update_fields=["name"])
    assert Device.objects.get(pk=device.pk).name == "Шуруповёрт"
    with pytest.raises(ProtectedError):
        room.delete()
    with pytest.raises(ProtectedError):
        device.condition.delete()
    device.delete()
    assert not Device.objects.filter(room=room).exists()
    room.delete()


@pytest.mark.parametrize(("field", "value"), [
    ("price", Decimal("-0.01")), ("purchase_year", 1800),
    ("purchase_year", 9999), ("service_interval", 0), ("name", ""),
])
def test_model_validation(field: str, value: Any) -> None:
    device = Device.objects.get(pk=1)
    setattr(device, field, value)
    with pytest.raises(ValidationError):
        device.full_clean()


def test_database_constraints_not_only_form_validation() -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Device.objects.filter(pk=1).update(price=Decimal("-1"))
    with pytest.raises(IntegrityError), transaction.atomic():
        Room.objects.create(name="Кухня")
    with pytest.raises(IntegrityError), transaction.atomic():
        Condition.objects.create(name="Неизвестное")


def test_import_preserves_source_ids_links_passwords_and_is_repeatable(
    web_database: Path,
) -> None:
    before = hashlib.sha256(web_database.read_bytes()).hexdigest()
    assert import_pr7(web_database) == {
        "rooms": 0, "conditions": 0, "users": 0, "devices": 0,
    }
    assert hashlib.sha256(web_database.read_bytes()).hexdigest() == before
    device = queries.get_device(1)
    assert device.room_id == 1
    assert device.room.name == "Кухня"
    assert device.condition.name == "требует обслуживания"
    assert device.price == Decimal("45990.50")
    user = User.objects.get(pk=1)
    assert user.check_password("home2026")
    assert not user.check_password("wrong")
    assert user.password != "home2026"


def test_import_rolls_back_new_rows_on_target_conflict(
    web_database: Path,
) -> None:
    with closing(get_connection(web_database)) as source:
        source.execute("INSERT INTO rooms VALUES (10, 'Новая комната')")
        source.commit()
    User.objects.filter(pk=1).update(login="changed")
    with pytest.raises(ValueError, match="Конфликт"):
        import_pr7(web_database)
    assert not Room.objects.filter(pk=10).exists()
    assert User.objects.get(pk=1).login == "changed"


def test_import_rejects_broken_source_links(web_database: Path) -> None:
    with closing(get_connection(web_database)) as source:
        source.execute("PRAGMA foreign_keys = OFF")
        source.execute("UPDATE devices SET room_id = 999 WHERE id = 1")
        source.commit()
    with pytest.raises(ValueError, match="внешние ключи"):
        import_pr7(web_database)
    assert Device.objects.get(pk=1).room_id == 1


def test_management_command_reports_success_and_missing_source(
    web_database: Path, tmp_path: Path,
) -> None:
    output = StringIO()
    call_command("import_pr7", source=web_database, stdout=output)
    assert "devices=0" in output.getvalue()
    with pytest.raises(CommandError, match="не найдена"):
        call_command("import_pr7", source=tmp_path / "missing.sqlite")


def test_related_objects_load_in_one_query(django_assert_num_queries) -> None:
    with django_assert_num_queries(1):
        devices = list(queries.device_queryset())
        assert [device.room.name for device in devices]
        assert [device.condition.name for device in devices]


@pytest.mark.parametrize(("filters", "ids"), [
    ({"room_id": 1}, {1}),
    ({"condition": "исправно"}, {2}),
    ({"room_id": 1, "condition": "исправно"}, set()),
    ({"room_id": 2, "condition": "исправно"}, {2}),
    ({"max_price": Decimal("46000")}, {1}),
    ({"q": "Телев", "scope": "name"}, {2}),
    ({"q": "Samsung", "scope": "name"}, set()),
    ({"q": "Samsung", "scope": "all"}, {2}),
    ({"needs_service": True}, {1}),
])
def test_filter_and_search_scenarios(filters: dict[str, Any], ids: set[int]):
    if "room_id" in filters:
        filters["room_id"] = Room.objects.get(pk=filters["room_id"])
    result = queries.filter_devices(filters).values_list("pk", flat=True)
    assert set(result) == ids


def test_exclude_retired_and_service_rules() -> None:
    device = Device.objects.get(pk=1)
    device.change_condition("списано")
    device.save()
    assert set(queries.filter_devices({"hide_retired": True}).values_list(
        "pk", flat=True
    )) == {2, 3}
    assert set(queries.service_due(current_year=2035).values_list(
        "pk", flat=True
    )) == {2}
    assert device.get_service_status() == "Устройство снято с эксплуатации"
    assert not device.is_available()


def test_sorting_by_price_and_related_field() -> None:
    assert list(queries.filter_devices({"sort": "price"}).values_list(
        "pk", flat=True
    )) == [1, 3, 2]
    by_room = list(queries.filter_devices({"sort": "room"}))
    names = [(device.room.name, device.name, device.pk) for device in by_room]
    assert names == sorted(names)


def test_aggregate_annotation_having_and_rooms_without_devices() -> None:
    empty = Room.objects.create(name="Кладовая")
    assert queries.device_totals()["total_price"] == Decimal("146970.50")
    rooms = {room.pk: room for room in queries.room_statistics()}
    assert getattr(rooms[empty.pk], "device_count") == 0
    assert getattr(rooms[empty.pk], "total_price") == 0
    assert empty in queries.empty_rooms()
    assert empty not in queries.room_statistics(min_count=1)
    retired = Condition.objects.get(name="списано")
    state = next(row for row in queries.condition_statistics()
                 if row.pk == retired.pk)
    assert getattr(state, "device_count") == 0
    Device.objects.filter(pk=1).update(condition=retired)
    assert Room.objects.get(pk=1) in queries.empty_rooms()
    assert queries.device_totals()["total_price"] == Decimal("100980.00")


def test_empty_orm_statistics_and_pages(client: Client) -> None:
    Device.objects.all().delete()
    totals = queries.device_totals()
    assert totals["total_devices"] == totals["total_price"] == 0
    assert totals["average_price"] == 0
    assert totals["oldest_year"] is None
    assert response_for(client, "/devices/statistics/").status_code == 200


@pytest.fixture
def many_devices(web_database: Path) -> None:
    room = Room.objects.get(pk=1)
    condition = Condition.objects.get(name="исправно")
    Device.objects.bulk_create([
        Device(
            name=f"Page device {index:02}", device_type="Тест",
            manufacturer="Test", model="P", purchase_year=2025,
            price=Decimal(index), room=room, condition=condition,
        ) for index in range(12)
    ])


@pytest.mark.usefixtures("many_devices")
@pytest.mark.parametrize("url", ["/devices/", "/devices/search/"])
def test_filter_sort_paginate_and_preserve_query(client: Client, url: str):
    parameters = {
        "q": "Page", "room_id": "1", "condition": "исправно",
        "sort": "price_desc", "page_size": "5", "page": "2",
    }
    response = response_for(client, url, parameters)
    assert response.status_code == 200
    page = getattr(response, "context")["page_obj"]
    assert page.paginator.count == 12
    assert page.paginator.num_pages == 3
    expected_prices = list(map(Decimal, [6, 5, 4, 3, 2]))
    assert [d.price for d in page.object_list] == expected_prices
    content = unescape(response.content.decode())
    links = re.findall(r'href="(\?[^\"]+)"', content)
    assert links
    for link in links:
        actual = parse_qs(urlsplit(link).query)
        assert actual["q"] == ["Page"]
        assert actual["room_id"] == ["1"]
        assert actual["condition"] == ["исправно"]
        assert actual["sort"] == ["price_desc"]
        assert actual["page_size"] == ["5"]
        assert len(actual["page"]) == 1


@pytest.mark.usefixtures("many_devices")
@pytest.mark.parametrize(("page", "expected"), [
    ("abc", 1), ("0", 3), ("-1", 3), ("999", 3),
])
def test_invalid_page_numbers_are_handled(
    client: Client, page: str, expected: int,
) -> None:
    response = response_for(client, "/devices/", {
        "q": "Page", "page_size": "5", "page": page,
    })
    assert response.status_code == 200
    assert getattr(response, "context")["page_obj"].number == expected


@pytest.mark.parametrize("parameters", [
    {"sort": "password"}, {"sort": "name; DROP TABLE devices"},
    {"page_size": "0"}, {"page_size": "1000000"}, {"page_size": "abc"},
    {"scope": "unknown"},
])
def test_invalid_sort_and_page_size_show_errors(
    client: Client, parameters: dict[str, str],
) -> None:
    response = response_for(client, "/devices/", parameters)
    assert response.status_code == 200
    assert getattr(response, "context")["form"].errors
    assert Device.objects.count() == 3


def test_pr7_source_no_longer_controls_web_pages(
    client: Client, web_database: Path,
) -> None:
    with closing(get_connection(web_database)) as source:
        source.execute("UPDATE devices SET name = 'Legacy only' WHERE id = 1")
        source.commit()
    content = response_for(client, "/devices/1/").content.decode()
    assert "Legacy only" not in content
    assert "Холодильник на кухне" in content


def test_project_user_admin_requires_password_for_new_user() -> None:
    form = ProjectUserForm(data={"login": "new", "new_password": ""})
    assert not form.is_valid()
    assert "new_password" in form.errors


def test_pagination_can_be_shown_on_initial_three_devices(client: Client):
    response = response_for(client, "/devices/", {
        "page_size": "2", "page": "2",
    })
    page = getattr(response, "context")["page_obj"]
    assert page.paginator.num_pages == 2
    assert len(page.object_list) == 1
    assert "Назад" in response.content.decode()


def test_admin_crud_and_domain_password_hashing(client: Client) -> None:
    administrator = AdminUser.objects.create_superuser(
        username="pr9_admin", password="admin-test-only",
    )
    client.force_login(administrator)
    for url in (
        "/admin/equipment/device/", "/admin/rooms/room/",
        "/admin/conditions/condition/", "/admin/users/user/",
    ):
        assert response_for(client, url).status_code == 200
    response = client.post("/admin/users/user/add/", {
        "login": "new-project-user", "new_password": "new-password",
        "_save": "Сохранить",
    })
    assert getattr(response, "status_code") == 302
    user = User.objects.get(login="new-project-user")
    assert user.check_password("new-password")
    assert not AdminUser.objects.filter(username=user.login).exists()
