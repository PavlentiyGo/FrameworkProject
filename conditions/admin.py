from django.contrib import admin

from conditions.models import Condition


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code")
    list_display_links = ("id", "name")
    search_fields = ("name", "code")
    list_filter = ("code",)
    ordering = ("pk",)
    readonly_fields = ("name",)
    list_per_page = 10
