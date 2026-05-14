import rules

from .constants import Scope
from .models import (
    AnonymousOrganization,
    Membership,
    MembershipPermissionOverride,
    Organization,
    OrganizationPermissionOverride,
    Permission,
)


def _current_organization(user) -> Organization | AnonymousOrganization:
    return getattr(user, "current_organization", AnonymousOrganization())


def _organization_in_state(*states):
    @rules.predicate
    def predicate(user, obj=None):
        organization = _current_organization(user)
        return not organization.is_anonymous and organization.is_active and organization.status in states

    return predicate


organization_is_active = _organization_in_state(
    Organization.Status.APPROVED,
    Organization.Status.APPROVED_LIMITED,
)

organization_in_application = _organization_in_state(
    Organization.Status.DRAFT,
    Organization.Status.PENDING,
    Organization.Status.NEEDS_INFO,
)

organization_is_readable = _organization_in_state(
    Organization.Status.APPROVED,
    Organization.Status.APPROVED_LIMITED,
    Organization.Status.ARCHIVED,
    Organization.Status.DECLINED,
)


@rules.predicate
def is_staff_acting(user, obj=None):
    organization = _current_organization(user)
    return user.is_authenticated and user.is_staff and not organization.is_anonymous


@rules.predicate
def has_membership_in_current(user, obj=None):
    organization = _current_organization(user)
    return not organization.is_anonymous and organization.is_member(user)


@rules.predicate
def belongs_to_current_organization(user, obj):
    """True when obj belongs to the acting organization.

    Returns True when obj is None so that the same permission string works for both
    list-level checks (no object) and object-level checks. Requires the model to
    have an owner_organization_id attribute.
    """
    if obj is None:
        return True
    organization = _current_organization(user)
    return not organization.is_anonymous and getattr(obj, "owner_organization_id", None) == organization.pk


def _effective_permissions(user, organization) -> frozenset[str]:
    """Compute the effective permission codes for user acting in organization.

    Cached on user._permission_cache[organization.pk] for the lifetime of the request.
    Result is the intersection of the user's role+override set and the organization's
    capability+override set.
    """
    cache = getattr(user, "_permission_cache", None)
    if cache is None:
        cache = {}
        user._permission_cache = cache

    if organization.pk in cache:
        return cache[organization.pk]

    try:
        membership = Membership.objects.get(user=user, organization=organization)
    except Membership.DoesNotExist:
        cache[organization.pk] = frozenset()
        return frozenset()

    # --- User set ---
    role_codes: set[str] = set()
    if membership.role_id is not None:
        role_codes = set(Permission.objects.filter(groups=membership.role).values_list("code", flat=True))

    membership_allows: set[str] = set()
    membership_denies: set[str] = set()
    for override in MembershipPermissionOverride.objects.filter(membership=membership).select_related("permission"):
        if override.effect == MembershipPermissionOverride.Effect.ALLOW:
            membership_allows.add(override.permission.code)
        else:
            membership_denies.add(override.permission.code)

    user_set = (role_codes | membership_allows) - membership_denies

    # --- Organization set ---
    org_capability_codes: set[str] = set(
        Permission.objects.filter(
            groups__organizations=organization,
            groups__scope=Scope.ORGANIZATION,
        ).values_list("code", flat=True)
    )

    org_allows: set[str] = set()
    org_denies: set[str] = set()
    org_overrides = OrganizationPermissionOverride.objects.filter(organization=organization).select_related(
        "permission"
    )
    for override in org_overrides:
        if override.effect == OrganizationPermissionOverride.Effect.ALLOW:
            org_allows.add(override.permission.code)
        else:
            org_denies.add(override.permission.code)

    organization_set = (org_capability_codes | org_allows) - org_denies

    result = frozenset(user_set & organization_set)
    cache[organization.pk] = result
    return result


def cascade_grants(code: str):
    """Return a predicate that checks whether the cascade grants the given permission code."""

    @rules.predicate(name=f"cascade_grants:{code}")
    def predicate(user, obj=None):
        organization = _current_organization(user)
        return not organization.is_anonymous and code in _effective_permissions(user, organization)

    return predicate


def member_permission(code: str):
    """Return the standard member-side predicate for a permission code.

    Composes staff bypass, lifecycle check, membership check, and the cascade.
    Use this as the ``rule`` argument to ``register_permission`` for all member-side
    permissions. For permissions that also need object-level checks, compose with &:

        register_permission(
            "donations.edit_donation", "...",
            rule=member_permission("donations.edit_donation") & belongs_to_current_organization,
        )
    """
    return is_staff_acting | (organization_is_active & has_membership_in_current & cascade_grants(code))


def application_permission(code: str):
    """Like member_permission but requires only application-state org access (DRAFT/PENDING/NEEDS_INFO)."""
    return is_staff_acting | (organization_in_application & has_membership_in_current & cascade_grants(code))
