from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from equipment.admin_inlines import DeviceInline
from rooms.models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "device_count", "public_link")
    list_display_links = ("id",)
    list_editable = ("name",)
    search_fields = ("name",)
    ordering = ("name", "pk")
    list_per_page = 10
    readonly_fields = ("slug",)
    inlines = (DeviceInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(device_count=Count("devices"))

    @admin.display(description="Устройств", ordering="device_count")
    def device_count(self, obj):
        return obj.device_count

    @admin.display(description="На сайте")
    def public_link(self, obj):
        return format_html('<a href="{}">Открыть</a>', obj.get_absolute_url())
