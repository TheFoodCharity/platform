from django.db import models


class StorageLocation(models.Model):
    name = models.CharField(max_length=255)

    # location
    address = models.CharField(max_length=255)
    municipality = models.CharField(max_length=100)
    region = models.CharField(max_length=100)

    # capacity
    dry_capacity = models.IntegerField(null=True, blank=True)
    refrigerated_capacity = models.IntegerField(null=True, blank=True)
    frozen_capacity = models.IntegerField(null=True, blank=True)
    available_space = models.IntegerField(null=True, blank=True)

    # operations
    access_hours = models.CharField(max_length=255, blank=True)
    restrictions = models.TextField(blank=True)

    # equipment
    has_forklift = models.BooleanField(default=False)
    has_pallet_jack = models.BooleanField(default=False)
    has_loading_dock = models.BooleanField(default=False)

    # system
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
