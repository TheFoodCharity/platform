from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("food-help-map/", views.food_help_map, name="food_help_map"),
    path("demo-interest/", views.demo_interest, name="demo_interest"),
]
