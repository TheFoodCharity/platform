from django.contrib import admin

from .models import (
    CollaborationChatMessage,
    CollaborationLinkedObject,
    CollaborationSpace,
    CollaborationSpaceOrganizationMembership,
    CollaborationSpaceRequest,
    CollaborationSpaceUserMembership,
)


class CollaborationSpaceUserMembershipInline(admin.TabularInline):
    model = CollaborationSpaceUserMembership
    extra = 0


class CollaborationSpaceOrganizationMembershipInline(admin.TabularInline):
    model = CollaborationSpaceOrganizationMembership
    extra = 0


class CollaborationChatMessageInline(admin.TabularInline):
    model = CollaborationChatMessage
    extra = 0
    fields = ["author", "body", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(CollaborationSpaceRequest)
class CollaborationSpaceRequestAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "requested_by_user", "requested_by_org", "created_at", "reviewed_at"]
    list_filter = ["status", "topic_category", "visibility_preference"]
    search_fields = ["title", "purpose", "region", "municipality"]
    readonly_fields = ["created_at", "updated_at", "reviewed_at"]


@admin.register(CollaborationSpace)
class CollaborationSpaceAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "visibility_level", "owner", "moderator", "last_activity_at"]
    list_filter = ["status", "visibility_level", "topic_category"]
    search_fields = ["title", "purpose", "region", "municipality"]
    readonly_fields = ["created_at", "updated_at", "last_activity_at"]
    inlines = [
        CollaborationSpaceUserMembershipInline,
        CollaborationSpaceOrganizationMembershipInline,
        CollaborationChatMessageInline,
    ]


@admin.register(CollaborationLinkedObject)
class CollaborationLinkedObjectAdmin(admin.ModelAdmin):
    list_display = ["label", "space", "content_type", "object_id", "created_by", "created_at"]
    search_fields = ["label", "notes", "space__title"]


@admin.register(CollaborationChatMessage)
class CollaborationChatMessageAdmin(admin.ModelAdmin):
    list_display = ["space", "author", "created_at"]
    search_fields = ["body", "space__title", "author__email"]
