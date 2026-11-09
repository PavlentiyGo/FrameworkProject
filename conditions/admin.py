from django.contrib import admin

from conditions.models import Condition


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
