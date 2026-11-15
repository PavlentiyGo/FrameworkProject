from django.contrib import admin, messages

from conditions.models import Condition
from equipment.models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "room", "condition", "price", "next_service_year",
        "available",
    )
    list_display_links = ("id", "name")
    list_editable = ("condition", "price")
    list_filter = ("room", "condition", "device_type")
    search_fields = ("name", "manufacturer", "model", "room__name")
    list_select_related = ("room", "condition")
    ordering = ("room__name", "name", "pk")
    list_per_page = 10
    autocomplete_fields = ("room", "condition")
    readonly_fields = ("next_service_year",)
    fieldsets = (
        ("Характеристики", {"fields": (
            "name", "device_type", "manufacturer", "model",
        )}),
        ("Размещение и состояние", {"fields": ("room", "condition")}),
        ("Стоимость и обслуживание", {"fields": (
            "price", "purchase_year", "service_interval", "next_service_year",
        )}),
        ("Примечание", {"fields": ("notes",)}),
    )
    actions = ("mark_for_service", "retire_devices")

    @admin.display(description="Доступно", boolean=True)
    def available(self, obj):
        return obj.is_available()

    @admin.action(description="Направить исправные на обслуживание",
                  permissions=["change"])
    def mark_for_service(self, request, queryset):
        state, _ = Condition.objects.get_or_create(
            code=Condition.Code.SERVICE,
            defaults={"name": Condition.Code.SERVICE.label},
        )
        count = queryset.working().update(condition=state)
        self.message_user(request, f"Направлено на обслуживание: {count}.",
                          messages.SUCCESS)

    @admin.action(description="Списать выбранные устройства",
                  permissions=["change"])
    def retire_devices(self, request, queryset):
        state, _ = Condition.objects.get_or_create(
            code=Condition.Code.RETIRED,
            defaults={"name": Condition.Code.RETIRED.label},
        )
        count = queryset.active().update(condition=state)
        self.message_user(request, f"Списано устройств: {count}.",
                          messages.SUCCESS)
