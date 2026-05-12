from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "forums"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="forums:request_list", permanent=False)),
    path("applications/", views.forum_request_list, name="request_list"),
    path("applications/new/", views.forum_request_create, name="request_create"),
    path("applications/<uuid:request_id>/detail/", views.forum_request_detail, name="request_detail"),
]
