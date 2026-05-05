from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group as AuthGroup  # noqa: TID251
from django.utils.translation import gettext_lazy as _
from organizations.abstract import (
    AbstractOrganization,
    AbstractOrganizationInvitation,
    AbstractOrganizationOwner,
    AbstractOrganizationUser,
)


class User(AbstractUser):
    pass


class Group(AuthGroup):
    class Meta:
        proxy = True


class Organization(AbstractOrganization):
    pass


class Membership(AbstractOrganizationUser):
    class Meta:
        verbose_name = _("membership")
        verbose_name_plural = _("memberships")


class OrganizationOwner(AbstractOrganizationOwner):
    pass


class Invitation(AbstractOrganizationInvitation):
    pass
