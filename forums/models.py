import uuid

from django.conf import settings
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from organizations.models import Organization


def approved_member_organizations(user):
    if not user.is_authenticated:
        return Organization.objects.none()

    return user.organizations.filter(
        is_active=True,
        status__in=[
            Organization.Status.APPROVED,
            Organization.Status.APPROVED_LIMITED,
        ],
    )


def can_request_forum(user):
    return user.is_authenticated and (
        user.is_staff or user.is_superuser or approved_member_organizations(user).exists()
    )


class ForumSpaceRequest(models.Model):
    class TopicCategory(models.TextChoices):
        GENERAL = "general", "General discussion"
        REGIONAL = "regional", "Regional discussion"
        FOOD_SUPPLY = "food_supply", "Food supply"
        STORAGE = "storage", "Storage"
        TRANSPORTATION = "transportation", "Transportation"
        FUNDING = "funding", "Funding"
        ADVOCACY = "advocacy", "Advocacy"
        EDUCATION = "education", "Education / training"
        EMERGENCY_RESPONSE = "emergency_response", "Emergency response"
        WORKING_GROUP = "working_group", "Working group"
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
        related_name="forum_space_requests",
        on_delete=models.PROTECT,
    )
    requested_by_org = models.ForeignKey(
        Organization,
        related_name="forum_space_requests",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="reviewed_forum_space_requests",
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

            space, created = ForumSpace.objects.get_or_create(
                created_from_request=self,
                defaults={
                    "title": self.title,
                    "description": self.purpose,
                    "topic_category": self.topic_category,
                    "region": self.region,
                    "municipality": self.municipality,
                    "visibility_level": self.visibility_preference,
                    "status": ForumSpace.Status.ACTIVE,
                    "owner": self.requested_by_user,
                    "created_by": reviewer,
                    "last_activity_at": timezone.now(),
                },
            )
            if created:
                ForumSpaceUserMembership.objects.create(
                    space=space,
                    user=self.requested_by_user,
                    role=ForumSpaceUserMembership.Role.OWNER,
                    invited_by=reviewer,
                    joined_at=timezone.now(),
                )
                if self.requested_by_org:
                    ForumSpaceOrganizationMembership.objects.create(
                        space=space,
                        organization=self.requested_by_org,
                        role=ForumSpaceOrganizationMembership.Role.MEMBER,
                        invited_by=reviewer,
                    )
            return space

    def decline(self, reviewer, admin_notes=""):
        self.status = self.Status.DECLINED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.admin_notes = admin_notes
        self.save(update_fields=["status", "reviewed_by", "reviewed_at", "admin_notes", "updated_at"])


class ForumSpaceQuerySet(models.QuerySet):
    def visible_to(self, user):
        if not user.is_authenticated:
            return self.none()

        if user.is_staff or user.is_superuser:
            return self.all()

        organization_ids = user.organizations.values_list("id", flat=True)
        approved_organizations = approved_member_organizations(user)
        approved_regions = approved_organizations.exclude(region="").values_list("region", flat=True)

        approved_member_filter = Q(pk__in=[])
        region_filter = Q(pk__in=[])
        if approved_organizations.exists():
            approved_member_filter = Q(visibility_level=ForumSpace.VisibilityLevel.APPROVED_MEMBERS)
        if approved_regions.exists():
            region_filter = Q(visibility_level=ForumSpace.VisibilityLevel.REGION_ONLY, region__in=approved_regions)

        return (
            self.filter(
                Q(created_by=user)
                | Q(owner=user)
                | Q(moderator=user)
                | Q(
                    user_memberships__user=user,
                    user_memberships__left_at__isnull=True,
                    user_memberships__role__in=ForumMembershipBase.view_roles(),
                )
                | Q(
                    organization_memberships__organization_id__in=organization_ids,
                    organization_memberships__left_at__isnull=True,
                    organization_memberships__role__in=ForumMembershipBase.view_roles(),
                )
                | approved_member_filter
                | region_filter
            )
            .distinct()
            .order_by("-last_activity_at", "title")
        )


class ForumSpace(models.Model):
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
    description = models.TextField()
    topic_category = models.CharField(
        max_length=50,
        choices=ForumSpaceRequest.TopicCategory.choices,
        default=ForumSpaceRequest.TopicCategory.OTHER,
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
        related_name="owned_forum_spaces",
        on_delete=models.PROTECT,
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="moderated_forum_spaces",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_forum_spaces",
        on_delete=models.PROTECT,
    )
    created_from_request = models.OneToOneField(
        ForumSpaceRequest,
        related_name="space",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    last_activity_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ForumSpaceQuerySet.as_manager()

    class Meta:
        ordering = ["-last_activity_at", "title"]

    def __str__(self):
        return self.title

    def can_view(self, user):
        return ForumSpace.objects.visible_to(user).filter(pk=self.pk).exists()

    def can_post(self, user):
        if not user.is_authenticated or self.status != self.Status.ACTIVE:
            return False

        if user.is_staff or user.is_superuser:
            return True

        direct_membership_can_post = self.user_memberships.filter(
            user=user,
            left_at__isnull=True,
            role__in=ForumMembershipBase.post_roles(),
        ).exists()
        organization_membership_can_post = self.organization_memberships.filter(
            organization_id__in=user.organizations.values_list("id", flat=True),
            left_at__isnull=True,
            role__in=ForumMembershipBase.post_roles(),
        ).exists()
        approved_member_can_post = (
            self.visibility_level == self.VisibilityLevel.APPROVED_MEMBERS
            and approved_member_organizations(user).exists()
        )
        region_member_can_post = (
            self.visibility_level == self.VisibilityLevel.REGION_ONLY
            and bool(self.region)
            and approved_member_organizations(user).filter(region=self.region).exists()
        )
        return (
            direct_membership_can_post
            or organization_membership_can_post
            or approved_member_can_post
            or region_member_can_post
        )


class ForumMembershipBase(models.Model):
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


class ForumSpaceUserMembership(ForumMembershipBase):
    space = models.ForeignKey(ForumSpace, related_name="user_memberships", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="forum_space_memberships",
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ("space", "user")
        ordering = ["space", "user"]

    def __str__(self):
        return f"{self.user} in {self.space}"


class ForumSpaceOrganizationMembership(ForumMembershipBase):
    space = models.ForeignKey(ForumSpace, related_name="organization_memberships", on_delete=models.CASCADE)
    organization = models.ForeignKey(
        Organization,
        related_name="forum_space_memberships",
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ("space", "organization")
        ordering = ["space", "organization"]

    def __str__(self):
        return f"{self.organization} in {self.space}"
