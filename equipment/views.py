from contextlib import closing
from datetime import date
from typing import cast

from django import forms
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import get_connection
from db.queries import fetch_all, fetch_one
from equipment.forms import DeviceSearchForm, StatisticsForm
from models import Device, Room


def device_list(request: HttpRequest) -> HttpResponse:
    with closing(get_connection(settings.APPLIANCES_DB_PATH)) as connection:
        context = {"devices": fetch_all(connection, "devices")}
    return render(request, "equipment/device_list.html", context)


def device_detail(
    request: HttpRequest,
    device_id: int,
) -> HttpResponse:
    with closing(get_connection(settings.APPLIANCES_DB_PATH)) as connection:
        device = fetch_one(connection, "device", (device_id,))
    # Существующая предметная логика ПР3 остаётся общей для CLI и сайта.
    domain_device = (
        Device.from_dict(
            dict(device), Room(device["room_id"], device["room_name"])
        )
        if device is not None else None
    )
    context = {
        "device": device,
        "service_status": (
            domain_device.get_service_status() if domain_device else ""
        ),
        "is_available": (
            domain_device.is_available() if domain_device else False
        ),
    }
    return render(
        request,
        "equipment/device_detail.html",
        context,
        status=404 if device is None else 200,
    )


def device_search(request: HttpRequest) -> HttpResponse:
    with closing(get_connection(settings.APPLIANCES_DB_PATH)) as connection:
        rooms = fetch_all(connection, "rooms")
        conditions = fetch_all(connection, "conditions")
        form = DeviceSearchForm(request.GET if request.GET else None)
        cast(forms.ChoiceField, form.fields["room_id"]).choices = [
            ("", "Все помещения"),
            *((str(room["id"]), room["name"]) for room in rooms),
        ]
        cast(forms.ChoiceField, form.fields["condition"]).choices = [
            ("", "Любое состояние"),
            *((row["name"], row["name"]) for row in conditions),
        ]
        devices = []
        if form.is_bound and form.is_valid():
            data = form.cleaned_data
            # LIKE ищет подстроку: пользовательские %, _ и \ экранируются.
            term = data["q"].replace("\\", "\\\\")
            pattern = "%" + term.replace("%", "\\%").replace("_", "\\_") + "%"
            room_id = int(data["room_id"]) if data["room_id"] else None
            condition = data["condition"] or None
            price = (
                float(data["max_price"])
                if data["max_price"] is not None else None
            )
            devices = fetch_all(connection, "search_devices", (
                pattern, pattern, pattern, room_id, room_id,
                condition, condition, price, price,
            ))
    return render(request, "equipment/device_search.html", {
        "form": form, "devices": devices,
        "searched": form.is_bound and not form.errors,
    })


def statistics(request: HttpRequest) -> HttpResponse:
    form = StatisticsForm(request.GET)
    valid = form.is_valid()
    with closing(get_connection(settings.APPLIANCES_DB_PATH)) as connection:
        context = {
            "form": form,
            "totals": fetch_one(connection, "device_totals"),
            "room_statistics": (
                fetch_all(connection, "room_statistics", (
                    form.cleaned_data["min_count"] or 0,
                )) if valid else []
            ),
            "condition_statistics": fetch_all(
                connection, "condition_statistics"
            ),
            "service_due": fetch_all(
                connection, "service_due", (date.today().year,)
            ),
        }
    return render(request, "equipment/statistics.html", context)
