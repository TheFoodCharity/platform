from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpRequest

from .models import Membership, Organization, OrganizationApplication, OrganizationType, PermissionGroup

SESSION_KEY = "_organizations_current_id"

User = get_user_model()


@transaction.atomic()
def organization_create(*, owner: User, name: str, organization_type: OrganizationType) -> Organization:
    organization = Organization.objects.create(owner=owner, name=name, organization_type=organization_type)
    manager_role = PermissionGroup.objects.filter(name="Organization Manager", scope=PermissionGroup.Scope.USER).first()
    Membership.objects.create(user=owner, organization=organization, role=manager_role)
    OrganizationApplication.objects.create(organization=organization)
    return organization


def set_current_organization(request: HttpRequest, organization: Organization):
    if not request.user.is_authenticated:
        return
    if not (request.user.is_staff or organization.is_member(request.user)):
        return

    request.session[SESSION_KEY] = organization.pk
    request.session.cycle_key()


def get_current_organization(request: HttpRequest) -> Organization | None:
    if not request.user.is_authenticated:
        return None

    try:
        pk = request.session[SESSION_KEY]
        if request.user.is_staff:
            return Organization.active.get(pk=pk)
        return Organization.active.for_user(request.user).get(pk=pk)
    except KeyError, Organization.DoesNotExist:
        pass

    return None
