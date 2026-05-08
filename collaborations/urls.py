from django.urls import path

from . import views

app_name = "collaborations"

urlpatterns = [
    path("", views.collaboration_list, name="list"),
    path("request/new/", views.collaboration_request_create, name="request_create"),
    path("requests/<uuid:request_id>/detail/", views.collaboration_request_detail, name="request_detail"),
    path("<uuid:space_id>/detail/", views.collaboration_detail, name="detail"),
    path("<uuid:space_id>/chat/messages/new/", views.collaboration_chat_message_create, name="chat_message_create"),
]
