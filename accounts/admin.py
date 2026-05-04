from typing import Any

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group as AuthGroup  # noqa: TID251
from django.http.request import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse

from .models import Group, User


def _redirect_admin_login(request: HttpRequest, extra_context: dict[str, Any] | None = None):
    next_url = request.GET.get("next", reverse("admin:index"))
    return redirect(f"{reverse('accounts:login')}?next={next_url}")


# Rebind authentication to use our implementation
admin.site.login = _redirect_admin_login

admin.site.unregister(AuthGroup)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    pass
