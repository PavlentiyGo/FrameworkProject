from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image
from django.contrib.auth.models import User as AdminUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import Client
from django.urls import reverse

from conditions.models import Condition
from equipment.forms import DeviceForm
from equipment.models import Device
from rooms.models import Room


pytestmark = pytest.mark.usefixtures("web_database")


@pytest.fixture
def editor(client: Client, web_database: Path) -> AdminUser:
    user = AdminUser.objects.create_superuser(
        "forms_editor", password="test-only",
    )
    client.force_login(user)
    return user


@pytest.fixture
def valid_data() -> dict[str, str]:
    return {
        "name": "Новый чайник", "device_type": "Чайник",
        "manufacturer": "Test",
        "model": "K1", "purchase_year": str(date.today().year),
        "price": "1234.50", "room": "1", "service_interval": "3",
        "notes": "Первая строка\nВторая строка",
    }


def image_upload(name: str = "room.png"):
    output = BytesIO()
    Image.new("RGB", (60, 40), (20, 100, 160)).save(output, "PNG")
    return SimpleUploadedFile(
        name, output.getvalue(), content_type="image/png",
    )


def test_form_has_explicit_editable_fields_and_bootstrap(valid_data):
    form = DeviceForm(valid_data)
    assert form.is_bound
    assert form.is_valid(), form.errors
    assert "condition" not in form.fields
    assert "next_service_year" not in form.fields
    assert form.fields["current_condition"].disabled
    assert form.fields["room"].widget.attrs["class"] == "form-select"
    assert form.fields["name"].widget.attrs["class"] == "form-control"
    assert form.cleaned_data["price"] == Decimal("1234.50")


@pytest.mark.usefixtures("editor")
def test_create_sets_working_state_and_redirects(client, valid_data):
    valid_data["condition"] = "4"
    valid_data["current_condition"] = "списано"
    response = client.post("/devices/create/", valid_data)
    assert response.status_code == 302
    device = Device.objects.get(name="Новый чайник")
    assert device.condition.code == Condition.Code.WORKING
    assert device.notes == "Первая строка\nВторая строка"
    assert device.next_service_year == date.today().year + 3
    response = client.get(response.url)
    assert "Изменения устройства сохранены" in response.content.decode()


@pytest.mark.usefixtures("editor")
@pytest.mark.parametrize(("field", "value"), [
    ("purchase_year", "9999"), ("purchase_year", "abc"), ("price", "-1"),
    ("service_interval", "0"), ("name", " "), ("name", "X"), ("room", "999"),
])
def test_invalid_create_keeps_input_and_does_not_save(
    client, valid_data, field, value,
):
    valid_data[field] = value
    response = client.post("/devices/create/", valid_data)
    assert response.status_code == 200
    assert response.context["form"].errors
    assert response.context["form"].is_bound
    assert Device.objects.count() == 3
    assert "Новый чайник" in response.content.decode() or field == "name"


@pytest.mark.usefixtures("editor")
def test_empty_post_is_bound_and_does_not_create(client):
    response = client.post("/devices/create/", {})
    assert response.context["form"].is_bound
    assert response.context["form"].errors
    assert Device.objects.count() == 3


@pytest.mark.usefixtures("editor")
def test_edit_excludes_self_but_rejects_duplicate_in_same_room(client):
    existing = Device.objects.get(pk=1)
    data = {
        field: str(getattr(existing, field))
        for field in ("name", "device_type", "manufacturer", "model",
                      "purchase_year", "price", "service_interval", "notes")
    }
    data["room"] = "1"
    assert client.post("/devices/1/edit/", data).status_code == 302
    assert Device.objects.count() == 3
    data.update(name="Телевизор в гостиной", room="2")
    response = client.post("/devices/1/edit/", data)
    assert response.status_code == 200
    assert response.context["form"].non_field_errors()
    assert Device.objects.get(pk=1).room_id == 1


@pytest.mark.usefixtures("editor")
def test_retirement_is_post_only_idempotent_and_preserves_history(client):
    assert client.get("/devices/2/retire/").status_code == 405
    for _ in range(2):
        assert client.post("/devices/2/retire/").status_code == 302
    assert Device.objects.count() == 3
    assert Device.objects.get(pk=2).condition.code == Condition.Code.RETIRED
    assert Room.objects.get(pk=2).devices.count() == 1


def test_retired_device_cannot_be_moved_via_form(valid_data):
    device = Device.objects.get(pk=1)
    device.change_condition("списано")
    device.save()
    valid_data["room"] = "2"
    form = DeviceForm(valid_data, instance=device)
    assert not form.is_valid()
    assert "Нельзя перемещать" in str(form.non_field_errors())


@pytest.mark.usefixtures("editor")
def test_missing_edit_and_retirement_return_404(client):
    assert client.get("/devices/999/edit/").status_code == 404
    assert client.post("/devices/999/retire/").status_code == 404


def test_unauthorized_users_cannot_change_data(client, valid_data):
    assert client.get("/devices/create/").status_code == 302
    assert client.post("/devices/create/", valid_data).status_code == 302
    viewer = AdminUser.objects.create_user("viewer11", password="test-only")
    client.force_login(viewer)
    assert client.post("/devices/create/", valid_data).status_code == 403
    assert client.post("/devices/1/retire/").status_code == 403
    assert Device.objects.count() == 3


def test_post_requires_csrf_token(editor, valid_data):
    protected = Client(enforce_csrf_checks=True)
    protected.force_login(editor)
    assert protected.post("/devices/create/", valid_data).status_code == 403
    protected.get("/devices/create/")
    token = protected.cookies["csrftoken"].value
    response = protected.post("/devices/create/", {
        **valid_data, "csrfmiddlewaretoken": token,
    })
    assert response.status_code == 302


@pytest.mark.usefixtures("editor")
def test_database_error_is_shown_as_form_error(client, valid_data):
    with patch("equipment.models.Device.save", side_effect=IntegrityError):
        response = client.post("/devices/create/", valid_data)
    assert response.status_code == 200
    assert "Не удалось сохранить" in response.content.decode()
    assert Device.objects.count() == 3


@pytest.mark.usefixtures("editor")
def test_photo_upload_replacement_and_display(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    room = Room.objects.get(pk=1)
    url = reverse("rooms:room_photo", args=[room.slug])
    response = client.post(url, {"photo": image_upload()})
    assert response.status_code == 302
    room.refresh_from_db()
    first_name = room.photo.name
    assert (tmp_path / first_name).is_file()
    assert first_name.startswith("rooms/1/")
    content = client.get(room.get_absolute_url()).content.decode()
    assert room.photo.url in content
    response = client.post(url, {"photo": image_upload("new.png")})
    assert response.status_code == 302
    room.refresh_from_db()
    assert room.photo.name != first_name


@pytest.mark.usefixtures("editor")
def test_invalid_and_oversize_images_are_rejected(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    room = Room.objects.get(pk=1)
    url = reverse("rooms:room_photo", args=[room.slug])
    bad = SimpleUploadedFile(
        "bad.png", b"not an image", content_type="image/png",
    )
    response = client.post(url, {"photo": bad})
    assert response.status_code == 200
    assert response.context["form"].errors
    upload = image_upload()
    upload.size = 6 * 1024 * 1024
    from rooms.forms import RoomPhotoForm

    form = RoomPhotoForm({}, {"photo": upload}, instance=room)
    assert not form.is_valid()
    room.refresh_from_db()
    assert not room.photo
