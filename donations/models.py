from django.db import models

from storage.models import StorageLocation


class DonationTicket(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        AVAILABLE = "available", "Available"
        PENDING = "pending", "Pending"
        MATCHED = "matched", "Matched"
        IN_TRANSIT = "in_transit", "In Transit"
        STORED = "stored", "Stored"
        DELIVERED = "delivered", "Delivered"
        COMPLETED = "completed", "Completed"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    class StorageRequirement(models.TextChoices):
        DRY = "dry", "Dry Storage"
        REFRIGERATED = "refrigerated", "Refrigerated Storage"
        FROZEN = "frozen", "Frozen Storage"
        NONE = "none", "No Storage Needed"

    class FoodCategory(models.TextChoices):
        PRODUCE = "produce", "Fresh Produce"
        REFRIGERATED = "refrigerated", "Perishable Refrigerated"
        FROZEN = "frozen", "Frozen"
        DRY_GOODS = "dry_goods", "Dry Goods"
        CANNED = "canned", "Canned/Shelf-Stable"
        PREPARED = "prepared", "Prepared Food"
        BULK = "bulk", "Bulk Ingredients"
        PALLETIZED = "palletized", "Palletized Goods"
        MIXED = "mixed", "Small Mixed Donation"
        OTHER = "other", "Other"

    donor_name = models.CharField(max_length=255)
    donor_contact = models.CharField(max_length=255, blank=True)

    food_category = models.CharField(
        max_length=50,
        choices=FoodCategory.choices,
        default=FoodCategory.OTHER,
    )
    food_type = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=50, default="items")
    estimated_weight = models.PositiveIntegerField(null=True, blank=True)

    pickup_location = models.CharField(max_length=255)
    pickup_window = models.CharField(max_length=255, blank=True)
    pickup_deadline = models.DateTimeField()
    best_before_date = models.DateField(null=True, blank=True)

    storage_requirement = models.CharField(
        max_length=50,
        choices=StorageRequirement.choices,
        default=StorageRequirement.DRY,
    )
    temperature_requirement = models.CharField(max_length=100, blank=True)

    requires_van = models.BooleanField(default=False)
    requires_cube_van = models.BooleanField(default=False)
    requires_refrigerated_vehicle = models.BooleanField(default=False)
    requires_pallet_jack = models.BooleanField(default=False)
    requires_forklift = models.BooleanField(default=False)
    loading_dock_available = models.BooleanField(default=False)
    donor_can_help_load = models.BooleanField(default=False)

    special_handling_notes = models.TextField(blank=True)
    chain_of_custody_notes = models.TextField(blank=True)

    assigned_storage = models.ForeignKey(
        StorageLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donation_tickets",
    )

    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Donation Ticket"
        verbose_name_plural = "Donation Tickets"

    def __str__(self):
        return f"{self.food_type} - {self.donor_name}"

    def assign_storage(self, storage_location):
        self.assigned_storage = storage_location
        self.status = self.Status.MATCHED

        if storage_location.available_space is not None:
            storage_location.available_space = max(
                storage_location.available_space - self.quantity,
                0,
            )
            storage_location.update_capacity_status()
            storage_location.save()

        self.save()
