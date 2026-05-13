from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _sync_permissions(sender, **kwargs):
    """Sync the Permission table with the in-memory registry after every migration run."""
    from .models import Permission
    from .registry import registered_permissions

    registered = registered_permissions()

    for code, description in registered.items():
        Permission.objects.update_or_create(code=code, defaults={"description": description})

    stale_codes = set(Permission.objects.values_list("code", flat=True)) - set(registered)
    if stale_codes:
        still_referenced = set(
            Permission.objects.filter(
                code__in=stale_codes,
            )
            .filter(
                groups__isnull=False,
            )
            .values_list("code", flat=True)
        )
        if still_referenced:
            import warnings

            warnings.warn(
                f"The following permission codes are no longer registered but are still referenced "
                f"by PermissionGroups and cannot be removed automatically: {sorted(still_referenced)}. "
                "Remove them from their groups and re-run migrations.",
                stacklevel=2,
            )
            stale_codes -= still_referenced

        if stale_codes:
            Permission.objects.filter(code__in=stale_codes).delete()


class OrganizationsConfig(AppConfig):
    name = "organizations"

    def ready(self):
        from . import checks  # noqa: F401 — registers system checks

        post_migrate.connect(_sync_permissions, sender=self)
