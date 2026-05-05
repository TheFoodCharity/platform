import uuid

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group as AuthGroup  # noqa: TID251
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField
from phonenumber_field.modelfields import PhoneNumberField


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields) -> "User":
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user: User = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()


class Group(AuthGroup):
    class Meta:
        proxy = True


class _TimestampedModel(models.Model):
    created = models.DateTimeField(default=timezone.now, editable=False)
    modified = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.modified = timezone.now()
        super().save(*args, **kwargs)


class Organization(_TimestampedModel):
    class Status(models.IntegerChoices):
        PENDING = 0, "Pending"
        APPROVED = 1, "Approved"
        APPROVED_LIMITED = 2, "Approved with limited access"
        NEEDS_INFO = 3, "Needs more information"
        DECLINED = 4, "Declined"
        ARCHIVED = 5, "Archived"

    name = models.CharField(max_length=200, help_text=_("The name of the organization"))
    is_active = models.BooleanField(default=True)
    slug = AutoSlugField(
        max_length=200,
        blank=True,
        editable=False,
        populate_from="name",
        unique=True,
        help_text=_("The name in all lowercase, suitable for URL identification"),
    )
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Membership", related_name="accounts_organization")
    status = models.PositiveSmallIntegerField(choices=Status, default=Status.PENDING, null=False)
    email = models.EmailField(blank=True)
    phone = PhoneNumberField(blank=True)
    website = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")

    def __str__(self):
        return self.name

    def is_member(self, user: "User") -> bool:
        return user in self.users.all()

    @classmethod
    def create(cls, name: str, owner: "User") -> "Organization":
        organization = cls.objects.create(name=name, is_active=False)
        membership = Membership.objects.create(organization=organization, user=owner)
        OrganizationOwner.objects.create(organization=organization, organization_user=membership)
        return organization


class Membership(_TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="accounts_membership", on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, related_name="organization_users", on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("membership")
        verbose_name_plural = _("memberships")
        ordering = ["organization", "user"]
        unique_together = ("user", "organization")

    def __str__(self):
        return f"{self.user} ({self.organization.name})"


class OrganizationOwner(_TimestampedModel):
    organization = models.OneToOneField(Organization, related_name="owner", on_delete=models.CASCADE)
    organization_user = models.OneToOneField(Membership, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("organization owner")
        verbose_name_plural = _("organization owners")

    def __str__(self):
        return f"{self.organization}: {self.organization_user}"

    def save(self, *args, **kwargs):
        if self.organization_user.organization_id != self.organization_id:
            raise ValueError("Organization user does not belong to this organization")
        super().save(*args, **kwargs)


class Invitation(_TimestampedModel):
    guid = models.UUIDField(editable=False)
    invitee_identifier = models.CharField(
        max_length=1000,
        help_text=_("The contact identifier for the invitee, email, phone number, social media handle, etc."),
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="accounts_invitation_sent_invitations", on_delete=models.CASCADE
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="accounts_invitation_invitations",
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(Organization, related_name="organization_invites", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.organization}: {self.invitee_identifier}"

    def save(self, **kwargs):
        if not self.guid:
            self.guid = uuid.uuid4()
        super().save(**kwargs)
