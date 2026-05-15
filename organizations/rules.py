from permissions import SystemCapability, SystemRole, register_permission

from .predicates import application_permission, is_organization_owner, member_permission

register_permission(
    "organizations.view_application",
    "View the organization application dashboard and section forms",
    rule=application_permission("organizations.view_application"),
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
    capabilities=[SystemCapability.DEFAULT],
)

register_permission(
    "organizations.edit_application",
    "Edit organization application sections",
    rule=application_permission("organizations.edit_application"),
    roles=[SystemRole.ORGANIZATION_MANAGER],
    capabilities=[SystemCapability.DEFAULT],
)

register_permission(
    "organizations.submit_application",
    "Submit or resubmit the organization application",
    rule=application_permission("organizations.submit_application"),
    roles=[SystemRole.ORGANIZATION_MANAGER],
    capabilities=[SystemCapability.DEFAULT],
)

register_permission(
    "organizations.view_profile",
    "View the organization profile",
    rule=member_permission("organizations.view_profile"),
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
    capabilities=[SystemCapability.DEFAULT],
)

register_permission(
    "organizations.edit_profile",
    "Edit the organization profile",
    rule=member_permission("organizations.edit_profile"),
    roles=[SystemRole.ORGANIZATION_MANAGER],
    capabilities=[SystemCapability.DEFAULT],
)

register_permission(
    "organizations.invite_member",
    "Invite a new member to the organization",
    rule=member_permission("organizations.invite_member"),
    roles=[SystemRole.ORGANIZATION_MANAGER],
    capabilities=[SystemCapability.DEFAULT],
)

register_permission(
    "organizations.view_members",
    "View organization members",
    rule=member_permission("organizations.view_members"),
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
    capabilities=[SystemCapability.DEFAULT],
)

register_permission(
    "organizations.edit_member_permissions",
    "Modify the permissions of organization members",
    rule=member_permission("organizations.edit_member_permissions"),
    roles=[SystemRole.ORGANIZATION_MANAGER],
    capabilities=[SystemCapability.DEFAULT],
)

register_permission(
    "organizations.remove_member",
    "Remove a member from the organization",
    rule=member_permission("organizations.remove_member"),
    roles=[SystemRole.ORGANIZATION_MANAGER],
    capabilities=[SystemCapability.DEFAULT],
)

register_permission(
    "organizations.transfer_ownership",
    "Transfer ownership of the organization to another member",
    rule=is_organization_owner,
    capabilities=[SystemCapability.DEFAULT],
)
