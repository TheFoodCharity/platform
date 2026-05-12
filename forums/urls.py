from django.urls import path

from . import views

app_name = "forums"

urlpatterns = [
    path("", views.forum_list, name="list"),
    path("applications/", views.forum_request_list, name="request_list"),
    path("applications/new/", views.forum_request_create, name="request_create"),
    path("applications/<uuid:request_id>/detail/", views.forum_request_detail, name="request_detail"),
    path("<uuid:space_id>/detail/", views.forum_detail, name="detail"),
    path("<uuid:space_id>/posts/new/", views.forum_post_create, name="post_create"),
]
