from pathlib import Path
from typing import cast

import pytest
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.urls import reverse
from pytest_django.asserts import assertContains, assertTemplateUsed

from models import CONDITIONS, Device, Room
from storage import save_devices, save_rooms


def get_response(client: Client, url: str) -> HttpResponse:
    """Уточнить тип ответа Django Client для Pyright."""
    return cast(HttpResponse, client.get(url))


@pytest.mark.parametrize(
    ("url", "template", "fragment"),
    [
        ("/", "homepage/index.html", "includes/navigation.html"),
        (
            "/devices/",
            "equipment/device_list.html",
            "equipment/includes/device_card.html",
        ),
        (
            "/devices/1/",
            "equipment/device_detail.html",
            "equipment/includes/device_condition.html",
        ),
        (
            "/rooms/",
            "rooms/room_list.html",
            "rooms/includes/room_card.html",
        ),
        (
            "/rooms/1/",
            "rooms/room_detail.html",
            "equipment/includes/device_card.html",
        ),
    ],
)
def test_pages_render_templates_and_fragments(
    client: Client,
    url: str,
    template: str,
    fragment: str,
) -> None:
    response = get_response(client, url)

    assert response.status_code == 200
    assertTemplateUsed(response, template)
    assertTemplateUsed(response, "base.html")
    assertTemplateUsed(response, fragment)
    assertContains(response, reverse("homepage:index"))
    assertContains(response, reverse("equipment:device_list"))
    assertContains(response, reverse("rooms:room_list"))


@pytest.mark.parametrize(
    ("url", "template", "message"),
    [
        (
            "/devices/9999/",
            "equipment/device_detail.html",
            "Устройство не найдено",
        ),
        (
            "/rooms/9999/",
            "rooms/room_detail.html",
            "Помещение не найдено",
        ),
        ("/unknown/", "404.html", "404 — страница не найдена"),
        ("/devices/abc/", "404.html", "404 — страница не найдена"),
    ],
)
@override_settings(DEBUG=False)
def test_missing_objects_and_urls_use_templates(
    client: Client,
    url: str,
    template: str,
    message: str,
) -> None:
    response = get_response(client, url)

    assertTemplateUsed(response, template)
    assertTemplateUsed(response, "base.html")
    assertContains(response, message, status_code=404)


def test_empty_json_collections(client: Client, tmp_path: Path) -> None:
    save_rooms(tmp_path / "data" / "rooms.json", [])
    save_devices(tmp_path / "data" / "devices.json", [])

    with override_settings(BASE_DIR=tmp_path):
        assertContains(
            get_response(client, "/rooms/"), "Помещения не найдены."
        )
        assertContains(
            get_response(client, "/devices/"), "Устройства не найдены."
        )


def test_room_without_devices(client: Client, tmp_path: Path) -> None:
    save_rooms(tmp_path / "data" / "rooms.json", [Room(1, "Кладовая")])
    save_devices(tmp_path / "data" / "devices.json", [])

    with override_settings(BASE_DIR=tmp_path):
        assertContains(
            get_response(client, "/rooms/1/"), "Устройств пока нет."
        )
        assertContains(get_response(client, "/rooms/"), "Устройств: 0")


@pytest.mark.parametrize(
    ("condition", "css_class"),
    list(zip(CONDITIONS, [
        "condition-working",
        "condition-service",
        "condition-repair",
        "condition-retired",
    ])),
)
def test_device_condition_fragment_in_all_views(
    client: Client,
    tmp_path: Path,
    sample_devices: list[Device],
    sample_rooms: list[Room],
    condition: str,
    css_class: str,
) -> None:
    device = sample_devices[0]
    device.change_condition(condition)
    save_rooms(tmp_path / "data" / "rooms.json", sample_rooms)
    save_devices(tmp_path / "data" / "devices.json", [device])

    with override_settings(BASE_DIR=tmp_path):
        for url in ("/devices/", "/devices/1/", "/rooms/1/"):
            response = get_response(client, url)
            assertTemplateUsed(
                response, "equipment/includes/device_condition.html"
            )
            assertContains(response, condition)
            assertContains(response, css_class)


def test_filters_and_related_links(client: Client) -> None:
    assertContains(get_response(client, "/rooms/"), "Всего помещений: 3")
    response = get_response(client, "/devices/1/")
    assertContains(response, "45990,50 ₽")
    room_url = reverse("rooms:room_detail", args=[1])
    assertContains(response, f'href="{room_url}"')
    assertContains(response, "2022")


def test_default_filter_in_room_card() -> None:
    content = render_to_string(
        "rooms/includes/room_card.html",
        {"room": {"id": 1, "name": ""}, "device_count": 0},
    )

    assert "Без названия" in content
    assert reverse("rooms:room_detail", args=[1]) in content


def test_json_names_are_escaped(
    client: Client,
    tmp_path: Path,
    sample_devices: list[Device],
    sample_rooms: list[Room],
) -> None:
    sample_devices[0].name = '<script>alert("name")</script>'
    save_rooms(tmp_path / "data" / "rooms.json", sample_rooms)
    save_devices(tmp_path / "data" / "devices.json", sample_devices)

    with override_settings(BASE_DIR=tmp_path):
        for url in ("/devices/", "/devices/1/", "/rooms/1/"):
            content = get_response(client, url).content.decode("utf-8")
            assert "&lt;script&gt;" in content
            assert sample_devices[0].name not in content


@pytest.mark.parametrize(
    "asset",
    ["css/style.css", "js/main.js", "img/logo.svg"],
)
def test_static_assets_are_found_and_linked(
    client: Client,
    asset: str,
) -> None:
    static_path = "homepage/" + asset

    assert finders.find(static_path)
    assertContains(get_response(client, "/"), "/static/" + static_path)
