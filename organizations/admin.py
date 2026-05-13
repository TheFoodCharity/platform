from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple

from .models import (
    Invitation,
    LegalStatus,
    Membership,
    MembershipPermissionOverride,
    Organization,
    OrganizationApplication,
    OrganizationPermissionOverride,
    OrganizationType,
    Permission,
    PermissionGroup,
)


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


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["code", "description"]
    search_fields = ["code", "description"]
    ordering = ["code"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class PermissionGroupAdminForm(forms.ModelForm):
    class Meta:
        model = PermissionGroup
        fields = ["name", "scope", "description", "permissions", "is_system"]
        widgets = {
            "permissions": FilteredSelectMultiple("permissions", is_stacked=False),
        }


@admin.register(PermissionGroup)
class PermissionGroupAdmin(admin.ModelAdmin):
    form = PermissionGroupAdminForm
    list_display = ["name", "scope", "is_system"]
    list_filter = ["scope", "is_system"]
    search_fields = ["name"]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_system:
            return ["name", "scope", "is_system"]
        return ["is_system"]

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)


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


class CapabilitiesWidget(FilteredSelectMultiple):
    pass


class OrganizationAdminForm(forms.ModelForm):
    capabilities = forms.ModelMultipleChoiceField(
        queryset=PermissionGroup.objects.filter(scope=PermissionGroup.Scope.ORGANIZATION),
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
        self.fields["role"].queryset = PermissionGroup.objects.filter(scope=PermissionGroup.Scope.USER)


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


@admin.register(OrganizationPermissionOverride)
class OrganizationPermissionOverrideAdmin(admin.ModelAdmin):
    list_display = ["organization", "permission", "effect"]
    list_filter = ["effect"]
    search_fields = ["organization__name", "permission__code"]
    raw_id_fields = ("organization",)
    autocomplete_fields = ["permission"]


@admin.register(MembershipPermissionOverride)
class MembershipPermissionOverrideAdmin(admin.ModelAdmin):
    list_display = ["membership", "permission", "effect"]
    list_filter = ["effect"]
    search_fields = ["membership__organization__name", "permission__code"]
    autocomplete_fields = ["permission"]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("invitee_identifier", "invited_by", "created")
    readonly_fields = ("guid", "created")
