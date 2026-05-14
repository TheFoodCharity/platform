from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple

from permissions.constants import Scope
from permissions.models import MembershipPermissionOverride, OrganizationPermissionOverride, PermissionGroup

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


class OrganizationAdminForm(forms.ModelForm):
    capabilities = forms.ModelMultipleChoiceField(
        queryset=PermissionGroup.objects.filter(scope=Scope.ORGANIZATION),
        required=False,
        widget=FilteredSelectMultiple("capabilities", is_stacked=False),
    )

    class Meta:
        model = Organization
        fields = [
            "name",
            "status",
            "is_active",
            "owner",
            "organization_type",
            "legal_status",
            "description",
            "interest_areas",
            "municipality",
            "region",
            "service_area",
            "email",
            "phone",
            "website",
            "contact_via_email",
            "contact_via_phone",
            "is_publicly_visible",
            "internal_notes",
            "capabilities",
        ]


class OrganizationPermissionOverrideInline(admin.TabularInline):
    model = OrganizationPermissionOverride
    extra = 0
    autocomplete_fields = ["permission"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("permission")


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    form = OrganizationAdminForm
    list_display = ["name", "owner", "status", "is_active"]
    list_filter = ["status", "is_active"]
    search_fields = ["name"]
    raw_id_fields = ("owner",)
    inlines = [OrganizationApplicationInline, OrganizationPermissionOverrideInline]
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
            {"fields": ["address_line_1", "address_line_2", "municipality", "region", "postal_code", "service_area"]},
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
            "Capabilities",
            {
                "description": "The capabilities this organization has been granted. "
                "These determine which permissions its members can be given.",
                "fields": ["capabilities"],
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


class MembershipAdminForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ["user", "organization", "role"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = PermissionGroup.objects.filter(scope=Scope.USER)


class MembershipPermissionOverrideInline(admin.TabularInline):
    model = MembershipPermissionOverride
    extra = 0
    autocomplete_fields = ["permission"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("permission")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    form = MembershipAdminForm
    list_display = ["user", "organization", "role"]
    list_filter = ["role"]
    raw_id_fields = ("user", "organization")
    inlines = [MembershipPermissionOverrideInline]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("invitee_identifier", "invited_by", "created")
    readonly_fields = ("guid", "created")
