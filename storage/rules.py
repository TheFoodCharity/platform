from organizations.predicates import member_permission
from permissions import SystemCapability, SystemRole, register_permission

register_permission(
    "storage.view_storage_locations",
    "View storage locations",
    rule=member_permission("storage.view_storage_locations"),
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
    capabilities=[SystemCapability.STORAGE_PROVIDER, SystemCapability.READ_ONLY],
)

register_permission(
    "storage.view_storage_location_detail",
    "View storage location details",
    rule=member_permission("storage.view_storage_location_detail"),
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
    capabilities=[SystemCapability.STORAGE_PROVIDER, SystemCapability.READ_ONLY],
)

register_permission(
    "storage.create_storage_location",
    "Create storage locations",
    rule=member_permission("storage.create_storage_location"),
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
    capabilities=[SystemCapability.STORAGE_PROVIDER],
)

register_permission(
    "storage.edit_storage_location",
    "Edit storage locations",
    rule=member_permission("storage.edit_storage_location"),
    roles=[SystemRole.ORGANIZATION_MANAGER, SystemRole.ORGANIZATION_USER],
    capabilities=[SystemCapability.STORAGE_PROVIDER],
)
