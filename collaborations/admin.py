from django.contrib import admin, messages
from django.db import transaction

from .models import (
    CollaborationChatMessage,
    CollaborationFile,
    CollaborationLinkedObject,
    CollaborationSpace,
    CollaborationSpaceOrganizationMembership,
    CollaborationSpaceRequest,
    CollaborationSpaceUserMembership,
)
from .tasks import scan_collaboration_file


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


class CollaborationFileInline(admin.TabularInline):
    model = CollaborationFile
    extra = 0
    fields = [
        "original_filename",
        "file",
        "content_type",
        "size",
        "scan_status",
        "scan_result",
        "scan_error",
        "scan_attempts",
        "scan_started_at",
        "scanned_at",
        "uploaded_by",
        "created_at",
    ]
    readonly_fields = [
        "original_filename",
        "content_type",
        "size",
        "scan_status",
        "scan_result",
        "scan_error",
        "scan_attempts",
        "scan_started_at",
        "scanned_at",
        "uploaded_by",
        "created_at",
    ]


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
        CollaborationFileInline,
    ]


@admin.register(CollaborationLinkedObject)
class CollaborationLinkedObjectAdmin(admin.ModelAdmin):
    list_display = ["label", "space", "content_type", "object_id", "created_by", "created_at"]
    search_fields = ["label", "notes", "space__title"]


@admin.register(CollaborationChatMessage)
class CollaborationChatMessageAdmin(admin.ModelAdmin):
    list_display = ["space", "author", "created_at"]
    search_fields = ["body", "space__title", "author__email"]


@admin.register(CollaborationFile)
class CollaborationFileAdmin(admin.ModelAdmin):
    list_display = [
        "original_filename",
        "space",
        "scan_status",
        "scan_result",
        "scan_attempts",
        "content_type",
        "size",
        "uploaded_by",
        "created_at",
        "scan_started_at",
        "scanned_at",
    ]
    list_filter = ["scan_status", "content_type", "created_at", "scan_started_at", "scanned_at"]
    search_fields = ["original_filename", "space__title", "uploaded_by__email"]
    readonly_fields = [
        "original_filename",
        "content_type",
        "size",
        "scan_status",
        "scan_result",
        "scan_error",
        "scan_attempts",
        "scan_started_at",
        "scanned_at",
        "uploaded_by",
        "created_at",
    ]
    actions = ["retry_scans"]

    @admin.action(description="Retry selected failed or infected scans")
    def retry_scans(self, request, queryset):
        retryable_statuses = [
            CollaborationFile.ScanStatus.FAILED,
            CollaborationFile.ScanStatus.INFECTED,
        ]
        retryable_files = queryset.filter(scan_status__in=retryable_statuses)
        skipped_status_count = queryset.count() - retryable_files.count()
        skipped_missing_count = 0
        queued_count = 0

        for collaboration_file in retryable_files:
            if not _collaboration_file_exists(collaboration_file):
                skipped_missing_count += 1
                continue

            collaboration_file.scan_status = CollaborationFile.ScanStatus.PENDING
            collaboration_file.scan_result = ""
            collaboration_file.scan_error = ""
            collaboration_file.scan_started_at = None
            collaboration_file.scanned_at = None
            collaboration_file.save(
                update_fields=[
                    "scan_status",
                    "scan_result",
                    "scan_error",
                    "scan_started_at",
                    "scanned_at",
                ]
            )
            transaction.on_commit(
                lambda collaboration_file_id=collaboration_file.id: scan_collaboration_file.delay(
                    str(collaboration_file_id)
                )
            )
            queued_count += 1

        if queued_count:
            self.message_user(request, f"Queued {queued_count} collaboration file scan(s).", messages.SUCCESS)
        if skipped_status_count:
            self.message_user(
                request,
                f"Skipped {skipped_status_count} file(s) because they were not failed or infected.",
                messages.WARNING,
            )
        if skipped_missing_count:
            self.message_user(
                request,
                f"Skipped {skipped_missing_count} file(s) because the uploaded file no longer exists in storage.",
                messages.WARNING,
            )


def _collaboration_file_exists(collaboration_file):
    name = collaboration_file.file.name
    if not name:
        return False

    return collaboration_file.file.storage.exists(name)
