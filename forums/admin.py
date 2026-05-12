from django.contrib import admin, messages

from .models import (
    ForumPost,
    ForumSpace,
    ForumSpaceOrganizationMembership,
    ForumSpaceRequest,
    ForumSpaceUserMembership,
)


class ForumSpaceUserMembershipInline(admin.TabularInline):
    model = ForumSpaceUserMembership
    extra = 0


class ForumSpaceOrganizationMembershipInline(admin.TabularInline):
    model = ForumSpaceOrganizationMembership
    extra = 0


class ForumPostInline(admin.TabularInline):
    model = ForumPost
    extra = 0
    readonly_fields = ["created_at", "updated_at", "moderated_at"]


@admin.register(ForumSpaceRequest)
class ForumSpaceRequestAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "topic_category", "requested_by_user", "requested_by_org", "created_at"]
    list_filter = ["status", "topic_category", "visibility_preference"]
    search_fields = ["title", "purpose", "region", "municipality"]
    readonly_fields = ["created_at", "updated_at", "reviewed_at"]
    actions = ["approve_requests", "reject_requests"]

    @admin.action(description="Approve selected pending requests and create forums")
    def approve_requests(self, request, queryset):
        pending_requests = queryset.filter(status=ForumSpaceRequest.Status.PENDING)
        approved_count = 0

        for forum_request in pending_requests:
            forum_request.approve(request.user, "Approved from Django admin action.")
            approved_count += 1

        skipped_count = queryset.count() - approved_count
        if approved_count:
            self.message_user(
                request,
                f"Approved {approved_count} forum request(s) and created matching forum(s).",
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
        pending_requests = queryset.filter(status=ForumSpaceRequest.Status.PENDING)
        rejected_count = 0

        for forum_request in pending_requests:
            forum_request.decline(request.user, "Rejected from Django admin action.")
            rejected_count += 1

        skipped_count = queryset.count() - rejected_count
        if rejected_count:
            self.message_user(request, f"Rejected {rejected_count} forum request(s).", messages.SUCCESS)
        if skipped_count:
            self.message_user(
                request,
                f"Skipped {skipped_count} request(s) because they were not pending.",
                messages.WARNING,
            )


@admin.register(ForumSpace)
class ForumSpaceAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "visibility_level", "topic_category", "owner", "moderator", "last_activity_at"]
    list_filter = ["status", "visibility_level", "topic_category"]
    search_fields = ["title", "description", "region", "municipality"]
    readonly_fields = ["created_at", "updated_at", "last_activity_at"]
    inlines = [
        ForumPostInline,
        ForumSpaceUserMembershipInline,
        ForumSpaceOrganizationMembershipInline,
    ]


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ["space", "author", "created_at", "is_removed"]
    list_filter = ["is_removed", "created_at"]
    search_fields = ["body", "author__first_name", "author__last_name", "author__email", "space__title"]
    readonly_fields = ["created_at", "updated_at", "moderated_at"]
