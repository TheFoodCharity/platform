from django.conf import settings
from django.db import models
from django.db.models import Sum

from storage.models import StorageLocation


class Donation(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        AVAILABLE = "available", "Available"
        IN_TRANSIT = "in_transit", "In Transit"
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
        BAGS = "bags", "Bags"
        BOXES = "boxes", "Boxes"
        CASES = "cases", "Cases"
        PALLETS = "pallets", "Pallets"
        OTHER = "other", "Other"

    class PickupDay(models.TextChoices):
        TODAY = "today", "Today"
        TOMORROW = "tomorrow", "Tomorrow"

    class PickupReadyTime(models.TextChoices):
        READY_NOW = "ready_now", "It is packaged and ready to go"
        FROM_8AM = "8am", "From 8am"
        FROM_9AM = "9am", "From 9am"
        FROM_10AM = "10am", "From 10am"
        FROM_11AM = "11am", "From 11am"
        FROM_12PM = "12pm", "From 12pm"
        FROM_1PM = "1pm", "From 1pm"
        FROM_2PM = "2pm", "From 2pm"
        FROM_3PM = "3pm", "From 3pm"
        FROM_4PM = "4pm", "From 4pm"
        FROM_5PM = "5pm", "From 5pm"

    class PickupEndTime(models.TextChoices):
        BEFORE_noon = "before_noon", "Before noon"
        BEFORE_1PM = "before_1pm", "Before 1pm"
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

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_donations",
    )
    supplier_organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donations",
    )

    food_category = models.CharField(
        max_length=50,
        choices=FoodCategory.choices,
        default=FoodCategory.OTHER,
    )
    food_type = models.JSONField(default=list)
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=50, choices=QuantityUnit.choices)

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
        default=Status.SUBMITTED,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "donations_donationticket"
        ordering = ["-created_at"]
        verbose_name = "Donation"
        verbose_name_plural = "Donations"

    def __str__(self):
        return f"{self.food_type_display} - {self.donor_display_name}"

    @property
    def donor_display_name(self):
        if self.supplier_organization_id:
            return self.supplier_organization.name
        if self.submitted_by_id:
            return self.submitted_by.get_full_name().strip() or self.submitted_by.email
        return "Unknown donor"

    @property
    def donor_contact_display(self):
        if self.supplier_organization_id and self.supplier_organization.email:
            return self.supplier_organization.email
        if self.submitted_by_id:
            return self.submitted_by.email
        return ""

    @property
    def food_type_display(self):
        labels = dict(self.FoodCategory.choices)
        if isinstance(self.food_type, list):
            return ", ".join(labels.get(food_type, food_type) for food_type in self.food_type)
        return labels.get(self.food_type, self.food_type)

    def assign_storage(self, storage_location):
        self.assigned_storage = storage_location
        self.status = self.Status.IN_TRANSIT

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
        BAGS = "bags", "Bags"
        BOXES = "boxes", "Boxes"
        CASES = "cases", "Cases"
        PALLETS = "pallets", "Pallets"
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

    @property
    def allocated_quantity(self):
        allocated = self.request_allocations.exclude(
            food_request__status__in=[
                FoodRequest.Status.DECLINED,
                FoodRequest.Status.CANCELLED,
            ],
        ).aggregate(total=Sum("quantity"))["total"]
        return allocated or 0

    @property
    def remaining_quantity(self):
        return max(self.quantity - self.allocated_quantity, 0)


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
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="food_requests",
    )
    receiver_organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="food_requests",
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
        return f"{self.receiver_display_name} request for {self.donation}"

    @property
    def receiver_display_name(self):
        if self.requested_by_id:
            return self.requested_by.get_full_name().strip() or self.requested_by.email
        return "Unknown receiver"

    @property
    def receiver_organization_display(self):
        if self.receiver_organization_id:
            return self.receiver_organization.name
        return ""

    @property
    def receiver_email_display(self):
        if self.receiver_organization_id and self.receiver_organization.email:
            return self.receiver_organization.email
        if self.requested_by_id:
            return self.requested_by.email
        return ""

    @property
    def receiver_phone_display(self):
        if self.receiver_organization_id and self.receiver_organization.phone:
            return str(self.receiver_organization.phone)
        return ""


class FoodRequestAllocation(models.Model):
    food_request = models.ForeignKey(
        FoodRequest,
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    donation_food_item = models.ForeignKey(
        DonationFoodItem,
        on_delete=models.CASCADE,
        related_name="request_allocations",
    )
    quantity = models.PositiveIntegerField()

    class Meta:
        ordering = ["id"]
        verbose_name = "Food Request Allocation"
        verbose_name_plural = "Food Request Allocations"

    def __str__(self):
        return f"{self.quantity} from {self.donation_food_item}"
