from django.db import migrations

ORGANIZATION_TYPES = [
    "Food bank",
    "Food hub",
    "Community food program",
    "Farmer",
    "Grower",
    "Supermarket",
    "Grocery store",
    "Food distributor",
    "Warehouse",
    "Cold storage provider",
    "Transportation partner",
    "Municipal government",
    "Provincial agency",
    "First Nations government",
    "Indigenous organization",
    "Indigenous-led food program",
    "School",
    "University",
    "Church / faith-based organization",
    "Service club",
    "Foundation",
    "Funder",
    "Volunteer group",
    "Community association",
    "Registered charity",
    "Nonprofit / not-for-profit",
    "NGO",
    "Social enterprise",
    "Private business",
    "Research partner",
    "Public health organization",
    "Emergency preparedness organization",
    "Other",
]

LEGAL_STATUSES = [
    "Community group",
    "Educational institution",
    "Faith-based organization",
    "Foundation / funder",
    "Indigenous organization",
    "Municipality",
    "NGO",
    "Not sure",
    "Other",
    "Private business",
    "Public body / government",
    "Registered charity",
    "Registered nonprofit / not-for-profit",
    "Social enterprise",
]


def seed_lookups(apps, schema_editor):
    OrganizationType = apps.get_model("organizations", "OrganizationType")
    LegalStatus = apps.get_model("organizations", "LegalStatus")
    OrganizationType.objects.bulk_create(
        [OrganizationType(name=name) for name in ORGANIZATION_TYPES], ignore_conflicts=True
    )
    LegalStatus.objects.bulk_create([LegalStatus(name=name) for name in LEGAL_STATUSES], ignore_conflicts=True)


def unseed_lookups(apps, schema_editor):
    OrganizationType = apps.get_model("organizations", "OrganizationType")
    LegalStatus = apps.get_model("organizations", "LegalStatus")
    OrganizationType.objects.filter(name__in=ORGANIZATION_TYPES).delete()
    LegalStatus.objects.filter(name__in=LEGAL_STATUSES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0002_application"),
    ]

    operations = [
        migrations.RunPython(seed_lookups, reverse_code=unseed_lookups),
    ]
