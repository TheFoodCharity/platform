from django.contrib import admin

from .models import StorageLocation


@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "municipality",
        "region",
        "available_space",
        "is_active",
    )

    search_fields = ("name", "municipality", "region")
