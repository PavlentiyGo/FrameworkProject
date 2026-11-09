from typing import Any, cast

from django import forms
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from conditions.models import Condition
from equipment import queries
from equipment.forms import DeviceSearchForm, StatisticsForm
from equipment.models import Device


def _listing_context(
    request: HttpRequest, *, search_only: bool = False,
) -> dict[str, Any]:
    form = DeviceSearchForm(request.GET if request.GET else None)
    cast(forms.ChoiceField, form.fields["condition"]).choices = [
        ("", "Любое состояние"),
        *Condition.objects.values_list("name", "name"),
    ]
    valid = form.is_valid() if form.is_bound else True
    searched = valid and (form.is_bound or not search_only)
    data = form.cleaned_data if form.is_bound and valid else {}
    devices = (
        queries.filter_devices(data) if searched else Device.objects.none()
    )
    paginator = Paginator(devices, data.get("page_size") or 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    parameters = request.GET.copy()
    parameters.pop("page", None)
    return {
        "form": form, "searched": searched,
        "devices": page_obj.object_list, "page_obj": page_obj,
        "query_string": parameters.urlencode(),
    }


def device_list(request: HttpRequest) -> HttpResponse:
    return render(request, "equipment/device_list.html",
                  _listing_context(request))


def device_detail(request: HttpRequest, device_id: int) -> HttpResponse:
    try:
        device = queries.get_device(device_id)
    except Device.DoesNotExist:
        device = None
    return render(request, "equipment/device_detail.html", {
        "device": device,
        "service_status": device.get_service_status() if device else "",
        "is_available": device.is_available() if device else False,
    }, status=404 if device is None else 200)


def device_search(request: HttpRequest) -> HttpResponse:
    return render(request, "equipment/device_search.html",
                  _listing_context(request, search_only=True))


def statistics(request: HttpRequest) -> HttpResponse:
    form = StatisticsForm(request.GET)
    valid = form.is_valid()
    return render(request, "equipment/statistics.html", {
        "form": form, "totals": queries.device_totals(),
        "room_statistics": (
            queries.room_statistics(form.cleaned_data["min_count"] or 0)
            if valid else []
        ),
        "condition_statistics": queries.condition_statistics(),
        "service_due": queries.service_due_rows(),
    })
