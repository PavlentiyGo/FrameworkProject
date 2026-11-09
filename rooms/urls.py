from django.urls import path

from . import views


app_name = "rooms"

urlpatterns = [
    path("", views.room_list, name="room_list"),
    path("available/", views.available_rooms, name="available_rooms"),
    path("<int:room_id>/", views.room_detail, name="room_detail"),
]
