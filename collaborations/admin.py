from django.contrib import admin, messages

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
    actions = ["approve_requests", "reject_requests"]

    @admin.action(description="Approve selected pending requests and create spaces")
    def approve_requests(self, request, queryset):
        pending_requests = queryset.filter(status=CollaborationSpaceRequest.Status.PENDING)
        approved_count = 0

        for collaboration_request in pending_requests:
            collaboration_request.approve(request.user, "Approved from Django admin action.")
            approved_count += 1

        skipped_count = queryset.count() - approved_count
        if approved_count:
            self.message_user(
                request,
                f"Approved {approved_count} collaboration request(s) and created matching space(s).",
                messages.SUCCESS,
            )
        if skipped_count:
            self.message_user(
                request,
                f"Skipped {skipped_count} request(s) because they were not pending.",
                messages.WARNING,
            )

    @admin.action(description="Reject selected pending requests")
    def reject_requests(self, request, queryset):
        pending_requests = queryset.filter(status=CollaborationSpaceRequest.Status.PENDING)
        rejected_count = 0

        for collaboration_request in pending_requests:
            collaboration_request.decline(request.user, "Rejected from Django admin action.")
            rejected_count += 1

        skipped_count = queryset.count() - rejected_count
        if rejected_count:
            self.message_user(
                request,
                f"Rejected {rejected_count} collaboration request(s).",
                messages.SUCCESS,
            )
        if skipped_count:
            self.message_user(
                request,
                f"Skipped {skipped_count} request(s) because they were not pending.",
                messages.WARNING,
            )


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
