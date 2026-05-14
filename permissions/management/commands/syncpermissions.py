import re
from pathlib import Path

from django.core.management.base import BaseCommand

from permissions.constants import Scope, SystemCapability, SystemRole
from permissions.registry import registered_permissions

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"

_ROLE_ATTR = {v: k for k, v in vars(SystemRole).items() if not k.startswith("_")}
_CAP_ATTR = {v: k for k, v in vars(SystemCapability).items() if not k.startswith("_")}


def _last_migration():
    numbers = {}
    for path in MIGRATIONS_DIR.glob("*.py"):
        m = re.match(r"^(\d+)_(.+)\.py$", path.name)
        if m:
            numbers[int(m.group(1))] = path.stem
    if not numbers:
        raise RuntimeError("No existing migrations found in organizations/migrations/.")
    return numbers[max(numbers)]


def _next_migration_number():
    numbers = [int(m.group(1)) for path in MIGRATIONS_DIR.glob("*.py") if (m := re.match(r"^(\d+)_", path.name))]
    return max(numbers) + 1 if numbers else 1


def _const_list(items, attr_map, prefix):
    if not items:
        return "[]"
    parts = [f"{prefix}.{attr_map[v]}" if v in attr_map else f'"{v}"' for v in items]
    return f"[{', '.join(parts)}]"


def _render_perm_list(varname, entries):
    lines = [f"{varname} = ["]
    for code, entry in entries.items():
        roles = _const_list(entry["roles"], _ROLE_ATTR, "SystemRole")
        caps = _const_list(entry["capabilities"], _CAP_ATTR, "SystemCapability")
        lines.append(f'    ("{code}", "{entry["description"]}", {roles}, {caps}),')
    lines.append("]")
    return "\n".join(lines)


def _render_delete(varname):
    return f"    Permission.objects.filter(code__in=[code for code, *_ in {varname}]).delete()"


def _render_add(varname, has_roles, has_caps):
    loop_var = "code, description, roles, capabilities" if (has_roles or has_caps) else "code, description, *_"
    lines = [
        f"    for {loop_var} in {varname}:",
        '        perm, _ = Permission.objects.update_or_create(code=code, defaults={"description": description})',
    ]
    if has_roles:
        lines += [
            "        for role in roles:",
            "            PermissionGroup.objects.get(name=role, scope=Scope.USER).permissions.add(perm)",
        ]
    if has_caps:
        lines += [
            "        for cap in capabilities:",
            "            PermissionGroup.objects.get(name=cap, scope=Scope.ORGANIZATION).permissions.add(perm)",
        ]
    return "\n".join(lines)


def _render_step(name, delete_vars, add_vars, has_roles, has_caps):
    """Render one migration function: delete the listed vars, then add the listed vars."""
    needs_groups = add_vars and (has_roles or has_caps)
    lines = [
        f"def {name}(apps, schema_editor):",
        '    Permission = apps.get_model("permissions", "Permission")',
    ]
    if needs_groups:
        lines.append('    PermissionGroup = apps.get_model("permissions", "PermissionGroup")')
    blocks = ["\n".join(lines)]
    blocks += [_render_delete(v) for v in delete_vars]
    blocks += [_render_add(v, has_roles, has_caps) for v in add_vars]
    return "\n".join(blocks)


def _render_migration(to_add, to_remove, last):
    """Render the full migration file.

    Forward: delete REMOVED_PERMISSIONS (if any), then add PERMISSIONS (if any).
    Reverse: delete PERMISSIONS (if any), then restore REMOVED_PERMISSIONS (if any).
    """
    all_entries = {**to_add, **to_remove}
    has_roles = any(e["roles"] for e in all_entries.values())
    has_caps = any(e["capabilities"] for e in all_entries.values())

    imports = ["Scope"]
    if has_roles:
        imports.append("SystemRole")
    if has_caps:
        imports.append("SystemCapability")
    constants_import = f"from permissions.constants import {', '.join(sorted(imports))}"

    list_blocks = []
    if to_add:
        list_blocks.append(_render_perm_list("PERMISSIONS", to_add))
    if to_remove:
        list_blocks.append(_render_perm_list("REMOVED_PERMISSIONS", to_remove))

    if to_add and to_remove:
        forward_name, reverse_name = "sync_permissions", "unsync_permissions"
    elif to_add:
        forward_name, reverse_name = "add_permissions", "remove_permissions"
    else:
        forward_name, reverse_name = "remove_permissions", "restore_permissions"

    forward_deletes = ["REMOVED_PERMISSIONS"] if to_remove else []
    forward_adds = ["PERMISSIONS"] if to_add else []
    reverse_deletes = ["PERMISSIONS"] if to_add else []
    reverse_adds = ["REMOVED_PERMISSIONS"] if to_remove else []

    forward = _render_step(forward_name, forward_deletes, forward_adds, has_roles, has_caps)
    reverse = _render_step(reverse_name, reverse_deletes, reverse_adds, has_roles, has_caps)

    migration_class = (
        "class Migration(migrations.Migration):\n"
        "    dependencies = [\n"
        f'        ("permissions", "{last}"),\n'
        "    ]\n"
        "\n"
        "    operations = [\n"
        f"        migrations.RunPython({forward_name}, reverse_code={reverse_name}),\n"
        "    ]"
    )

    sections = ["from django.db import migrations", constants_import, *list_blocks, forward, reverse, migration_class]
    return "\n\n\n".join(sections) + "\n"


def _migration_name(prefix, codes, number):
    apps_list = list(dict.fromkeys(c.split(".")[0] for c in codes))[:3]
    return f"{number:04d}_{prefix}_{'_'.join(apps_list)}"


class Command(BaseCommand):
    help = "Generate data migrations for newly registered or recently removed permissions."

    def handle(self, *args, **options):
        from permissions.models import Permission, PermissionGroup

        registry = registered_permissions()
        registry_codes = set(registry)

        db_permissions = {p.code: p.description for p in Permission.objects.all()}
        db_codes = set(db_permissions)

        new_entries = {code: registry[code] for code in sorted(registry_codes - db_codes)}

        removed_entries = {}
        for code in sorted(db_codes - registry_codes):
            groups = PermissionGroup.objects.filter(permissions__code=code)
            removed_entries[code] = {
                "description": db_permissions[code],
                "roles": list(groups.filter(scope=Scope.USER).values_list("name", flat=True)),
                "capabilities": list(groups.filter(scope=Scope.ORGANIZATION).values_list("name", flat=True)),
            }

        if not new_entries and not removed_entries:
            self.stdout.write("No new or removed permissions — nothing to generate.")
            return

        last = _last_migration()
        next_num = _next_migration_number()
        all_codes = list(new_entries) + list(removed_entries)

        if new_entries and removed_entries:
            prefix = "sync_permissions"
        elif new_entries:
            prefix = "permissions"
        else:
            prefix = "remove_permissions"

        name = _migration_name(prefix, all_codes, next_num)
        path = MIGRATIONS_DIR / f"{name}.py"
        path.write_text(_render_migration(new_entries, removed_entries, last))

        self.stdout.write(self.style.SUCCESS(f"Created {path.name}"))
        self.stdout.write("Review the migration, then run migrate.")
