import rules
from django.core.checks import Error, Tags, Warning, register

from .registry import registered_permissions


@register(Tags.compatibility)
def check_permission_registry_consistency(app_configs, **kwargs):
    """E001: every code registered via rules.add_perm exists in registered_permissions().

    Catches stray rules.add_perm() calls that bypass register_permission() and would
    therefore have no description, no DB row, and no coverage in the sync check.
    """
    errors = []
    registered = set(registered_permissions())
    rules_keys = set(rules.permissions.permissions.keys())

    for code in sorted(rules_keys - registered):
        errors.append(
            Error(
                f"Permission {code!r} is registered in django-rules but was not registered "
                "via register_permission(). Use register_permission() instead of rules.add_perm() directly.",
                id="organizations.E001",
            )
        )
    return errors


@register(Tags.compatibility, Tags.database)
def check_permission_db_sync(app_configs, databases=None, **kwargs):
    """E002/W001: registered_permissions() and the Permission table must contain identical codes.

    Runs only when a DB connection is available. Skipped silently otherwise (e.g. in CI
    without a database). Run manage.py check --database default to force the DB check.
    """
    if databases is None:
        return []

    from django.db import DatabaseError

    from .models import Permission

    errors = []

    registered = set(registered_permissions())
    try:
        db_codes = set(Permission.objects.values_list("code", flat=True))
    except DatabaseError:
        return []

    for code in sorted(registered - db_codes):
        errors.append(
            Warning(
                f"Permission {code!r} is registered but has no corresponding Permission row. Run migrate to sync.",
                id="organizations.W001",
            )
        )
    for code in sorted(db_codes - registered):
        errors.append(
            Error(
                f"Permission {code!r} exists in the database but is not registered. "
                "Register it via register_permission() or remove the database row.",
                id="organizations.E002",
            )
        )

    return errors
