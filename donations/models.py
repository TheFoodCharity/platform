from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.formats import date_format

from storage.models import StorageLocation


class Donation(models.Model):
    """A supplier's donation ticket, tracked with the user and organization that submitted it."""

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

    class ReceiverLimit(models.TextChoices):
        ONE = "one", "1 receiver only"
        TWO = "two", "Maximum 2 receivers"
        NO_LIMIT = "no_limit", "No limit"

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_donations",
    )
    supplier_organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="donations",
    )
    preferred_receiver_organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferred_donations",
        verbose_name="preferred receiver",
    )
    receiver_limit = models.CharField(
        "maximum number of receivers",
        max_length=20,
        choices=ReceiverLimit.choices,
        default=ReceiverLimit.ONE,
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
    pickup_notes = models.CharField(max_length=255, blank=True)
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

    people_fed_estimate = models.PositiveIntegerField(choices=PeopleFedEstimate.choices, null=True, blank=True)
    fits_in_car = models.BooleanField(default=True)
    food_safety_agreement = models.BooleanField(default=False)
    other_information = models.TextField(blank=True)

    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.AVAILABLE,
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
    def ticket_number(self):
        """Human-readable identifier used in app screens and admin lists."""
        if self.pk is None:
            return "DON-unsaved"
        return f"DON-{self.pk:06d}"

    @property
    def donor_display_name(self):
        return self.supplier_organization.name

    @property
    def donor_contact_display(self):
        if self.supplier_organization.email:
            return self.supplier_organization.email
        return self.submitted_by.email

    @property
    def donor_public_phone_display(self):
        if self.supplier_organization.phone:
            return str(self.supplier_organization.phone)
        return ""

    @property
    def food_type_display(self):
        """Render the stored category list with labels instead of raw enum values."""
        labels = dict(self.FoodCategory.choices)
        if isinstance(self.food_type, list):
            return ", ".join(labels.get(food_type, food_type) for food_type in self.food_type)
        return labels.get(self.food_type, self.food_type)

    @property
    def category_list_display(self):
        """Prefer current food item categories, falling back to legacy summary fields."""
        labels = dict(self.FoodCategory.choices)
        categories = []

        for food_item in self.food_items.all():
            if food_item.food_category not in categories:
                categories.append(food_item.food_category)

        if not categories and isinstance(self.food_type, list):
            categories = self.food_type

        if not categories:
            categories = [self.food_category]

        return ", ".join(labels.get(category, category) for category in categories)

    @property
    def total_remaining_quantity(self):
        """Total packages still available across all food items."""
        return sum(food_item.remaining_quantity for food_item in self.food_items.all())

    @property
    def quantity_summary_display(self):
        totals_by_packaging = {}
        packaging_labels = dict(DonationFoodItem.Packaging.choices)

        # Only combine quantities that share the same packaging unit.
        for food_item in self.food_items.all():
            totals_by_packaging[food_item.packaging] = (
                totals_by_packaging.get(food_item.packaging, 0) + food_item.quantity
            )

        if not totals_by_packaging:
            return f"{self.quantity} {self.get_unit_display()}"

        return ", ".join(
            f"{quantity} {packaging_labels.get(packaging, packaging)}"
            for packaging, quantity in totals_by_packaging.items()
        )

    @property
    def pickup_summary_display(self):
        if timezone.localtime(self.pickup_deadline).date() < timezone.localdate():
            return date_format(timezone.localtime(self.pickup_deadline), "M j, Y g:i A")
        return f"{self.get_pickup_day_display()}, {self.get_pickup_end_time_display()}"

    @property
    def is_fully_requested(self):
        return self.food_items.exists() and self.total_remaining_quantity == 0

    @property
    def receiver_limit_count(self):
        limits = {
            self.ReceiverLimit.ONE: 1,
            self.ReceiverLimit.TWO: 2,
        }
        return limits.get(self.receiver_limit)

    def active_receiver_organization_ids(self):
        return set(
            self.food_requests.exclude(
                status__in=[FoodRequest.Status.DECLINED, FoodRequest.Status.CANCELLED],
            )
            .values_list("receiver_organization_id", flat=True)
            .distinct(),
        )

    def can_accept_receiver(self, organization):
        """Return whether this organization can still request from this donation."""
        receiver_limit_count = self.receiver_limit_count
        if receiver_limit_count is None or organization is None:
            return True

        receiver_ids = self.active_receiver_organization_ids()
        if organization.pk in receiver_ids:
            return True

        return len(receiver_ids) < receiver_limit_count

    def is_final_receiver_slot(self, organization):
        """When the requester is the final allowed receiver, they must claim all remaining food."""
        receiver_limit_count = self.receiver_limit_count
        if receiver_limit_count is None or organization is None:
            return False

        other_receiver_ids = self.active_receiver_organization_ids() - {organization.pk}
        return len(other_receiver_ids) >= receiver_limit_count - 1

    @property
    def allocation_status_display(self):
        if self.is_fully_requested:
            return "Fully requested"
        return "Available"


class DonationFoodItem(models.Model):
    """A specific food category and package count within a donation."""

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
        """Quantity requested from this item, excluding declined or cancelled requests."""
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
    """A receiver organization's request for some or all food from a donation."""

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
        on_delete=models.PROTECT,
        related_name="food_requests",
    )
    receiver_organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
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
    def ticket_number(self):
        """Human-readable identifier used in app screens and admin lists."""
        if self.pk is None:
            return "REQ-unsaved"
        return f"REQ-{self.pk:06d}"

    @property
    def receiver_display_name(self):
        return self.requested_by.get_full_name().strip() or self.requested_by.email

    @property
    def receiver_organization_display(self):
        return self.receiver_organization.name

    @property
    def receiver_email_display(self):
        if self.receiver_organization.email:
            return self.receiver_organization.email
        return self.requested_by.email

    @property
    def receiver_phone_display(self):
        if self.receiver_organization.phone:
            return str(self.receiver_organization.phone)
        return ""


class FoodRequestAllocation(models.Model):
    """The requested quantity for one donation food item within a food request."""

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
