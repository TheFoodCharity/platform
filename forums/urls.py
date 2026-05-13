from django.urls import path

from . import views

app_name = "forums"

urlpatterns = [
    path("", views.forum_list, name="list"),
    path("applications/", views.forum_request_list, name="request_list"),
    path("applications/new/", views.forum_request_create, name="request_create"),
    path("applications/<uuid:request_id>/detail/", views.forum_request_detail, name="request_detail"),
    path("<uuid:space_id>/posts/", views.forum_detail_posts, name="detail_posts"),
    path("<uuid:space_id>/members/", views.forum_detail_members, name="detail_members"),
    path("<uuid:space_id>/admin/", views.forum_detail_admin, name="detail_admin"),
    path("<uuid:space_id>/posts/new/", views.forum_post_create, name="post_create"),
]
