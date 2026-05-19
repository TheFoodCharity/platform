import rules

from organizations.predicates import _current_organization, member_permission
from permissions import SystemCapability, SystemRole, register_permission


@rules.predicate
def donation_belongs_to_current_supplier(user, obj=None):
    """Restrict object-level donation permissions to the acting supplier organization."""
    if obj is None:
        return True

    organization = _current_organization(user)
    return not organization.is_anonymous and getattr(obj, "supplier_organization_id", None) == organization.pk


# Each registration participates in the permission cascade:
# membership role grants intersect with the acting organization's capabilities.
register_permission(
    "donations.view_donations",
    "View donation tickets for the current organization",
    rule=member_permission("donations.view_donations"),
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
    capabilities=[SystemCapability.FOOD_DONOR],
)

register_permission(
    "donations.create_donation",
    "Create food donation tickets",
    rule=member_permission("donations.create_donation"),
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
    capabilities=[SystemCapability.FOOD_DONOR],
)

register_permission(
    "donations.view_donation_detail",
    "View donation ticket details owned by the current organization",
    rule=member_permission("donations.view_donation_detail") & donation_belongs_to_current_supplier,
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
    capabilities=[SystemCapability.FOOD_DONOR],
)

register_permission(
    "donations.edit_donation",
    "Edit donation tickets owned by the current organization",
    rule=member_permission("donations.edit_donation") & donation_belongs_to_current_supplier,
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
    capabilities=[SystemCapability.FOOD_DONOR],
)

register_permission(
    "donations.view_available_donations",
    "View available donation tickets for requesting food",
    rule=member_permission("donations.view_available_donations"),
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
    capabilities=[SystemCapability.FOOD_RECEIVER],
)

register_permission(
    "donations.request_donation",
    "Submit food requests for available donations",
    rule=member_permission("donations.request_donation"),
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
    capabilities=[SystemCapability.FOOD_RECEIVER],
)

register_permission(
    "donations.view_food_request",
    "View food request details connected to the current organization",
    rule=member_permission("donations.view_food_request"),
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
    capabilities=[SystemCapability.FOOD_DONOR, SystemCapability.FOOD_RECEIVER],
)
