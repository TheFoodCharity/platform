from django.db import migrations

from permissions import Scope, SystemCapability, SystemRole

PERMISSIONS = [
    (
        "donations.view_all_donations",
        "View donation tickets across all organizations",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.READ_ONLY],
    ),
]


def add_permissions(apps, schema_editor):
    Permission = apps.get_model("permissions", "Permission")
    PermissionGroup = apps.get_model("permissions", "PermissionGroup")
    for code, description, roles, capabilities in PERMISSIONS:
        perm, _ = Permission.objects.update_or_create(code=code, defaults={"description": description})
        for role in roles:
            PermissionGroup.objects.get(name=role, scope=Scope.USER).permissions.add(perm)
        for cap in capabilities:
            PermissionGroup.objects.get(name=cap, scope=Scope.ORGANIZATION).permissions.add(perm)


def remove_permissions(apps, schema_editor):
    Permission = apps.get_model("permissions", "Permission")
    Permission.objects.filter(code__in=[code for code, *_ in PERMISSIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("permissions", "0005_read_only_donation_permissions"),
    ]

    operations = [
        migrations.RunPython(add_permissions, reverse_code=remove_permissions),
    ]
