from django.contrib import admin

from .models import Donation, DonationFoodItem, FoodRequest


class DonationFoodItemInline(admin.TabularInline):
    model = DonationFoodItem
    extra = 1


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    inlines = [DonationFoodItemInline]
    ordering = ("-created_at",)
    list_per_page = 25
    empty_value_display = "-"

    list_display = (
        "donor_display_name",
        "submitted_by",
        "supplier_organization",
        "food_type_display",
        "food_category",
        "quantity",
        "unit",
        "estimated_weight_display",
        "storage_requirement",
        "assigned_storage",
        "status",
        "pickup_deadline",
        "created_at",
    )

    list_filter = (
        "status",
        "food_category",
        "supplier_organization",
        "storage_requirement",
        "requires_refrigerated_vehicle",
        "requires_forklift",
        "requires_pallet_jack",
        "created_at",
    )

    search_fields = (
        "submitted_by__first_name",
        "submitted_by__last_name",
        "submitted_by__email",
        "supplier_organization__name",
        "pickup_location",
        "special_handling_notes",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(FoodRequest)
class FoodRequestAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "receiver_name",
        "requested_by",
        "receiver_organization",
        "organization",
        "donation",
        "requested_quantity",
        "requested_unit",
        "storage_required",
        "preferred_storage",
        "status",
        "created_at",
    )
    list_filter = (
        "status",
        "storage_required",
        "requested_unit",
        "preferred_storage",
        "receiver_organization",
        "created_at",
    )
    search_fields = (
        "receiver_name",
        "organization",
        "email",
        "requested_by__email",
        "receiver_organization__name",
        "donation__submitted_by__email",
        "donation__supplier_organization__name",
        "preferred_storage__name",
    )
    readonly_fields = ("created_at", "updated_at")
