from django.db import migrations

from organizations.constants import Scope, SystemCapability, SystemRole

USER_ROLES = [
    (SystemRole.FOOD_CHARITY_ADMIN, "Platform administration and moderation."),
    (SystemRole.ORGANIZATION_MANAGER, "Manage an organization's profile, members, and submissions."),
    (SystemRole.ORGANIZATION_USER, "Standard member access within an organization."),
]

ORGANIZATION_CAPABILITIES = [
    (SystemCapability.FOOD_DONOR, "Submit and manage food supply listings."),
    (SystemCapability.FOOD_RECEIVER, "Express interest in food listings and confirm receipt."),
    (SystemCapability.STORAGE_PROVIDER, "Submit and maintain storage location records."),
    (SystemCapability.COLLABORATION_PARTICIPANT, "Participate in invited working groups and collaboration spaces."),
    (SystemCapability.FORUM_PARTICIPANT, "Participate in member-only forum and discussion spaces."),
    (SystemCapability.READ_ONLY, "View-only access to permitted resources."),
]


def seed_permission_groups(apps, schema_editor):
    PermissionGroup = apps.get_model("organizations", "PermissionGroup")
    Membership = apps.get_model("organizations", "Membership")

    for name, description in USER_ROLES:
        PermissionGroup.objects.update_or_create(
            name=name,
            scope=Scope.USER.value,
            defaults={"description": description, "is_system": True},
        )

    for name, description in ORGANIZATION_CAPABILITIES:
        PermissionGroup.objects.update_or_create(
            name=name,
            scope=Scope.ORGANIZATION.value,
            defaults={"description": description, "is_system": True},
        )

    manager_role = PermissionGroup.objects.get(name="Organization Manager", scope=Scope.USER.value)
    user_role = PermissionGroup.objects.get(name="Organization User", scope=Scope.USER.value)

    Membership.objects.filter(is_admin=True, role__isnull=True).update(role=manager_role)
    Membership.objects.filter(is_admin=False, role__isnull=True).update(role=user_role)


def unseed_permission_groups(apps, schema_editor):
    PermissionGroup = apps.get_model("organizations", "PermissionGroup")
    all_names = [name for name, _ in USER_ROLES + ORGANIZATION_CAPABILITIES]
    PermissionGroup.objects.filter(name__in=all_names, is_system=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0005_permissions_framework"),
    ]

    operations = [
        migrations.RunPython(seed_permission_groups, reverse_code=unseed_permission_groups),
    ]
