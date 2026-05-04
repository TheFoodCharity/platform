from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group as AuthGroup

from .models import Group, User

admin.site.unregister(AuthGroup)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    pass
