from django.db import migrations

from permissions.constants import Scope, SystemCapability, SystemRole

PERMISSIONS = [
    (
        "organizations.edit_application",
        "Edit organization application sections",
        [SystemRole.ORGANIZATION_MANAGER],
        [SystemCapability.DEFAULT],
    ),
    (
        "organizations.edit_member_permissions",
        "Modify the permissions of organization members",
        [SystemRole.ORGANIZATION_MANAGER],
        [SystemCapability.DEFAULT],
    ),
    (
        "organizations.edit_profile",
        "Edit the organization profile",
        [SystemRole.ORGANIZATION_MANAGER],
        [SystemCapability.DEFAULT],
    ),
    (
        "organizations.invite_member",
        "Invite a new member to the organization",
        [SystemRole.ORGANIZATION_MANAGER],
        [SystemCapability.DEFAULT],
    ),
    (
        "organizations.remove_member",
        "Remove a member from the organization",
        [SystemRole.ORGANIZATION_MANAGER],
        [SystemCapability.DEFAULT],
    ),
    (
        "organizations.submit_application",
        "Submit or resubmit the organization application",
        [SystemRole.ORGANIZATION_MANAGER],
        [SystemCapability.DEFAULT],
    ),
    (
        "organizations.transfer_ownership",
        "Transfer ownership of the organization to another member",
        [],
        [SystemCapability.DEFAULT],
    ),
    (
        "organizations.view_application",
        "View the organization application dashboard and section forms",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.DEFAULT],
    ),
    (
        "organizations.view_members",
        "View organization members",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.DEFAULT],
    ),
    (
        "organizations.view_profile",
        "View the organization profile",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.DEFAULT],
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
        ("permissions", "0002_seed_groups"),
    ]

    operations = [
        migrations.RunPython(add_permissions, reverse_code=remove_permissions),
    ]
