from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group as AuthGroup  # noqa: TID251
from django.db import models
from django.utils.translation import gettext_lazy as _
from organizations.abstract import (
    AbstractOrganization,
    AbstractOrganizationInvitation,
    AbstractOrganizationOwner,
    AbstractOrganizationUser,
)
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


class Organization(AbstractOrganization):
    class Status(models.IntegerChoices):
        PENDING = 0, "Pending"
        APPROVED = 1, "Approved"
        APPROVED_LIMITED = 2, "Approved with limited access"
        NEEDS_INFO = 3, "Needs more information"
        DECLINED = 4, "Declined"
        ARCHIVED = 5, "Archived"

    status = models.PositiveSmallIntegerField(choices=Status.choices, default=Status.PENDING, null=False)

    email = models.EmailField(blank=True)
    phone = PhoneNumberField(blank=True)
    website = models.URLField(blank=True)

    @classmethod
    def create(cls, name: str, owner: User) -> "Organization":
        organization = cls.objects.create(name=name, is_active=False)
        membership = Membership.objects.create(organization=organization, user=owner)
        OrganizationOwner.objects.create(organization=organization, organization_user=membership)

        return organization


class Membership(AbstractOrganizationUser):
    class Meta:
        verbose_name = _("membership")
        verbose_name_plural = _("memberships")


class OrganizationOwner(AbstractOrganizationOwner):
    pass


class Invitation(AbstractOrganizationInvitation):
    pass
