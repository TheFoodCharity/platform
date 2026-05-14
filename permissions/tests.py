import rules
from django.core.checks import run_checks
from django.test import TestCase

from .models import Permission
from .registry import register_permission, registered_permissions

# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


class RegistryTests(TestCase):
    def setUp(self):
        # Save and restore the registry state around each test
        from permissions import registry

        self._orig_descriptions = dict(registry._registry)
        self._orig_rules = dict(rules.permissions.permissions)

    def tearDown(self):
        from permissions import registry

        registry._registry.clear()
        registry._registry.update(self._orig_descriptions)
        rules.permissions.permissions.clear()
        rules.permissions.permissions.update(self._orig_rules)

    def test_register_permission_records_description(self):
        register_permission("test.registry_perm", "Registry test", rule=rules.always_true)
        self.assertIn("test.registry_perm", registered_permissions())
        self.assertEqual(registered_permissions()["test.registry_perm"]["description"], "Registry test")

    def test_register_permission_adds_to_rules(self):
        register_permission("test.rules_perm", "Rules test", rule=rules.always_true)
        self.assertIn("test.rules_perm", rules.permissions.permissions)

    def test_register_permission_raises_on_duplicate(self):
        register_permission("test.dup_perm", "First", rule=rules.always_true)
        with self.assertRaises(RuntimeError, msg="Permission 'test.dup_perm' is already registered"):
            register_permission("test.dup_perm", "Second", rule=rules.always_true)

    def test_registered_permissions_entry_has_expected_keys(self):
        register_permission("test.entry_shape", "Shape test", rule=rules.always_true)
        entry = registered_permissions()["test.entry_shape"]
        self.assertEqual(entry["description"], "Shape test")
        self.assertIsInstance(entry["roles"], list)
        self.assertIsInstance(entry["capabilities"], list)


# ---------------------------------------------------------------------------
# System check tests
# ---------------------------------------------------------------------------


class SystemCheckE001Tests(TestCase):
    """E001: stray rules.add_perm() that bypassed register_permission()."""

    def setUp(self):
        from permissions import registry

        self._orig_descriptions = dict(registry._registry)
        self._orig_rules = dict(rules.permissions.permissions)

    def tearDown(self):
        from permissions import registry

        registry._registry.clear()
        registry._registry.update(self._orig_descriptions)
        rules.permissions.permissions.clear()
        rules.permissions.permissions.update(self._orig_rules)

    def test_e001_fires_for_stray_add_perm(self):
        rules.add_perm("test.stray_perm", rules.always_true)
        errors = run_checks(tags=None)
        e001_errors = [e for e in errors if getattr(e, "id", None) == "organizations.E001"]
        self.assertTrue(any("test.stray_perm" in e.msg for e in e001_errors))

    def test_e001_clean_when_registered_via_register_permission(self):
        register_permission("test.clean_perm", "Clean", rule=rules.always_true)
        errors = run_checks(tags=None)
        e001_errors = [e for e in errors if getattr(e, "id", None) == "organizations.E001"]
        self.assertFalse(any("test.clean_perm" in e.msg for e in e001_errors))


class SystemCheckE002Tests(TestCase):
    """E002/W001: DB and registry must contain identical permission codes."""

    def setUp(self):
        from permissions import registry

        self._orig_descriptions = dict(registry._registry)
        self._orig_rules = dict(rules.permissions.permissions)

    def tearDown(self):
        from permissions import registry

        registry._registry.clear()
        registry._registry.update(self._orig_descriptions)
        rules.permissions.permissions.clear()
        rules.permissions.permissions.update(self._orig_rules)
        # Clean up any permission rows created in this test
        Permission.objects.filter(code__startswith="test.e002").delete()

    def test_w001_fires_when_registered_but_no_db_row(self):
        register_permission("test.e002_no_db", "No DB row", rule=rules.always_true)
        errors = run_checks(tags=None, databases=["default"])
        w001s = [e for e in errors if getattr(e, "id", None) == "organizations.W001"]
        self.assertTrue(any("test.e002_no_db" in e.msg for e in w001s))

    def test_e002_fires_when_db_row_not_registered(self):
        Permission.objects.create(code="test.e002_orphan", description="Orphan")
        errors = run_checks(tags=None, databases=["default"])
        e002s = [e for e in errors if getattr(e, "id", None) == "organizations.E002"]
        self.assertTrue(any("test.e002_orphan" in e.msg for e in e002s))

    def test_no_errors_when_db_and_registry_match(self):
        register_permission("test.e002_match", "Match", rule=rules.always_true)
        Permission.objects.get_or_create(code="test.e002_match", defaults={"description": "Match"})
        errors = run_checks(tags=None)
        check_ids = {"organizations.E001", "organizations.E002", "organizations.W001"}
        relevant = [e for e in errors if getattr(e, "id", None) in check_ids and "test.e002_match" in e.msg]
        self.assertEqual(relevant, [])
