from typing import cast

import pytest
from django.http import HttpResponse
from django.test import Client, override_settings


pytestmark = pytest.mark.usefixtures("web_database")


def get_response(client: Client, url: str) -> HttpResponse:
    """Уточнить тип ответа Django Client для статического анализатора."""
    return cast(HttpResponse, client.get(url))


@pytest.mark.parametrize(
    ("url", "expected_text"),
    [
        ("/", "Сервис учёта бытовой техники"),
        ("/devices/", "Холодильник на кухне"),
        ("/devices/1/", "Atlant"),
        ("/rooms/", "Кухня"),
        ("/rooms/1/", "Холодильник на кухне"),
    ],
)
def test_main_pages(
    client: Client,
    url: str,
    expected_text: str,
) -> None:
    response = get_response(client, url)

    assert response.status_code == 200
    assert expected_text in response.content.decode("utf-8")


@pytest.mark.parametrize(
    ("url", "expected_text"),
    [
        ("/devices/999/", "Устройство не найдено"),
        ("/rooms/999/", "Помещение не найдено"),
    ],
)
def test_missing_objects_return_404(
    client: Client,
    url: str,
    expected_text: str,
) -> None:
    response = get_response(client, url)

    assert response.status_code == 404
    assert expected_text in response.content.decode("utf-8")


def test_path_converter_rejects_non_integer_id(client: Client) -> None:
    assert get_response(client, "/rooms/abc/").status_code == 404


@override_settings(DEBUG=False)
def test_custom_404_page(client: Client) -> None:
    response = get_response(client, "/nonexistent/")

    assert response.status_code == 404
    assert "404 — страница не найдена" in response.content.decode("utf-8")


def test_pages_use_bootstrap_and_navigation(client: Client) -> None:
    content = get_response(client, "/").content.decode("utf-8")

    assert "bootstrap@5.3.3" in content
    assert 'href="/devices/"' in content
    assert 'href="/rooms/"' in content
