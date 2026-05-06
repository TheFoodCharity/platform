from django.contrib import admin

from .models import DonationTicket


@admin.register(DonationTicket)
class DonationTicketAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_per_page = 25
    empty_value_display = "-"

    list_display = (
        "donor_name",
        "food_type",
        "food_category",
        "quantity",
        "storage_requirement",
        "assigned_storage",
        "status",
        "pickup_deadline",
        "created_at",
    )

    list_filter = (
        "status",
        "food_category",
        "storage_requirement",
        "requires_refrigerated_vehicle",
        "requires_forklift",
        "requires_pallet_jack",
        "created_at",
    )

    search_fields = (
        "donor_name",
        "donor_contact",
        "food_type",
        "pickup_location",
        "special_handling_notes",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )
