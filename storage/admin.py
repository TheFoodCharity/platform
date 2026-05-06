from django.contrib import admin

from .models import StorageLocation


@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    ordering = ("name",)
    list_per_page = 25
    empty_value_display = "-"

    list_display = (
        "name",
        "municipality",
        "region",
        "storage_type",
        "capacity_status",
        "permission_level",
        "approval_status",
        "is_active",
        "updated_at",
    )

    list_filter = (
        "storage_type",
        "capacity_status",
        "permission_level",
        "approval_status",
        "is_active",
        "municipality",
        "region",
        "has_loading_dock",
        "has_forklift",
        "has_pallet_jack",
    )

    search_fields = (
        "name",
        "owner_operator",
        "address",
        "municipality",
        "region",
        "accepted_food_types",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Basic Information", {"fields": ("name", "owner_operator", "is_active")}),
        (
            "Location",
            {
                "fields": (
                    "address",
                    "approximate_location",
                    "municipality",
                    "region",
                    "province",
                    "postal_code",
                    "latitude",
                    "longitude",
                )
            },
        ),
        ("Contact", {"fields": ("contact_person", "contact_method")}),
        (
            "Storage Capacity",
            {
                "fields": (
                    "storage_type",
                    "accepted_food_types",
                    "dry_capacity",
                    "refrigerated_capacity",
                    "frozen_capacity",
                    "available_space",
                    "capacity_status",
                )
            },
        ),
        (
            "Access and Notes",
            {
                "fields": (
                    "access_hours",
                    "restrictions",
                    "special_notes",
                    "admin_notes",
                )
            },
        ),
        (
            "Equipment and Facility Capabilities",
            {
                "fields": (
                    "has_loading_dock",
                    "has_ramp_access",
                    "has_liftgate_access",
                    "has_forklift",
                    "has_pallet_jack",
                    "has_floor_jack",
                    "has_hand_truck",
                    "max_pallet_capacity",
                    "max_load_size",
                )
            },
        ),
        (
            "Permissions and Approval",
            {
                "fields": (
                    "permission_level",
                    "approval_status",
                )
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "last_verified_at",
                    "verification_requested_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
