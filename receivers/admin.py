from django.contrib import admin

from .models import FoodRequest


@admin.register(FoodRequest)
class FoodRequestAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "receiver_name",
        "organization",
        "donation_ticket",
        "requested_quantity",
        "requested_unit",
        "storage_required",
        "preferred_storage",
        "status",
        "created_at",
    )
    list_filter = ("status", "storage_required", "requested_unit", "preferred_storage", "created_at")
    search_fields = ("receiver_name", "organization", "email", "donation_ticket__donor_name", "preferred_storage__name")
    readonly_fields = ("created_at", "updated_at")
