from django.db import migrations

from organizations.constants import Scope, SystemRole

PERMISSIONS = [
    ("organizations.view_application", "View the organization application dashboard and section forms"),
    ("organizations.edit_application", "Edit organization application sections"),
    ("organizations.submit_application", "Submit or resubmit the organization application"),
    ("organizations.manage_profile", "Edit the organization profile"),
    ("organizations.manage_members", "Invite users and manage organization memberships"),
]


def add_permissions(apps, schema_editor):
    Permission = apps.get_model("organizations", "Permission")
    PermissionGroup = apps.get_model("organizations", "PermissionGroup")

    for code, description in PERMISSIONS:
        Permission.objects.update_or_create(code=code, defaults={"description": description})

    role_assignments = {
        SystemRole.ORGANIZATION_MANAGER: [
            "organizations.view_application",
            "organizations.edit_application",
            "organizations.submit_application",
            "organizations.manage_profile",
            "organizations.manage_members",
        ],
        SystemRole.ORGANIZATION_USER: ["organizations.view_application"],
    }
    for role_name, codes in role_assignments.items():
        group = PermissionGroup.objects.get(name=role_name, scope=Scope.USER)
        group.permissions.add(*Permission.objects.filter(code__in=codes))


def remove_permissions(apps, schema_editor):
    Permission = apps.get_model("organizations", "Permission")
    Permission.objects.filter(
        code__in=[
            "organizations.view_application",
            "organizations.edit_application",
            "organizations.submit_application",
            "organizations.manage_profile",
            "organizations.manage_members",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0007_remove_membership_is_admin"),
    ]

    operations = [
        migrations.RunPython(add_permissions, reverse_code=remove_permissions),
    ]
