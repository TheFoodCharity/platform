import uuid
from typing import TYPE_CHECKING

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


class Organization(TimestampedModel):
    class Status(models.IntegerChoices):
        PENDING = 0, "Pending"
        APPROVED = 1, "Approved"
        APPROVED_LIMITED = 2, "Approved with limited access"
        NEEDS_INFO = 3, "Needs more information"
        DECLINED = 4, "Declined"
        ARCHIVED = 5, "Archived"

    name = models.CharField(max_length=200, help_text=_("The name of the organization"))
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="owned_organizations", on_delete=models.PROTECT)
    status = models.PositiveSmallIntegerField(choices=Status, default=Status.PENDING, null=False)

    email = models.EmailField(blank=True)
    phone = PhoneNumberField(blank=True)
    website = models.URLField(blank=True)

    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Membership", related_name="organizations")

    class Meta:
        ordering = ["name"]
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")

    def __str__(self):
        return self.name

    def is_member(self, user: "User") -> bool:
        return self.users.filter(pk=user.pk).exists()

    @classmethod
    def create(cls, name: str, owner: "User") -> "Organization":
        with transaction.atomic():
            organization = cls.objects.create(name=name, is_active=False, owner=owner)
            Membership.objects.create(organization=organization, user=owner)
        return organization


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
