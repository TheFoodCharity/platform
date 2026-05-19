from django.db import migrations

from permissions import Scope, SystemCapability, SystemRole

PERMISSIONS = [
    (
        "storage.create_storage_location",
        "Create storage locations",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.STORAGE_PROVIDER],
    ),
    (
        "storage.edit_storage_location",
        "Edit storage locations",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.STORAGE_PROVIDER],
    ),
    (
        "storage.view_storage_location_detail",
        "View storage location details",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.STORAGE_PROVIDER, SystemCapability.READ_ONLY],
    ),
    (
        "storage.view_storage_locations",
        "View storage locations",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.STORAGE_PROVIDER, SystemCapability.READ_ONLY],
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
        ("permissions", "0006_permission_view_all_donations"),
    ]

    operations = [
        migrations.RunPython(add_permissions, reverse_code=remove_permissions),
    ]
