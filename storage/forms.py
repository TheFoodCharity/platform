from django import forms

from .models import StorageLocation


class StorageLocationForm(forms.ModelForm):
    class Meta:
        model = StorageLocation

        fields = [
            "name",
            "owner_operator",
            "address",
            "approximate_location",
            "municipality",
            "region",
            "province",
            "postal_code",
            "latitude",
            "longitude",
            "contact_person",
            "contact_method",
            "storage_type",
            "accepted_food_types",
            "dry_capacity",
            "refrigerated_capacity",
            "frozen_capacity",
            "available_space",
            "capacity_status",
            "access_hours",
            "restrictions",
            "special_notes",
            "admin_notes",
            "has_loading_dock",
            "has_ramp_access",
            "has_liftgate_access",
            "has_forklift",
            "has_pallet_jack",
            "has_floor_jack",
            "has_hand_truck",
            "max_pallet_capacity",
            "max_load_size",
            "permission_level",
            "approval_status",
            "is_active",
        ]
