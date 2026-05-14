from django.contrib import admin

from .models import Donation, DonationFoodItem, FoodRequest, FoodRequestAllocation


class DonationFoodItemInline(admin.TabularInline):
    model = DonationFoodItem
    extra = 1


class FoodRequestAllocationInline(admin.TabularInline):
    model = FoodRequestAllocation
    extra = 0
    readonly_fields = ("donation_food_item", "quantity")
    can_delete = False


class FoodRequestInline(admin.TabularInline):
    model = FoodRequest
    extra = 0
    fields = (
        "ticket_number",
        "requested_by",
        "receiver_organization",
        "status",
        "created_at",
    )
    readonly_fields = fields
    can_delete = False
    show_change_link = True


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    inlines = [DonationFoodItemInline, FoodRequestInline]
    ordering = ("-created_at",)
    list_per_page = 25
    empty_value_display = "-"

    list_display = (
        "ticket_number",
        "donor_display_name",
        "submitted_by",
        "supplier_organization",
        "food_type_display",
        "food_category",
        "quantity",
        "unit",
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
        "ticket_number",
        "created_at",
        "updated_at",
    )


@admin.register(FoodRequest)
class FoodRequestAdmin(admin.ModelAdmin):
    inlines = [FoodRequestAllocationInline]
    ordering = ("-created_at",)
    list_display = (
        "ticket_number",
        "receiver_display_name",
        "requested_by",
        "receiver_organization",
        "donation",
        "storage_required",
        "preferred_storage",
        "status",
        "created_at",
    )
    list_filter = (
        "status",
        "storage_required",
        "preferred_storage",
        "receiver_organization",
        "created_at",
    )
    search_fields = (
        "requested_by__email",
        "requested_by__first_name",
        "requested_by__last_name",
        "receiver_organization__name",
        "donation__submitted_by__email",
        "donation__supplier_organization__name",
        "preferred_storage__name",
    )
    readonly_fields = ("ticket_number", "created_at", "updated_at")
