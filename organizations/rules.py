from .constants import SystemRole
from .predicates import application_permission, member_permission
from .registry import register_permission

register_permission(
    "organizations.view_application",
    "View the organization application dashboard and section forms",
    rule=application_permission("organizations.view_application"),
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
)

register_permission(
    "organizations.edit_application",
    "Edit organization application sections",
    rule=application_permission("organizations.edit_application"),
    roles=[SystemRole.ORGANIZATION_MANAGER],
)

register_permission(
    "organizations.submit_application",
    "Submit or resubmit the organization application",
    rule=application_permission("organizations.submit_application"),
    roles=[SystemRole.ORGANIZATION_MANAGER],
)

register_permission(
    "organizations.manage_profile",
    "Edit the organization profile",
    rule=member_permission("organizations.manage_profile"),
    roles=[SystemRole.ORGANIZATION_MANAGER],
)

register_permission(
    "organizations.manage_members",
    "Invite users and manage organization memberships",
    rule=member_permission("organizations.manage_members"),
    roles=[SystemRole.ORGANIZATION_MANAGER],
)
