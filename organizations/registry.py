import rules

_descriptions: dict[str, str] = {}


def register_permission(code: str, description: str, *, rule) -> None:
    """Register a permission's predicate and its human-readable description in one call.

    Wraps rules.add_perm(code, rule) and records the description for the catalog sync
    and admin display. All permission declarations must go through this function — calling
    rules.add_perm() directly bypasses the registry and will fail the organizations.E001
    system check.
    """
    if code in _descriptions:
        raise RuntimeError(f"Permission {code!r} is already registered")
    _descriptions[code] = description
    rules.add_perm(code, rule)


def registered_permissions() -> dict[str, str]:
    return dict(_descriptions)
