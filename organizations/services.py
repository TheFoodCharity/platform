from contextlib import contextmanager
from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from django.http import HttpRequest

from permissions import Scope, SystemCapability, SystemRole
from permissions.models import MembershipPermissionOverride, Permission, PermissionGroup

from .models import AnonymousOrganization, Membership, Organization, OrganizationApplication, OrganizationType

SESSION_KEY = "_organizations_current_id"

User = get_user_model()


@transaction.atomic()
def organization_create(*, owner: User, name: str, organization_type: OrganizationType) -> Organization:
    manager_role = PermissionGroup.objects.get(name=SystemRole.ORGANIZATION_MANAGER, scope=Scope.USER)
    default_capability = PermissionGroup.objects.get(name=SystemCapability.DEFAULT, scope=Scope.ORGANIZATION)

    organization = Organization.objects.create(owner=owner, name=name, organization_type=organization_type)
    organization.capabilities.add(default_capability)

    Membership.objects.create(user=owner, organization=organization, role=manager_role)
    OrganizationApplication.objects.create(organization=organization)
    return organization


@transaction.atomic()
def update_member_permissions(
    *,
    membership: Membership,
    role: PermissionGroup | None,
    actions: Iterable[tuple[str, str, int | None]],
) -> None:
    actions = list(actions)

    membership.role = role
    membership.permission_version = F("permission_version") + 1
    membership.save(update_fields=["role", "permission_version", "modified"])

    codes = [code for _action, code, _effect in actions]
    permissions_by_code = {p.code: p for p in Permission.objects.filter(code__in=codes)}

    remove_codes = [c for a, c, _ in actions if a == "remove"]
    if remove_codes:
        MembershipPermissionOverride.objects.filter(membership=membership, permission__code__in=remove_codes).delete()

    for action, code, effect in actions:
        if action == "remove":
            continue
        permission = permissions_by_code.get(code)
        if permission is None:
            continue
        MembershipPermissionOverride.objects.update_or_create(
            membership=membership,
            permission=permission,
            defaults={"effect": effect},
        )


def set_current_organization(request: HttpRequest, organization: Organization):
    if not request.user.is_authenticated:
        return
    if not (request.user.is_staff or organization.is_member(request.user)):
        return

    request.session[SESSION_KEY] = organization.pk
    request.session.cycle_key()


def get_current_organization(request: HttpRequest) -> Organization | AnonymousOrganization:
    if not request.user.is_authenticated:
        return AnonymousOrganization()

    try:
        pk = request.session[SESSION_KEY]
        if request.user.is_staff:
            return Organization.objects.get(pk=pk)
        return Organization.objects.for_user(request.user).get(pk=pk)
    except KeyError, Organization.DoesNotExist:
        pass

    return AnonymousOrganization()


@contextmanager
def acting_as(user: User, organization: Organization):
    """Pin the acting organization on ``user`` for the duration of the block.

    Restores the previous value on exit, including on exception and when nested.
    Handles the case where ``current_organization`` was not set beforehand.

    Use this in signals, management commands, and Celery tasks that need to perform
    a permission check outside of a request. Routes through the same predicates as views.
    """
    sentinel = object()
    previous = getattr(user, "current_organization", sentinel)
    user.current_organization = organization
    try:
        yield
    finally:
        if previous is sentinel:
            try:
                del user.current_organization
            except AttributeError:
                pass
        else:
            user.current_organization = previous
