from typing import Any

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group as AuthGroup  # noqa: TID251
from django.http.request import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from organizations.base_admin import BaseOrganizationAdmin, BaseOrganizationUserAdmin, BaseOwnerInline

from .models import Group, Invitation, Membership, Organization, OrganizationOwner, User


def _redirect_admin_login(request: HttpRequest, extra_context: dict[str, Any] | None = None):
    next_url = request.GET.get("next", reverse("admin:index"))
    return redirect(f"{reverse('accounts:login')}?next={next_url}")


# Rebind authentication to use our implementation
admin.site.login = _redirect_admin_login

admin.site.unregister(AuthGroup)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )
    list_display = ("email", "first_name", "last_name", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    pass


class OrganizationOwnerInline(BaseOwnerInline):
    model = OrganizationOwner


@admin.register(Organization)
class OrganizationAdmin(BaseOrganizationAdmin):
    list_filter = ["status", "is_active"]
    list_display = ["name", "status", "is_active"]
    inlines = [OrganizationOwnerInline]


@admin.register(Membership)
class MembershipAdmin(BaseOrganizationUserAdmin):
    pass


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("invitee_identifier", "invited_by", "created")
    readonly_fields = ("guid", "created")
