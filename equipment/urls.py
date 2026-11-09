from django.urls import path

from . import views


app_name = "equipment"

urlpatterns = [
    path("", views.device_list, name="device_list"),
    path("search/", views.device_search, name="device_search"),
    path("statistics/", views.statistics, name="statistics"),
    path("<int:device_id>/", views.device_detail, name="device_detail"),
]
