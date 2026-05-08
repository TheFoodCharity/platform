from django.contrib import admin

from .models import FoodHelpLocation


@admin.register(FoodHelpLocation)
class FoodHelpLocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "service_type",
        "municipality",
        "is_public",
        "is_approved",
        "last_verified",
    )

    list_filter = (
        "service_type",
        "municipality",
        "is_approved",
    )

    search_fields = (
        "name",
        "municipality",
        "region",
        "address",
    )
