from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple

from .models import MembershipPermissionOverride, OrganizationPermissionOverride, Permission, PermissionGroup


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
