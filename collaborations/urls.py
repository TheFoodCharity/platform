from django.urls import path

from . import views

app_name = "collaborations"

urlpatterns = [
    path("", views.collaboration_list, name="list"),
    path("applications/", views.collaboration_request_list, name="request_list"),
    path("applications/new/", views.collaboration_request_create, name="request_create"),
    path("applications/<uuid:request_id>/detail/", views.collaboration_request_detail, name="request_detail"),
    path("<uuid:space_id>/detail/", views.collaboration_detail, name="detail"),
    path("<uuid:space_id>/overview/", views.collaboration_detail_overview, name="detail_overview"),
    path("<uuid:space_id>/members/", views.collaboration_detail_members, name="detail_members"),
    path("<uuid:space_id>/chat/", views.collaboration_detail_chat, name="detail_chat"),
    path("<uuid:space_id>/links/", views.collaboration_detail_links, name="detail_links"),
    path("<uuid:space_id>/admin/", views.collaboration_detail_admin, name="detail_admin"),
    path("<uuid:space_id>/chat/messages/new/", views.collaboration_chat_message_create, name="chat_message_create"),
]
