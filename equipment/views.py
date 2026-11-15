from typing import Any, cast

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from conditions.models import Condition
from equipment import queries
from equipment.forms import DeviceForm, DeviceSearchForm, StatisticsForm
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


def _device_form(request: HttpRequest, device: Device | None = None):
    form = DeviceForm(
        request.POST if request.method == "POST" else None, instance=device,
    )
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                saved = form.save(commit=False)
                if device is None:
                    state, _ = Condition.objects.get_or_create(
                        code=Condition.Code.WORKING,
                        defaults={"name": str(Condition.Code.WORKING.label)},
                    )
                    saved.condition = state
                saved.save()
        except IntegrityError:
            form.add_error(
                None, "Не удалось сохранить данные. Проверьте ввод."
            )
        else:
            messages.success(request, "Изменения устройства сохранены.")
            return redirect("equipment:device_detail", device_id=saved.pk)
    return render(request, "equipment/device_form.html", {
        "form": form, "device": device,
        "heading": (
            "Редактирование устройства" if device else "Новое устройство"
        ),
    })


@login_required(login_url="admin:login")
@permission_required("equipment.add_device", raise_exception=True)
@require_http_methods(["GET", "POST"])
def device_create(request: HttpRequest) -> HttpResponse:
    return _device_form(request)


@login_required(login_url="admin:login")
@permission_required("equipment.change_device", raise_exception=True)
@require_http_methods(["GET", "POST"])
def device_edit(request: HttpRequest, device_id: int) -> HttpResponse:
    device = get_object_or_404(Device.objects.with_related(), pk=device_id)
    return _device_form(request, device)


@require_POST
@login_required(login_url="admin:login")
@permission_required("equipment.change_device", raise_exception=True)
def device_retire(request: HttpRequest, device_id: int) -> HttpResponse:
    device = get_object_or_404(Device, pk=device_id)
    with transaction.atomic():
        state, _ = Condition.objects.get_or_create(
            code=Condition.Code.RETIRED,
            defaults={"name": str(Condition.Code.RETIRED.label)},
        )
        Device.objects.filter(pk=device.pk).update(condition=state)
    messages.success(request, "Устройство списано. Запись сохранена.")
    return redirect("equipment:device_detail", device_id=device.pk)
