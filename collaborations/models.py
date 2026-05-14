import uuid
from pathlib import Path

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

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

    def approve(self, reviewer, admin_notes=""):
        with transaction.atomic():
            self.status = self.Status.APPROVED
            self.reviewed_by = reviewer
            self.reviewed_at = timezone.now()
            if admin_notes:
                self.admin_notes = admin_notes
            self.save(update_fields=["status", "reviewed_by", "reviewed_at", "admin_notes", "updated_at"])

            space, created = CollaborationSpace.objects.get_or_create(
                created_from_request=self,
                defaults={
                    "title": self.title,
                    "purpose": self.purpose,
                    "topic_category": self.topic_category,
                    "region": self.region,
                    "municipality": self.municipality,
                    "visibility_level": self.visibility_preference,
                    "status": CollaborationSpace.Status.ACTIVE,
                    "owner": self.requested_by_user,
                    "created_by": reviewer,
                    "last_activity_at": timezone.now(),
                },
            )
            if created:
                CollaborationSpaceUserMembership.objects.create(
                    space=space,
                    user=self.requested_by_user,
                    role=CollaborationSpaceUserMembership.Role.OWNER,
                    invited_by=reviewer,
                    joined_at=timezone.now(),
                )
                if self.requested_by_org:
                    CollaborationSpaceOrganizationMembership.objects.create(
                        space=space,
                        organization=self.requested_by_org,
                        role=CollaborationSpaceOrganizationMembership.Role.MEMBER,
                        invited_by=reviewer,
                    )
            return space

    def decline(self, reviewer, admin_notes=""):
        self.status = self.Status.DECLINED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.admin_notes = admin_notes
        self.save(update_fields=["status", "reviewed_by", "reviewed_at", "admin_notes", "updated_at"])


class CollaborationSpaceQuerySet(models.QuerySet):
    def visible_to(self, user):
        if not user.is_authenticated:
            return self.none()

        if user.is_staff or user.is_superuser:
            return self.all()

        organization_ids = user.organizations.values_list("id", flat=True)
        return (
            self.filter(
                Q(created_by=user)
                | Q(owner=user)
                | Q(moderator=user)
                | Q(
                    user_memberships__user=user,
                    user_memberships__left_at__isnull=True,
                    user_memberships__role__in=CollaborationMembershipBase.view_roles(),
                )
                | Q(
                    organization_memberships__organization_id__in=organization_ids,
                    organization_memberships__left_at__isnull=True,
                    organization_memberships__role__in=CollaborationMembershipBase.view_roles(),
                )
                | Q(visibility_level=CollaborationSpace.VisibilityLevel.APPROVED_MEMBERS)
            )
            .distinct()
            .order_by("-last_activity_at", "title")
        )


class CollaborationSpace(models.Model):
    class VisibilityLevel(models.TextChoices):
        ADMIN_ONLY = "admin_only", "Admin only"
        INVITE_ONLY = "invite_only", "Invite only"
        APPROVED_MEMBERS = "approved_members", "Approved members"
        REGION_ONLY = "region_only", "Region only"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    purpose = models.TextField()
    topic_category = models.CharField(
        max_length=50,
        choices=CollaborationSpaceRequest.TopicCategory.choices,
        default=CollaborationSpaceRequest.TopicCategory.OTHER,
    )
    region = models.CharField(max_length=100, blank=True)
    municipality = models.CharField(max_length=100, blank=True)
    visibility_level = models.CharField(
        max_length=50,
        choices=VisibilityLevel.choices,
        default=VisibilityLevel.INVITE_ONLY,
    )
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.DRAFT)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="owned_collaboration_spaces",
        on_delete=models.PROTECT,
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="moderated_collaboration_spaces",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_collaboration_spaces",
        on_delete=models.PROTECT,
    )
    created_from_request = models.OneToOneField(
        CollaborationSpaceRequest,
        related_name="space",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    last_activity_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CollaborationSpaceQuerySet.as_manager()

    class Meta:
        ordering = ["-last_activity_at", "title"]

    def __str__(self):
        return self.title

    def can_view(self, user):
        return CollaborationSpace.objects.visible_to(user).filter(pk=self.pk).exists()

    def can_post(self, user):
        if not user.is_authenticated or self.status != self.Status.ACTIVE:
            return False

        if user.is_staff or user.is_superuser:
            return True

        direct_membership_can_post = self.user_memberships.filter(
            user=user,
            left_at__isnull=True,
            role__in=CollaborationMembershipBase.post_roles(),
        ).exists()
        organization_membership_can_post = self.organization_memberships.filter(
            organization_id__in=user.organizations.values_list("id", flat=True),
            left_at__isnull=True,
            role__in=CollaborationMembershipBase.post_roles(),
        ).exists()
        return direct_membership_can_post or organization_membership_can_post


class CollaborationMembershipBase(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MODERATOR = "moderator", "Moderator"
        MEMBER = "member", "Member"
        READONLY = "readonly", "Read only"

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.MEMBER)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="%(class)s_invitations_sent",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @classmethod
    def view_roles(cls):
        return [cls.Role.OWNER, cls.Role.MODERATOR, cls.Role.MEMBER, cls.Role.READONLY]

    @classmethod
    def post_roles(cls):
        return [cls.Role.OWNER, cls.Role.MODERATOR, cls.Role.MEMBER]


class CollaborationSpaceUserMembership(CollaborationMembershipBase):
    space = models.ForeignKey(CollaborationSpace, related_name="user_memberships", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="collaboration_space_memberships",
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ("space", "user")
        ordering = ["space", "user"]

    def __str__(self):
        return f"{self.user} in {self.space}"


class CollaborationSpaceOrganizationMembership(CollaborationMembershipBase):
    space = models.ForeignKey(CollaborationSpace, related_name="organization_memberships", on_delete=models.CASCADE)
    organization = models.ForeignKey(
        Organization,
        related_name="collaboration_space_memberships",
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ("space", "organization")
        ordering = ["space", "organization"]

    def __str__(self):
        return f"{self.organization} in {self.space}"


class CollaborationLinkedObject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    space = models.ForeignKey(CollaborationSpace, related_name="linked_objects", on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey("content_type", "object_id")
    label = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="collaboration_links",
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["label"]

    def __str__(self):
        return self.label


class CollaborationChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    space = models.ForeignKey(CollaborationSpace, related_name="chat_messages", on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="collaboration_chat_messages",
        on_delete=models.PROTECT,
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Chat message by {self.author} in {self.space}"


def collaboration_file_upload_to(instance, filename):
    ext = Path(filename).suffix.lower()
    return f"collaborations/{instance.space_id}/files/{instance.id}{ext}"


class CollaborationFile(models.Model):
    class ScanStatus(models.TextChoices):
        PENDING = "pending", "Pending scan"
        SCANNING = "scanning", "Scanning"
        CLEAN = "clean", "Clean"
        INFECTED = "infected", "Infected"
        FAILED = "failed", "Scan failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    space = models.ForeignKey(CollaborationSpace, related_name="files", on_delete=models.CASCADE)
    file = models.FileField(upload_to=collaboration_file_upload_to, max_length=255)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField()
    scan_status = models.CharField(
        max_length=20,
        choices=ScanStatus.choices,
        default=ScanStatus.PENDING,
        db_index=True,
    )
    scan_result = models.CharField(max_length=255, blank=True)
    scan_error = models.TextField(blank=True)
    scan_attempts = models.PositiveSmallIntegerField(default=0)
    scan_started_at = models.DateTimeField(null=True, blank=True)
    scanned_at = models.DateTimeField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="uploaded_collaboration_files",
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "original_filename"]

    def __str__(self):
        return self.original_filename
