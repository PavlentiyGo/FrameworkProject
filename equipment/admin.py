from django.contrib import admin

from equipment.models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "room", "condition", "price")
    list_filter = ("room", "condition", "device_type")
    search_fields = ("name", "manufacturer", "model", "room__name")
    list_select_related = ("room", "condition")
