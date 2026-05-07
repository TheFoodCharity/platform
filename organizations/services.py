from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Membership, Organization, OrganizationApplication, OrganizationType

User = get_user_model()


@transaction.atomic()
def organization_create(*, owner: User, name: str, organization_type: OrganizationType) -> Organization:
    organization = Organization.objects.create(owner=owner, name=name, organization_type=organization_type)
    Membership.objects.create(user=owner, organization=organization, is_admin=True)
    OrganizationApplication.objects.create(organization=organization)
    return organization
