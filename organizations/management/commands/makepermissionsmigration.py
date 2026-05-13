import re
from pathlib import Path

from django.core.management.base import BaseCommand

from organizations.constants import Scope, SystemCapability, SystemRole
from organizations.registry import registered_group_assignments, registered_permissions

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"

# Reverse maps: string value -> attribute name, for both constants classes.
_ROLE_ATTR = {v: k for k, v in vars(SystemRole).items() if not k.startswith("_")}
_CAP_ATTR = {v: k for k, v in vars(SystemCapability).items() if not k.startswith("_")}
_SCOPE_ATTR = {v: k for k, v in vars(Scope).items() if not k.startswith("_") and isinstance(v, int)}


def _already_migrated_codes(registered: dict[str, str]) -> set[str]:
    found = set()
    for path in MIGRATIONS_DIR.glob("*.py"):
        content = path.read_text()
        for code in registered:
            if f'"{code}"' in content or f"'{code}'" in content:
                found.add(code)
    return found


def _last_migration() -> str:
    numbers = {}
    for path in MIGRATIONS_DIR.glob("*.py"):
        m = re.match(r"^(\d+)_(.+)\.py$", path.name)
        if m:
            numbers[int(m.group(1))] = path.stem
    if not numbers:
        raise RuntimeError("No existing migrations found in organizations/migrations/.")
    return numbers[max(numbers)]


def _next_migration_number() -> int:
    numbers = [int(m.group(1)) for path in MIGRATIONS_DIR.glob("*.py") if (m := re.match(r"^(\d+)_", path.name))]
    return max(numbers) + 1 if numbers else 1


def _build_assignments(new_codes: dict[str, str]) -> tuple[dict, dict]:
    """Return (role_to_codes, cap_to_codes) dicts for the new permissions."""
    assignments = registered_group_assignments()
    role_to_codes: dict[str, list[str]] = {}
    cap_to_codes: dict[str, list[str]] = {}
    for code in new_codes:
        for role in assignments[code]["roles"]:
            role_to_codes.setdefault(role, []).append(code)
        for cap in assignments[code]["capabilities"]:
            cap_to_codes.setdefault(cap, []).append(code)
    return role_to_codes, cap_to_codes


def _render_assignment_block(role_to_codes: dict, cap_to_codes: dict) -> str:
    lines = []

    if role_to_codes:
        lines.append("    role_assignments = {")
        for role, codes in role_to_codes.items():
            attr = _ROLE_ATTR.get(role)
            key = f"SystemRole.{attr}" if attr else f'"{role}"'
            code_list = ", ".join(f'"{c}"' for c in codes)
            lines.append(f"        {key}: [{code_list}],")
        lines.append("    }")
        lines.append("    for role_name, codes in role_assignments.items():")
        lines.append("        group = PermissionGroup.objects.get(name=role_name, scope=Scope.USER)")
        lines.append("        group.permissions.add(*Permission.objects.filter(code__in=codes))")

    if cap_to_codes:
        if lines:
            lines.append("")
        lines.append("    cap_assignments = {")
        for cap, codes in cap_to_codes.items():
            attr = _CAP_ATTR.get(cap)
            key = f"SystemCapability.{attr}" if attr else f'"{cap}"'
            code_list = ", ".join(f'"{c}"' for c in codes)
            lines.append(f"        {key}: [{code_list}],")
        lines.append("    }")
        lines.append("    for cap_name, codes in cap_assignments.items():")
        lines.append("        group = PermissionGroup.objects.get(name=cap_name, scope=Scope.ORGANIZATION)")
        lines.append("        group.permissions.add(*Permission.objects.filter(code__in=codes))")

    return "\n".join(lines)


def _render_imports(role_to_codes: dict, cap_to_codes: dict) -> str:
    parts = ["Scope"]
    if role_to_codes:
        parts.append("SystemRole")
    if cap_to_codes:
        parts.append("SystemCapability")
    return f"from organizations.constants import {', '.join(parts)}"


def _render_migration(
    new_codes: dict[str, str],
    role_to_codes: dict,
    cap_to_codes: dict,
    last: str,
) -> str:
    perms_lines = "\n".join(f'    ("{code}", "{desc}"),' for code, desc in new_codes.items())
    filter_list = ", ".join(f'"{code}"' for code in new_codes)
    constants_import = _render_imports(role_to_codes, cap_to_codes)
    assignment_block = _render_assignment_block(role_to_codes, cap_to_codes)

    has_groups = bool(role_to_codes or cap_to_codes)
    group_model = "    PermissionGroup = apps.get_model('organizations', 'PermissionGroup')\n" if has_groups else ""

    return f"""\
from django.db import migrations

{constants_import}

PERMISSIONS = [
{perms_lines}
]


def add_permissions(apps, schema_editor):
    Permission = apps.get_model("organizations", "Permission")
{group_model}
    for code, description in PERMISSIONS:
        Permission.objects.update_or_create(code=code, defaults={{"description": description}})

{assignment_block}


def remove_permissions(apps, schema_editor):
    Permission = apps.get_model("organizations", "Permission")
    Permission.objects.filter(code__in=[{filter_list}]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "{last}"),
    ]

    operations = [
        migrations.RunPython(add_permissions, reverse_code=remove_permissions),
    ]
"""


class Command(BaseCommand):
    help = "Generate a data migration for any newly registered permissions."

    def handle(self, *args, **options):
        registered = registered_permissions()
        already = _already_migrated_codes(registered)
        new_codes = {code: desc for code, desc in registered.items() if code not in already}

        if not new_codes:
            self.stdout.write("No new permissions — nothing to generate.")
            return

        role_to_codes, cap_to_codes = _build_assignments(new_codes)
        last = _last_migration()
        next_num = _next_migration_number()
        apps = list(dict.fromkeys(c.split(".")[0] for c in new_codes))[:3]
        name = f"{next_num:04d}_permissions_{'_'.join(apps)}"
        path = MIGRATIONS_DIR / f"{name}.py"

        path.write_text(_render_migration(new_codes, role_to_codes, cap_to_codes, last))

        self.stdout.write(self.style.SUCCESS(f"Created {path.name}"))
        self.stdout.write("Review the migration, then run migrate.")
