import json
import re
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import cast

import pytest
from django.contrib import admin
from django.contrib.auth.models import Group, User as AdminUser
from django.core.management import call_command
from django.http import HttpResponse
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.db import connection

from conditions.models import Condition
from equipment import queries
from equipment.managers import DeviceQuerySet
from equipment.models import Device
from rooms.models import Room


pytestmark = pytest.mark.usefixtures("web_database")


def response_for(client: Client, path: str) -> HttpResponse:
    return cast(HttpResponse, client.get(path))


@pytest.fixture
def administrator(client: Client, web_database: Path) -> AdminUser:
    user = AdminUser.objects.create_superuser(
        "pr10_admin", password="test-only",
    )
    client.force_login(user)
    return user


def test_slug_transliteration_uniqueness_and_stability(client: Client):
    room = Room.objects.create(name="Аудитория 301")
    assert re.fullmatch(r"[a-z0-9-]+", room.slug)
    assert room.slug.endswith(f"-{room.pk}")
    assert "auditori" in room.slug
    url = room.get_absolute_url()
    assert response_for(client, url).status_code == 200
    room.name = "Другое название"
    room.save(update_fields=["name"])
    room.refresh_from_db()
    assert room.get_absolute_url() == url
    other = Room.objects.create(name="Аудитория-301")
    assert room.slug != other.slug
    assert response_for(client, "/rooms/not-existing-slug/").status_code == 404
    assert response_for(client, "/rooms/1/").status_code == 200


def test_generated_service_year_is_recomputed_by_database() -> None:
    device = Device.objects.get(pk=1)
    assert device.next_service_year == 2025
    Device.objects.filter(pk=1).update(service_interval=7)
    device.refresh_from_db()
    assert device.next_service_year == 2029
    assert not Device._meta.get_field("next_service_year").editable
    working = Condition.objects.get(code=Condition.Code.WORKING)
    Device.objects.filter(pk=1).update(condition=working)
    assert 1 not in queries.service_due(current_year=2026).values_list(
        "pk", flat=True
    )
    assert 1 in queries.service_due(current_year=2029).values_list(
        "pk", flat=True
    )


def test_custom_manager_returns_chainable_and_complete_queryset() -> None:
    assert isinstance(Device.objects.with_related(), DeviceQuerySet)
    active_ids = Device.objects.active().values_list("pk", flat=True)
    assert set(active_ids) == {1, 2, 3}
    assert list(Device.objects.working().for_room(2).values_list(
        "pk", flat=True
    )) == [2]
    assert list(Device.objects.in_repair().values_list("pk", flat=True)) == [3]
    device = Device.objects.get(pk=2)
    device.change_condition("списано")
    device.save()
    assert Device.objects.count() == 3
    assert Device.objects.retired().count() == 1
    assert Device.objects.active().count() == 2
    assert queries.device_totals()["retired_count"] == 1
    assert queries.device_totals()["total_price"] == Decimal("93980.5")


def test_values_annotation_uses_one_sql_query(django_assert_num_queries):
    with django_assert_num_queries(1):
        result = list(queries.service_due_rows())
    assert result
    assert set(result[0]) == {
        "id", "name", "room_name", "condition_label", "next_service_year",
    }
    assert result[0]["room_name"] == "Кухня"


def test_context_processor_shared_values_and_actual_count(client: Client):
    for path in ("/", "/devices/", "/rooms/"):
        response = response_for(client, path)
        context = getattr(response, "context")
        assert context["site_name"] == "Учёт техники"
        assert context["rooms_count"] == 3
        assert "Помещения (3)" in response.content.decode()
    Room.objects.create(name="Кладовая")
    response = response_for(client, "/")
    assert "Помещения (4)" in response.content.decode()


@pytest.mark.usefixtures("administrator")
def test_admin_search_filter_and_public_room_link(client: Client):
    response = response_for(client, "/admin/equipment/device/?q=Samsung")
    changelist = getattr(response, "context")["cl"]
    assert [obj.pk for obj in changelist.result_list] == [2]
    state = Condition.objects.get(code=Condition.Code.REPAIR)
    response = response_for(client, "/admin/equipment/device/"
                            f"?condition__id__exact={state.pk}")
    result = getattr(response, "context")["cl"].result_list
    assert [obj.pk for obj in result] == [3]
    room = Room.objects.get(pk=1)
    response = response_for(client, f"/admin/rooms/room/{room.pk}/change/")
    assert response.status_code == 200
    assert "Холодильник на кухне" in response.content.decode()
    assert admin.site._registry[Room].view_on_site
    assert response_for(client, room.get_absolute_url()).status_code == 200


@pytest.mark.usefixtures("administrator")
def test_admin_list_editable_saves_valid_price(client: Client):
    response = response_for(client, "/admin/equipment/device/")
    rows = list(getattr(response, "context")["cl"].result_list)
    data = {
        "form-TOTAL_FORMS": str(len(rows)),
        "form-INITIAL_FORMS": str(len(rows)),
        "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
        "_save": "Сохранить",
    }
    for index, device in enumerate(rows):
        data[f"form-{index}-id"] = str(device.pk)
        data[f"form-{index}-condition"] = str(device.condition_id)
        data[f"form-{index}-price"] = (
            "100.25" if device.pk == 1 else str(device.price)
        )
    response = client.post("/admin/equipment/device/", data)
    assert getattr(response, "status_code") == 302
    assert Device.objects.get(pk=1).price == Decimal("100.25")


@pytest.mark.usefixtures("administrator")
def test_room_inline_can_change_existing_device(client: Client):
    room = Room.objects.get(pk=1)
    path = f"/admin/rooms/room/{room.pk}/change/"
    response = response_for(client, path)
    inline = getattr(response, "context")["inline_admin_formsets"][0]
    prefix = inline.formset.prefix
    state = Condition.objects.get(code=Condition.Code.REPAIR)
    data = {
        "name": room.name, "_save": "Сохранить",
        f"{prefix}-TOTAL_FORMS": "1", f"{prefix}-INITIAL_FORMS": "1",
        f"{prefix}-MIN_NUM_FORMS": "0", f"{prefix}-MAX_NUM_FORMS": "1000",
        f"{prefix}-0-id": "1", f"{prefix}-0-room": str(room.pk),
        f"{prefix}-0-condition": str(state.pk),
        f"{prefix}-0-price": "45990.50",
    }
    response = client.post(path, data)
    assert getattr(response, "status_code") == 302
    assert Device.objects.get(pk=1).condition.code == Condition.Code.REPAIR


@pytest.mark.usefixtures("administrator")
def test_admin_actions_preserve_history_and_exclude_repair(client: Client):
    client.post("/admin/equipment/device/", {
        "action": "mark_for_service", "_selected_action": ["2", "3"],
    })
    assert Device.objects.get(pk=2).condition.code == Condition.Code.SERVICE
    assert Device.objects.get(pk=3).condition.code == Condition.Code.REPAIR
    client.post("/admin/equipment/device/", {
        "action": "retire_devices", "_selected_action": ["2"],
    })
    assert Device.objects.retired().count() == 1
    assert Device.objects.count() == 3
    assert queries.device_totals()["retired_count"] == 1
    assert Room.objects.get(pk=2) in queries.empty_rooms()


def test_groups_and_read_only_staff_permissions(client: Client):
    output = StringIO()
    call_command("setup_admin_groups", stdout=output)
    call_command("setup_admin_groups", stdout=output)
    viewer = Group.objects.get(name="Наблюдатели техники")
    editor = Group.objects.get(name="Операторы техники")
    assert viewer.permissions.count() == 4
    assert editor.permissions.count() == 12
    delete_permissions = editor.permissions.filter(
        codename__startswith="delete_",
    )
    assert not delete_permissions.exists()
    staff = AdminUser.objects.create_user(
        username="viewer", password="test-only", is_staff=True,
    )
    staff.groups.add(viewer)
    client.force_login(staff)
    assert response_for(client, "/admin/equipment/device/").status_code == 200
    add_response = response_for(client, "/admin/equipment/device/add/")
    assert add_response.status_code == 403
    assert not staff.has_perm("equipment.change_device")
    client.post("/admin/equipment/device/", {
        "action": "retire_devices", "_selected_action": ["2"],
    })
    assert Device.objects.get(pk=2).condition.code == Condition.Code.WORKING


def test_non_staff_cannot_enter_admin(client: Client):
    user = AdminUser.objects.create_user("ordinary", password="test-only")
    client.force_login(user)
    assert response_for(client, "/admin/").status_code == 302


def test_profile_command_compares_actual_queries(tmp_path):
    output = tmp_path / "profile.json"
    call_command("profile_orm", output=output, stdout=StringIO())
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["naive"]["count"] == 7
    assert report["optimized"]["count"] == 1
    assert report["/devices/"]["count"] == 5
    assert report["/devices/?page_size=2&page=2"]["count"] == 5


def test_public_list_has_no_n_plus_one_growth(client: Client):
    with CaptureQueriesContext(connection) as context:
        response_for(client, "/devices/?page_size=50")
    initial_count = len(context)
    sample = Device.objects.get(pk=1)
    Device.objects.bulk_create([
        Device(
            name=f"Дополнительное {index}", device_type="Тест",
            manufacturer="Test", model="T", purchase_year=2025,
            price=Decimal("1"), room=sample.room, condition=sample.condition,
        ) for index in range(12)
    ])
    with CaptureQueriesContext(connection) as context:
        response_for(client, "/devices/?page_size=50")
    assert len(context) == initial_count


@override_settings(DEBUG=False)
def test_debug_toolbar_is_not_public_by_default(client: Client):
    response = response_for(client, "/devices/")
    assert b"djDebug" not in response.content
    assert response_for(client, "/__debug__/render_panel/").status_code == 404
