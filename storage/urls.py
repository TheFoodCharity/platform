from django.urls import path

from . import views

app_name = "storage"

urlpatterns = [
    path("", views.storage_list, name="list"),
    path("add/", views.storage_create, name="create"),
    path("<int:pk>/edit/", views.storage_edit, name="edit"),
]
