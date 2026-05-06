from django.contrib import admin

from .models import Invitation, LegalStatus, Membership, Organization, OrganizationApplication, OrganizationType


@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


@admin.register(LegalStatus)
class LegalStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


class OrganizationApplicationInline(admin.StackedInline):
    model = OrganizationApplication
    extra = 0
    readonly_fields = ["submitted_at", "acknowledged_at", "acknowledged_by", "reviewed_at"]
    fieldsets = [
        ("Submission", {"fields": ["submitted_at"]}),
        (
            "Review notice acknowledgement",
            {"fields": ["acknowledged_at", "acknowledged_by"]},
        ),
        (
            "Admin review",
            {"fields": ["admin_notes", "reviewed_at", "reviewed_by"]},
        ),
    ]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "status", "is_active"]
    list_filter = ["status", "is_active"]
    search_fields = ["name"]
    raw_id_fields = ("owner",)
    inlines = [OrganizationApplicationInline]
    fieldsets = [
        (
            "Identity",
            {
                "fields": [
                    "name",
                    "status",
                    "is_active",
                    "owner",
                    "organization_type",
                    "legal_status",
                    "description",
                    "interest_areas",
                ],
            },
        ),
        (
            "Location",
            {"fields": ["municipality", "region", "service_area"]},
        ),
        (
            "Public contact",
            {
                "description": "Contact details shown publicly for organizations that provide direct public support.",
                "fields": ["email", "phone", "website"],
            },
        ),
        (
            "Operational profile",
            {
                "fields": [
                    "contact_via_email",
                    "contact_via_phone",
                    "is_publicly_visible",
                ],
            },
        ),
        (
            "Internal / admin",
            {
                "classes": ["collapse"],
                "fields": ["internal_notes"],
            },
        ),
    ]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "organization", "is_admin"]
    raw_id_fields = ("user", "organization")


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("invitee_identifier", "invited_by", "created")
    readonly_fields = ("guid", "created")
