from django.urls import path

from . import views

app_name = "donations"

urlpatterns = [
    path("", views.donation_list, name="list"),
    path("add/", views.donation_create, name="create"),
    path("available/", views.available_donation_list, name="available_list"),
    path("available/<int:pk>/", views.available_donation_detail, name="available_detail"),
    path("<int:pk>/thanks/", views.donation_thanks, name="donation_thanks"),
    path("<int:pk>/", views.donation_detail, name="detail"),
    path("<int:pk>/edit/", views.donation_edit, name="edit"),
    path("<int:pk>/request/", views.food_request_create, name="request_create"),
    path("requests/<int:pk>/", views.food_request_detail, name="request_detail"),
    path("requests/<int:pk>/thanks/", views.food_request_thanks, name="request_thanks"),
]
