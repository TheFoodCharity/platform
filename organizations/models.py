import uuid
from typing import TYPE_CHECKING, Literal

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

if TYPE_CHECKING:
    from accounts.models import User


class TimestampedModel(models.Model):
    created = models.DateTimeField(default=timezone.now, editable=False)
    modified = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.modified = timezone.now()
        super().save(*args, **kwargs)


class OrganizationType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("organization type")
        verbose_name_plural = _("organization types")

    def __str__(self):
        return self.name


class LegalStatus(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("legal status")
        verbose_name_plural = _("legal statuses")

    def __str__(self):
        return self.name


class Organization(TimestampedModel):
    class Status(models.IntegerChoices):
        DRAFT = 0, "Draft"
        PENDING = 1, "Pending"
        APPROVED = 2, "Approved"
        APPROVED_LIMITED = 3, "Approved with limited access"
        NEEDS_INFO = 4, "Needs more information"
        DECLINED = 5, "Declined"
        ARCHIVED = 6, "Archived"

    # Core identity
    name = models.CharField(max_length=200, help_text=_("The name of the organization"))
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="owned_organizations",
        on_delete=models.PROTECT,
        help_text=_("Primary internal contact responsible for membership, onboarding, and operational communication"),
    )
    status = models.PositiveSmallIntegerField(choices=Status, default=Status.DRAFT, null=False)
    organization_type = models.ForeignKey(
        OrganizationType,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_("organization type"),
    )
    legal_status = models.ForeignKey(
        LegalStatus,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_("legal / organizational status"),
    )
    description = models.TextField(blank=True, help_text=_("Brief organization description"))
    interest_areas = models.TextField(blank=True, help_text=_("Main interest areas and project interests"))

    # Location
    municipality = models.CharField(max_length=200, blank=True)
    region = models.CharField(max_length=200, blank=True)
    service_area = models.TextField(blank=True, help_text=_("Geographic or community area the organization serves"))

    # Public-facing contact (shown to the public for organizations that provide direct public support)
    email = models.EmailField(blank=True, help_text=_("Public-facing contact email"))
    phone = PhoneNumberField(blank=True, help_text=_("Public-facing contact phone"))
    website = models.URLField(blank=True, help_text=_("Public-facing website"))

    # Operational profile (§4.5)
    contact_via_email = models.BooleanField(default=False)
    contact_via_phone = models.BooleanField(default=False)
    internal_notes = models.TextField(blank=True)
    is_publicly_visible = models.BooleanField(
        default=False,
        help_text=_("Whether this organization may appear on public maps or directories"),
    )

    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Membership", related_name="organizations")

    class Meta:
        ordering = ["name"]
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")

    def __str__(self):
        return self.name

    def is_member(self, user: "User") -> bool:
        return self.users.filter(pk=user.pk).exists()

    def is_approved(self) -> bool:
        return self.status in (self.Status.APPROVED, self.Status.APPROVED_LIMITED)

    def is_editable(self) -> bool:
        return self.status not in (self.Status.DECLINED, self.Status.ARCHIVED)

    def submit(self):
        if self.status in (self.Status.DRAFT, self.Status.NEEDS_INFO):
            self.status = self.Status.PENDING
            self.save(update_fields=["status"])

    @classmethod
    def create(cls, name: str, owner: "User") -> "Organization":
        with transaction.atomic():
            organization = cls.objects.create(name=name, is_active=False, owner=owner, status=cls.Status.DRAFT)
            Membership.objects.create(organization=organization, user=owner)
            OrganizationApplication.objects.create(organization=organization)
        return organization


class OrganizationApplication(TimestampedModel):
    organization = models.OneToOneField(Organization, related_name="application", on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(null=True, blank=True)

    # Form segment statuses
    basics_last_updated = models.DateTimeField(null=True, blank=True)
    location_last_updated = models.DateTimeField(null=True, blank=True)
    contact_last_updated = models.DateTimeField(null=True, blank=True)
    operations_last_updated = models.DateTimeField(null=True, blank=True)

    # §4.1 — automated review notice acknowledgement.
    # acknowledged_by mirrors Organization.owner at the time of acknowledgement but is preserved
    # in case ownership changes later.
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="application_acknowledgements",
        on_delete=models.PROTECT,
    )

    # Admin review
    admin_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="reviewed_applications",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = _("organization application")
        verbose_name_plural = _("organization applications")

    def __str__(self):
        return str(self.organization)

    def mark_section_updated(self, section: Literal["basics", "location", "contact", "operations"]):
        field = f"{section}_last_updated"
        setattr(self, field, timezone.now())
        self.save(update_fields=[field])

    def submit(self, by: "User"):
        now = timezone.now()
        self.submitted_at = now
        update_fields = ["submitted_at"]
        if not self.acknowledged_at:
            self.acknowledged_at = now
            self.acknowledged_by = by
            update_fields += ["acknowledged_at", "acknowledged_by"]
        self.save(update_fields=update_fields)


class Membership(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="memberships", on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, related_name="memberships", on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("membership")
        verbose_name_plural = _("memberships")
        ordering = ["organization", "user"]
        unique_together = ("user", "organization")

    def __str__(self):
        return f"{self.user} ({self.organization.name})"


class Invitation(TimestampedModel):
    guid = models.UUIDField(editable=False)
    invitee_identifier = models.CharField(
        max_length=1000,
        help_text=_("The contact identifier for the invitee, email, phone number, social media handle, etc."),
    )
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="sent_invitations", on_delete=models.CASCADE)
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="received_invitations",
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(Organization, related_name="invitations", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.organization}: {self.invitee_identifier}"

    def save(self, **kwargs):
        if not self.guid:
            self.guid = uuid.uuid4()
        super().save(**kwargs)
