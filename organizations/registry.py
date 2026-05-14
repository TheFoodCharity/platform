from typing import TypedDict

import rules


class _RegistryEntry(TypedDict):
    description: str
    roles: list[str]
    capabilities: list[str]


_registry: dict[str, _RegistryEntry] = {}


def register_permission(
    code: str,
    description: str,
    *,
    rule,
    roles: list[str] | None = None,
    capabilities: list[str] | None = None,
) -> None:
    """Register a permission's predicate and its human-readable description in one call.

    Wraps rules.add_perm(code, rule) and records the description for the catalog sync
    and admin display. All permission declarations must go through this function — calling
    rules.add_perm() directly bypasses the registry and will fail the organizations.E001
    system check.

    ``roles`` lists SystemRole values that should receive this permission by default.
    ``capabilities`` lists SystemCapability values that should receive it by default.
    Both are used by ``makepermissionsmigration`` to generate the group assignment block
    in the migration — nothing reads them at runtime.
    """
    if code in _registry:
        raise RuntimeError(f"Permission {code!r} is already registered")
    _registry[code] = {
        "description": description,
        "roles": list(roles or []),
        "capabilities": list(capabilities or []),
    }
    rules.add_perm(code, rule)


def registered_permissions() -> dict[str, "_RegistryEntry"]:
    return _registry
