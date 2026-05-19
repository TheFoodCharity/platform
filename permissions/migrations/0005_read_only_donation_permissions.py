from django.db import migrations

from permissions import Scope, SystemCapability

READ_ONLY_PERMISSIONS = [
    "donations.view_all_donations",
    "donations.view_available_donations",
    "donations.view_donation_detail",
    "donations.view_donations",
    "donations.view_food_request",
]


def add_read_only_permissions(apps, schema_editor):
    Permission = apps.get_model("permissions", "Permission")
    PermissionGroup = apps.get_model("permissions", "PermissionGroup")

    read_only = PermissionGroup.objects.get(name=SystemCapability.READ_ONLY, scope=Scope.ORGANIZATION)
    read_only.permissions.add(*Permission.objects.filter(code__in=READ_ONLY_PERMISSIONS))


def remove_read_only_permissions(apps, schema_editor):
    Permission = apps.get_model("permissions", "Permission")
    PermissionGroup = apps.get_model("permissions", "PermissionGroup")

    read_only = PermissionGroup.objects.get(name=SystemCapability.READ_ONLY, scope=Scope.ORGANIZATION)
    read_only.permissions.remove(*Permission.objects.filter(code__in=READ_ONLY_PERMISSIONS))


class Migration(migrations.Migration):
    dependencies = [
        ("permissions", "0004_permissions_donations"),
    ]

    operations = [
        migrations.RunPython(add_read_only_permissions, reverse_code=remove_read_only_permissions),
    ]
