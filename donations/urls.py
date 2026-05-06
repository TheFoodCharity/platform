from django.urls import path

from . import views

app_name = "donations"

urlpatterns = [
    path("", views.donation_ticket_list, name="list"),
    path("add/", views.donation_ticket_create, name="create"),
    path("<int:pk>/", views.donation_ticket_detail, name="detail"),
    path("<int:pk>/edit/", views.donation_ticket_edit, name="edit"),
    path(
        "<int:pk>/assign-storage/<int:storage_pk>/",
        views.donation_ticket_assign_storage,
        name="assign_storage",
    ),
]
