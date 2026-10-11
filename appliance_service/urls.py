"""Маршрутизация верхнего уровня."""

from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("devices/", include("equipment.urls")),
    path("rooms/", include("rooms.urls")),
    path("", include("homepage.urls")),
]

handler404 = "homepage.views.page_not_found"
