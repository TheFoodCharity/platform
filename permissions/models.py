from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import Scope  # noqa: TID251


class Permission(models.Model):
    code = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ("code",)
        verbose_name = _("permission")
        verbose_name_plural = _("permissions")

    def __str__(self):
        return self.code


class PermissionGroup(models.Model):
    name = models.CharField(max_length=100)
    scope = models.PositiveSmallIntegerField(choices=Scope.choices)
    description = models.CharField(max_length=500, blank=True)
    permissions = models.ManyToManyField(Permission, related_name="groups", blank=True)
    is_system = models.BooleanField(default=False)

    class Meta:
        unique_together = ("name", "scope")
        ordering = ("scope", "name")
        verbose_name = _("permission group")
        verbose_name_plural = _("permission groups")

    def __str__(self):
        return f"{self.name} ({self.get_scope_display()})"


class PermissionOverrideBase(models.Model):
    class Effect(models.IntegerChoices):
        ALLOW = 1
        DENY = 2

    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    effect = models.PositiveSmallIntegerField(choices=Effect.choices)

    class Meta:
        abstract = True


class OrganizationPermissionOverride(PermissionOverrideBase):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="permission_overrides",
    )

    class Meta:
        unique_together = ("organization", "permission")
        verbose_name = _("organization permission override")
        verbose_name_plural = _("organization permission overrides")

    def __str__(self):
        return f"{self.organization}: {self.permission.code} ({self.get_effect_display()})"


class MembershipPermissionOverride(PermissionOverrideBase):
    membership = models.ForeignKey(
        "organizations.Membership",
        on_delete=models.CASCADE,
        related_name="permission_overrides",
    )

    class Meta:
        unique_together = ("membership", "permission")
        verbose_name = _("membership permission override")
        verbose_name_plural = _("membership permission overrides")

    def __str__(self):
        return f"{self.membership}: {self.permission.code} ({self.get_effect_display()})"
