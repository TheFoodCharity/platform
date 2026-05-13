from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("demo-interest/", views.demo_interest, name="demo_interest"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
