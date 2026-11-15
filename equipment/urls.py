from django.urls import path

from . import views


app_name = "equipment"

urlpatterns = [
    path("", views.device_list, name="device_list"),
    path("search/", views.device_search, name="device_search"),
    path("statistics/", views.statistics, name="statistics"),
    path("create/", views.device_create, name="device_create"),
    path("<int:device_id>/edit/", views.device_edit, name="device_edit"),
    path("<int:device_id>/retire/", views.device_retire, name="device_retire"),
    path("<int:device_id>/", views.device_detail, name="device_detail"),
]
