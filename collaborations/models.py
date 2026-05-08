import uuid

from django.conf import settings
from django.db import models

from organizations.models import Organization


class CollaborationSpaceRequest(models.Model):
    class TopicCategory(models.TextChoices):
        FOOD_SUPPLY = "food_supply", "Food supply"
        STORAGE = "storage", "Storage"
        DISTRIBUTION = "distribution", "Distribution"
        VOLUNTEERS = "volunteers", "Volunteers"
        EMERGENCY_RESPONSE = "emergency_response", "Emergency response"
        OTHER = "other", "Other"

    class VisibilityPreference(models.TextChoices):
        INVITE_ONLY = "invite_only", "Invite only"
        APPROVED_MEMBERS = "approved_members", "Approved members"
        REGION_ONLY = "region_only", "Region only"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        DECLINED = "declined", "Declined"
        NEEDS_INFO = "needs_info", "Needs more information"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    purpose = models.TextField()
    topic_category = models.CharField(
        max_length=50,
        choices=TopicCategory.choices,
        default=TopicCategory.OTHER,
    )
    region = models.CharField(max_length=100, blank=True)
    municipality = models.CharField(max_length=100, blank=True)
    suggested_participants = models.TextField(blank=True)
    visibility_preference = models.CharField(
        max_length=50,
        choices=VisibilityPreference.choices,
        default=VisibilityPreference.INVITE_ONLY,
    )
    reason_for_request = models.TextField()
    requested_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="collaboration_requests",
        on_delete=models.PROTECT,
    )
    requested_by_org = models.ForeignKey(
        Organization,
        related_name="collaboration_requests",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="reviewed_collaboration_requests",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
