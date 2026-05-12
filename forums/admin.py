from django.contrib import admin

from .models import ForumSpaceRequest


@admin.register(ForumSpaceRequest)
class ForumSpaceRequestAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "topic_category", "requested_by_user", "requested_by_org", "created_at"]
    list_filter = ["status", "topic_category", "visibility_preference"]
    search_fields = ["title", "purpose", "region", "municipality"]
    readonly_fields = ["created_at", "updated_at", "reviewed_at"]
