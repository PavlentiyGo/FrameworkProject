from django.contrib import admin

from equipment.models import Device


class DeviceInline(admin.TabularInline):
    model = Device
    fields = ("name", "condition", "price", "next_service_year")
    readonly_fields = ("name", "next_service_year")
    extra = 0
    can_delete = False
    show_change_link = True
    verbose_name = "устройство"
    verbose_name_plural = "Устройства помещения"

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("room", "condition")
