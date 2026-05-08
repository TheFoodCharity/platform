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

    class QuantityUnit(models.TextChoices):
        ITEMS = "items", "Items"
        BOXES = "boxes", "Boxes"
        CASES = "cases", "Cases"
        BAGS = "bags", "Bags"
        PALLETS = "pallets", "Pallets"
        KILOGRAMS = "kg", "Kilograms"
        POUNDS = "lb", "Pounds"
        LITRES = "litres", "Litres"

    class WeightUnit(models.TextChoices):
        KILOGRAMS = "kg", "Kilograms"
        POUNDS = "lb", "Pounds"

    donor_name = models.CharField(max_length=255)
    donor_contact = models.CharField(max_length=255, blank=True)

    food_category = models.CharField(
        max_length=50,
        choices=FoodCategory.choices,
        default=FoodCategory.OTHER,
    )
    food_type = models.JSONField(default=list)
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=50, choices=QuantityUnit.choices, default=QuantityUnit.ITEMS)
    estimated_weight = models.PositiveIntegerField(null=True, blank=True)
    estimated_weight_unit = models.CharField(max_length=20, choices=WeightUnit.choices, default=WeightUnit.POUNDS)

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
        return f"{self.food_type_display} - {self.donor_name}"

    @property
    def food_type_display(self):
        labels = dict(self.FoodCategory.choices)
        if isinstance(self.food_type, list):
            return ", ".join(labels.get(food_type, food_type) for food_type in self.food_type)
        return labels.get(self.food_type, self.food_type)

    @property
    def estimated_weight_display(self):
        if self.estimated_weight is None:
            return ""
        return f"{self.estimated_weight} {self.get_estimated_weight_unit_display()}"

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
