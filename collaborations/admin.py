from django.contrib import admin

from .models import (
    CollaborationSpaceRequest,
)


@admin.register(CollaborationSpaceRequest)
class CollaborationSpaceRequestAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "requested_by_user", "requested_by_org", "created_at", "reviewed_at"]
    list_filter = ["status", "topic_category", "visibility_preference"]
    search_fields = ["title", "purpose", "region", "municipality"]
    readonly_fields = ["created_at", "updated_at", "reviewed_at"]
