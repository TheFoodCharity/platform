from django.db import models

from storage.models import StorageLocation


class Donation(models.Model):
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
        BAKED_GOODS = "baked_goods", "Baked Goods"
        DAIRY = "dairy", "Dairy"
        MEAT_PROTEIN = "meat_protein", "Meat & Protein"
        NON_FOOD = "non_food", "Non-Food"
        NON_PERISHABLE = "non_perishable", "Non-Perishable"
        PREPARED_INDIVIDUAL = "prepared_individual", "Prepared - Individually Packaged"
        PREPARED_TRAYS = "prepared_trays", "Prepared - Trays/Multi-Serving"
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
        SMALL_BAGS = "small_bags", "Small bags"
        LARGE_BAGS = "large_bags", "Large bags"
        BOXES = "boxes", "Boxes"
        CASES = "cases", "Cases"
        BAGS = "bags", "Bags"
        CRATES = "crates", "Crates"
        FLATS = "flats", "Flats"
        GALLONS = "gallons", "Gallons"
        GAYLORDS = "gaylords", "Gaylords"
        PALLETS = "pallets", "Pallets"
        TRAYS = "trays", "Trays"
        KILOGRAMS = "kg", "Kilograms"
        POUNDS = "lb", "Pounds"
        LITRES = "litres", "Litres"
        OTHER = "other", "Other"

    class WeightUnit(models.TextChoices):
        KILOGRAMS = "kg", "Kilograms"
        POUNDS = "lb", "Pounds"

    class PickupDay(models.TextChoices):
        TODAY = "today", "Today"
        TOMORROW = "tomorrow", "Tomorrow"

    class PickupReadyTime(models.TextChoices):
        READY_NOW = "ready_now", "It is packaged and ready to go"
        FROM_12PM = "12pm", "From 12pm"
        FROM_1PM = "1pm", "From 1pm"
        FROM_2PM = "2pm", "From 2pm"
        FROM_3PM = "3pm", "From 3pm"

    class PickupEndTime(models.TextChoices):
        BEFORE_2PM = "before_2pm", "Before 2pm"
        BEFORE_3PM = "before_3pm", "Before 3pm"
        BEFORE_4PM = "before_4pm", "Before 4pm"
        BEFORE_5PM = "before_5pm", "Before 5pm"

    class PeopleFedEstimate(models.IntegerChoices):
        FIVE = 5, "5"
        TEN = 10, "10"
        FIFTEEN = 15, "15"
        TWENTY = 20, "20"
        TWENTY_FIVE = 25, "25"
        THIRTY = 30, "30"
        FORTY = 40, "40"
        FIFTY = 50, "50"
        SEVENTY_FIVE = 75, "75"
        ONE_HUNDRED = 100, "100"
        ONE_HUNDRED_FIFTY = 150, "150"
        TWO_HUNDRED = 200, "200"
        THREE_HUNDRED = 300, "300"

    company_name = models.CharField(max_length=255, blank=True)
    address_1 = models.CharField(max_length=255, blank=True)
    address_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    province_or_state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)

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
    pickup_day = models.CharField(max_length=20, choices=PickupDay.choices, default=PickupDay.TODAY)
    pickup_ready_time = models.CharField(
        max_length=30,
        choices=PickupReadyTime.choices,
        default=PickupReadyTime.READY_NOW,
    )
    pickup_end_time = models.CharField(max_length=30, choices=PickupEndTime.choices, default=PickupEndTime.BEFORE_5PM)
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
    people_fed_estimate = models.PositiveIntegerField(choices=PeopleFedEstimate.choices, null=True, blank=True)
    fits_in_car = models.BooleanField(default=True)
    food_safety_agreement = models.BooleanField(default=False)
    other_information = models.TextField(blank=True)

    assigned_storage = models.ForeignKey(
        StorageLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donations",
    )

    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "donations_donationticket"
        ordering = ["-created_at"]
        verbose_name = "Donation"
        verbose_name_plural = "Donations"

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


class DonationFoodItem(models.Model):
    class Packaging(models.TextChoices):
        SMALL_BAGS = "small_bags", "Small bags"
        LARGE_BAGS = "large_bags", "Large bags"
        BOXES = "boxes", "Boxes"
        CASES = "cases", "Cases"
        CRATES = "crates", "Crates"
        FLATS = "flats", "Flats"
        GALLONS = "gallons", "Gallons"
        GAYLORDS = "gaylords", "Gaylords"
        PALLETS = "pallets", "Pallets"
        TRAYS = "trays", "Trays"
        OTHER = "other", "Other"

    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name="food_items")
    food_category = models.CharField(max_length=50, choices=Donation.FoodCategory.choices)
    packaging = models.CharField(max_length=50, choices=Packaging.choices)
    quantity = models.PositiveIntegerField()
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Donation Food Item"
        verbose_name_plural = "Donation Food Items"

    def __str__(self):
        return f"{self.quantity} {self.get_packaging_display()} of {self.get_food_category_display()}"


class FoodRequest(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        DECLINED = "declined", "Declined"
        FULFILLED = "fulfilled", "Fulfilled"
        CANCELLED = "cancelled", "Cancelled"

    donation = models.ForeignKey(
        Donation,
        on_delete=models.CASCADE,
        related_name="food_requests",
    )
    receiver_name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    requested_quantity = models.PositiveIntegerField()
    requested_unit = models.CharField(
        max_length=50,
        choices=Donation.QuantityUnit.choices,
        default=Donation.QuantityUnit.ITEMS,
    )
    storage_required = models.BooleanField(default=False)
    preferred_storage = models.ForeignKey(
        StorageLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="food_requests",
    )
    storage_notes = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Food Request"
        verbose_name_plural = "Food Requests"

    def __str__(self):
        return f"{self.receiver_name} request for {self.donation}"
