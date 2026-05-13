from django.db import migrations

USER_ROLES = [
    ("Super Admin", "Full platform access for staff and superusers."),
    ("Food Charity Admin", "Platform administration and moderation."),
    ("Organization Manager", "Manage an organization's profile, members, and submissions."),
    ("Organization User", "Standard member access within an organization."),
]

ORGANIZATION_CAPABILITIES = [
    ("Food Donor", "Submit and manage food supply listings."),
    ("Food Receiver", "Express interest in food listings and confirm receipt."),
    ("Storage Provider", "Submit and maintain storage location records."),
    ("Collaboration Participant", "Participate in invited working groups and collaboration spaces."),
    ("Forum Participant", "Participate in member-only forum and discussion spaces."),
    ("Read-Only", "View-only access to permitted resources."),
]


def seed_permission_groups(apps, schema_editor):
    PermissionGroup = apps.get_model("organizations", "PermissionGroup")
    Membership = apps.get_model("organizations", "Membership")

    user_scope = 1
    org_scope = 2

    for name, description in USER_ROLES:
        PermissionGroup.objects.update_or_create(
            name=name,
            scope=user_scope,
            defaults={"description": description, "is_system": True},
        )

    for name, description in ORGANIZATION_CAPABILITIES:
        PermissionGroup.objects.update_or_create(
            name=name,
            scope=org_scope,
            defaults={"description": description, "is_system": True},
        )

    manager_role = PermissionGroup.objects.get(name="Organization Manager", scope=user_scope)
    user_role = PermissionGroup.objects.get(name="Organization User", scope=user_scope)

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
