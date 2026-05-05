from django.db import models


class StorageLocation(models.Model):
    class StorageType(models.TextChoices):
        DRY = "dry", "Dry Storage"
        REFRIGERATED = "refrigerated", "Cold/Refrigerated Storage"
        FROZEN = "frozen", "Frozen Storage"
        WAREHOUSE = "warehouse", "Palletized Warehouse Storage"
        SMALL_ROOM = "small_room", "Small-Room Storage"
        PANTRY = "pantry", "Community Pantry Storage"
        KITCHEN = "kitchen", "Commercial Kitchen Storage"
        EMERGENCY = "emergency", "Temporary/Emergency Storage"
        OTHER = "other", "Other"

    class CapacityStatus(models.TextChoices):
        AVAILABLE = "available", "Available"
        LIMITED = "limited", "Limited"
        FULL = "full", "Full"
        UNAVAILABLE = "unavailable", "Temporarily Unavailable"

    class PermissionLevel(models.TextChoices):
        ADMIN_ONLY = "admin_only", "Admin Only"
        APPROVED_MEMBERS = "approved_members", "Approved Members"
        RESTRICTED_GROUP = "restricted_group", "Restricted Group"
        REGION_ONLY = "region_only", "Region Only"
        DIRECT_PARTNER = "direct_partner", "Direct Partner Only"

    class ApprovalStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved"
        NEEDS_UPDATE = "needs_update", "Needs Update"
        INACTIVE = "inactive", "Inactive"
        ARCHIVED = "archived", "Archived"

    # Basic info
    name = models.CharField(max_length=255)
    owner_operator = models.CharField(max_length=255, blank=True)

    # Location / map-ready fields
    address = models.CharField(max_length=255)
    approximate_location = models.CharField(max_length=255, blank=True)
    municipality = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    province = models.CharField(max_length=100, default="British Columbia")
    postal_code = models.CharField(max_length=20, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Contact
    contact_person = models.CharField(max_length=255, blank=True)
    contact_method = models.CharField(max_length=255, blank=True)

    # Storage details
    storage_type = models.CharField(
        max_length=50,
        choices=StorageType.choices,
        default=StorageType.DRY,
    )
    accepted_food_types = models.TextField(blank=True)

    dry_capacity = models.PositiveIntegerField(null=True, blank=True)
    refrigerated_capacity = models.PositiveIntegerField(null=True, blank=True)
    frozen_capacity = models.PositiveIntegerField(null=True, blank=True)
    available_space = models.PositiveIntegerField(null=True, blank=True)
    capacity_status = models.CharField(
        max_length=50,
        choices=CapacityStatus.choices,
        default=CapacityStatus.AVAILABLE,
    )

    # Access / restrictions
    access_hours = models.CharField(max_length=255, blank=True)
    restrictions = models.TextField(blank=True)
    special_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    # Equipment / facility capability
    has_loading_dock = models.BooleanField(default=False)
    has_ramp_access = models.BooleanField(default=False)
    has_liftgate_access = models.BooleanField(default=False)
    has_forklift = models.BooleanField(default=False)
    has_pallet_jack = models.BooleanField(default=False)
    has_floor_jack = models.BooleanField(default=False)
    has_hand_truck = models.BooleanField(default=False)
    max_pallet_capacity = models.PositiveIntegerField(null=True, blank=True)
    max_load_size = models.CharField(max_length=100, blank=True)

    # Permission / admin workflow
    permission_level = models.CharField(
        max_length=50,
        choices=PermissionLevel.choices,
        default=PermissionLevel.ADMIN_ONLY,
    )
    approval_status = models.CharField(
        max_length=50,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )

    # Verification / lifecycle
    is_active = models.BooleanField(default=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    verification_requested_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Storage Location"
        verbose_name_plural = "Storage Locations"

    def __str__(self):
        return self.name