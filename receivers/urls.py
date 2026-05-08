from django.urls import path

from . import views

app_name = "receivers"

urlpatterns = [
    path("donations/", views.receiver_donation_list, name="donation_list"),
    path("donations/<int:pk>/", views.receiver_donation_detail, name="donation_detail"),
    path("donations/<int:pk>/request/", views.food_request_create, name="request_create"),
    path("requests/<int:pk>/thanks/", views.food_request_thanks, name="request_thanks"),
]
