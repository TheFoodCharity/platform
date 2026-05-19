from django.db import migrations

from permissions import Scope, SystemCapability, SystemRole

# Keep this list aligned with donations/rules.py so DB permissions match runtime registrations.
PERMISSIONS = [
    (
        "donations.create_donation",
        "Create food donation tickets",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.FOOD_DONOR],
    ),
    (
        "donations.edit_donation",
        "Edit donation tickets owned by the current organization",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.FOOD_DONOR],
    ),
    (
        "donations.request_donation",
        "Submit food requests for available donations",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.FOOD_RECEIVER],
    ),
    (
        "donations.view_available_donations",
        "View available donation tickets for requesting food",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.FOOD_RECEIVER, SystemCapability.READ_ONLY],
    ),
    (
        "donations.view_donation_detail",
        "View donation ticket details owned by the current organization",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.FOOD_DONOR, SystemCapability.READ_ONLY],
    ),
    (
        "donations.view_donations",
        "View donation tickets for the current organization",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.FOOD_DONOR, SystemCapability.READ_ONLY],
    ),
    (
        "donations.view_food_request",
        "View food request details connected to the current organization",
        [SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
        [SystemCapability.FOOD_DONOR, SystemCapability.FOOD_RECEIVER, SystemCapability.READ_ONLY],
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
        ("permissions", "0003_permissions_organizations"),
    ]

    operations = [
        migrations.RunPython(add_permissions, reverse_code=remove_permissions),
    ]
