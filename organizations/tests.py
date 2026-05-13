import rules
from django.contrib.auth import get_user_model
from django.core.checks import run_checks
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError
from django.test import RequestFactory, TestCase

from .constants import Scope
from .managers import TenantScopedQuerySet
from .models import (
    Membership,
    MembershipPermissionOverride,
    Organization,
    OrganizationPermissionOverride,
    Permission,
    PermissionGroup,
)
from .predicates import (
    _effective_permissions,
    application_permission,
    belongs_to_current_organization,
    has_membership_in_current,
    is_staff_acting,
    member_permission,
    organization_in_application,
    organization_is_active,
    organization_is_readable,
)
from .registry import register_permission, registered_permissions
from .services import acting_as

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user(**kwargs) -> User:
    defaults = {"email": f"user{make_user._counter}@example.com", "first_name": "Test", "last_name": "User"}
    make_user._counter += 1
    defaults.update(kwargs)
    return User.objects.create_user(**defaults, password="testpass")


make_user._counter = 0


def make_org(owner, status=Organization.Status.APPROVED, is_active=True) -> Organization:
    org = Organization.objects.create(name=f"Org{make_org._counter}", owner=owner, status=status, is_active=is_active)
    make_org._counter += 1
    return org


make_org._counter = 0


def make_membership(user, org, role=None) -> Membership:
    return Membership.objects.create(user=user, organization=org, role=role)


def make_permission(code="test.perm") -> Permission:
    return Permission.objects.get_or_create(code=code, defaults={"description": "Test permission"})[0]


def make_group(name, scope, permissions=()) -> PermissionGroup:
    group, _ = PermissionGroup.objects.get_or_create(name=name, scope=scope)
    if permissions:
        group.permissions.set(permissions)
    return group


# ---------------------------------------------------------------------------
# acting_as tests
# ---------------------------------------------------------------------------


class ActingAsTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.org = make_org(owner=self.user, status=Organization.Status.APPROVED)

    def test_sets_current_organization_during_block(self):
        with acting_as(self.user, self.org):
            self.assertIs(self.user.current_organization, self.org)

    def test_removes_attribute_after_block_when_not_previously_set(self):
        self.assertFalse(hasattr(self.user, "current_organization"))
        with acting_as(self.user, self.org):
            pass
        self.assertFalse(hasattr(self.user, "current_organization"))

    def test_restores_previous_value_after_block(self):
        other_org = make_org(owner=self.user)
        self.user.current_organization = other_org
        with acting_as(self.user, self.org):
            self.assertIs(self.user.current_organization, self.org)
        self.assertIs(self.user.current_organization, other_org)

    def test_restores_on_exception(self):
        def _raise():
            raise ValueError("boom")

        self.assertFalse(hasattr(self.user, "current_organization"))
        try:
            with acting_as(self.user, self.org):
                _raise()
        except ValueError:
            pass
        self.assertFalse(hasattr(self.user, "current_organization"))

    def test_restores_previous_value_on_exception(self):
        def _raise():
            raise ValueError("boom")

        other_org = make_org(owner=self.user)
        self.user.current_organization = other_org
        try:
            with acting_as(self.user, self.org):
                _raise()
        except ValueError:
            pass
        self.assertIs(self.user.current_organization, other_org)

    def test_nested_acting_as(self):
        org_a = make_org(owner=self.user)
        org_b = make_org(owner=self.user)
        with acting_as(self.user, org_a):
            self.assertIs(self.user.current_organization, org_a)
            with acting_as(self.user, org_b):
                self.assertIs(self.user.current_organization, org_b)
            self.assertIs(self.user.current_organization, org_a)
        self.assertFalse(hasattr(self.user, "current_organization"))


# ---------------------------------------------------------------------------
# Lifecycle predicate tests
# ---------------------------------------------------------------------------


class LifecyclePredicateTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def _org(self, status, is_active=True):
        org = make_org(owner=self.user, status=status, is_active=is_active)
        self.user.current_organization = org
        return org

    def test_organization_is_active_approved(self):
        self._org(Organization.Status.APPROVED)
        self.assertTrue(organization_is_active(self.user))

    def test_organization_is_active_approved_limited(self):
        self._org(Organization.Status.APPROVED_LIMITED)
        self.assertTrue(organization_is_active(self.user))

    def test_organization_is_active_false_for_draft(self):
        self._org(Organization.Status.DRAFT)
        self.assertFalse(organization_is_active(self.user))

    def test_organization_is_active_false_for_pending(self):
        self._org(Organization.Status.PENDING)
        self.assertFalse(organization_is_active(self.user))

    def test_organization_is_active_false_for_archived(self):
        self._org(Organization.Status.ARCHIVED)
        self.assertFalse(organization_is_active(self.user))

    def test_organization_is_active_false_when_inactive(self):
        self._org(Organization.Status.APPROVED, is_active=False)
        self.assertFalse(organization_is_active(self.user))

    def test_organization_is_active_false_with_no_org(self):
        if hasattr(self.user, "current_organization"):
            del self.user.current_organization
        self.assertFalse(organization_is_active(self.user))

    def test_organization_in_application_draft(self):
        self._org(Organization.Status.DRAFT)
        self.assertTrue(organization_in_application(self.user))

    def test_organization_in_application_pending(self):
        self._org(Organization.Status.PENDING)
        self.assertTrue(organization_in_application(self.user))

    def test_organization_in_application_needs_info(self):
        self._org(Organization.Status.NEEDS_INFO)
        self.assertTrue(organization_in_application(self.user))

    def test_organization_in_application_false_for_approved(self):
        self._org(Organization.Status.APPROVED)
        self.assertFalse(organization_in_application(self.user))

    def test_organization_is_readable_approved(self):
        self._org(Organization.Status.APPROVED)
        self.assertTrue(organization_is_readable(self.user))

    def test_organization_is_readable_archived(self):
        self._org(Organization.Status.ARCHIVED)
        self.assertTrue(organization_is_readable(self.user))

    def test_organization_is_readable_declined(self):
        self._org(Organization.Status.DECLINED)
        self.assertTrue(organization_is_readable(self.user))

    def test_organization_is_readable_false_for_draft(self):
        self._org(Organization.Status.DRAFT)
        self.assertFalse(organization_is_readable(self.user))


# ---------------------------------------------------------------------------
# Membership / staff predicate tests
# ---------------------------------------------------------------------------


class MembershipPredicateTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.member = make_user()
        self.non_member = make_user()
        self.staff = make_user(is_staff=True)
        self.org = make_org(owner=self.owner, status=Organization.Status.APPROVED)
        make_membership(self.member, self.org)

    def test_has_membership_in_current_true_for_member(self):
        self.member.current_organization = self.org
        self.assertTrue(has_membership_in_current(self.member))

    def test_has_membership_in_current_false_for_non_member(self):
        self.non_member.current_organization = self.org
        self.assertFalse(has_membership_in_current(self.non_member))

    def test_has_membership_in_current_false_with_no_org(self):
        self.assertFalse(has_membership_in_current(self.member))

    def test_is_staff_acting_true_for_staff_with_org(self):
        self.staff.current_organization = self.org
        self.assertTrue(is_staff_acting(self.staff))

    def test_is_staff_acting_false_for_staff_without_org(self):
        if hasattr(self.staff, "current_organization"):
            del self.staff.current_organization
        self.assertFalse(is_staff_acting(self.staff))

    def test_is_staff_acting_false_for_non_staff_with_org(self):
        self.member.current_organization = self.org
        self.assertFalse(is_staff_acting(self.member))


# ---------------------------------------------------------------------------
# belongs_to_current_organization predicate tests
# ---------------------------------------------------------------------------


class BelongsToCurrentOrgTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.org = make_org(owner=self.user)
        self.other_org = make_org(owner=self.user)
        self.user.current_organization = self.org

    def test_true_when_obj_is_none(self):
        self.assertTrue(belongs_to_current_organization(self.user, None))

    def test_true_when_obj_belongs_to_current_org(self):
        obj = type("FakeObj", (), {"owner_organization_id": self.org.pk})()
        self.assertTrue(belongs_to_current_organization(self.user, obj))

    def test_false_when_obj_belongs_to_other_org(self):
        obj = type("FakeObj", (), {"owner_organization_id": self.other_org.pk})()
        self.assertFalse(belongs_to_current_organization(self.user, obj))

    def test_false_when_no_current_organization(self):
        del self.user.current_organization
        obj = type("FakeObj", (), {"owner_organization_id": self.org.pk})()
        self.assertFalse(belongs_to_current_organization(self.user, obj))

    def test_false_when_obj_has_no_owner_organization_id(self):
        obj = type("FakeObj", (), {})()
        self.assertFalse(belongs_to_current_organization(self.user, obj))


# ---------------------------------------------------------------------------
# Cascade / _effective_permissions tests
# ---------------------------------------------------------------------------


class CascadeTests(TestCase):
    """Matrix: (role x role-overrides) x (capabilities x org-overrides) -> effective_set."""

    @classmethod
    def setUpTestData(cls):
        cls.user = make_user()
        cls.org = make_org(owner=cls.user, status=Organization.Status.APPROVED)

        cls.perm_a = Permission.objects.create(code="test.perm_a", description="Perm A")
        cls.perm_b = Permission.objects.create(code="test.perm_b", description="Perm B")
        cls.perm_c = Permission.objects.create(code="test.perm_c", description="Perm C")

        cls.user_role = PermissionGroup.objects.create(name="Test User Role", scope=Scope.USER)
        cls.org_cap = PermissionGroup.objects.create(name="Test Org Cap", scope=Scope.ORGANIZATION)

    def setUp(self):
        # Clear any cached permission results between tests
        if hasattr(self.user, "_permission_cache"):
            del self.user._permission_cache
        # Reset role/capability assignments
        self.user_role.permissions.clear()
        self.org_cap.permissions.clear()
        self.org.capabilities.clear()
        MembershipPermissionOverride.objects.filter(membership__user=self.user).delete()
        OrganizationPermissionOverride.objects.filter(organization=self.org).delete()
        Membership.objects.filter(user=self.user, organization=self.org).delete()

    def _make_membership(self, role=None):
        return Membership.objects.create(user=self.user, organization=self.org, role=role)

    def test_no_membership_returns_empty(self):
        result = _effective_permissions(self.user, self.org)
        self.assertEqual(result, frozenset())

    def test_no_role_no_capabilities_returns_empty(self):
        self._make_membership(role=None)
        self.org.capabilities.add(self.org_cap)
        result = _effective_permissions(self.user, self.org)
        self.assertEqual(result, frozenset())

    def test_role_grants_permission(self):
        self.user_role.permissions.add(self.perm_a)
        self.org_cap.permissions.add(self.perm_a)
        self.org.capabilities.add(self.org_cap)
        self._make_membership(role=self.user_role)
        result = _effective_permissions(self.user, self.org)
        self.assertIn("test.perm_a", result)

    def test_org_capability_is_ceiling(self):
        # User role has perm_a, but org has no matching capability -> not in effective set
        self.user_role.permissions.add(self.perm_a)
        self._make_membership(role=self.user_role)
        # org_cap does NOT include perm_a, and org has no capabilities with perm_a
        result = _effective_permissions(self.user, self.org)
        self.assertNotIn("test.perm_a", result)

    def test_membership_allow_override_adds_to_user_set(self):
        # perm_b not in role, but allow override adds it; org cap must include it too
        self.org_cap.permissions.add(self.perm_b)
        self.org.capabilities.add(self.org_cap)
        membership = self._make_membership(role=self.user_role)
        MembershipPermissionOverride.objects.create(
            membership=membership, permission=self.perm_b, effect=MembershipPermissionOverride.Effect.ALLOW
        )
        result = _effective_permissions(self.user, self.org)
        self.assertIn("test.perm_b", result)

    def test_membership_deny_override_removes_from_user_set(self):
        self.user_role.permissions.add(self.perm_a)
        self.org_cap.permissions.add(self.perm_a)
        self.org.capabilities.add(self.org_cap)
        membership = self._make_membership(role=self.user_role)
        MembershipPermissionOverride.objects.create(
            membership=membership, permission=self.perm_a, effect=MembershipPermissionOverride.Effect.DENY
        )
        result = _effective_permissions(self.user, self.org)
        self.assertNotIn("test.perm_a", result)

    def test_org_allow_override_expands_org_set(self):
        # perm_c not in any capability, but org ALLOW override adds it to org set
        self.user_role.permissions.add(self.perm_c)
        self._make_membership(role=self.user_role)
        OrganizationPermissionOverride.objects.create(
            organization=self.org, permission=self.perm_c, effect=OrganizationPermissionOverride.Effect.ALLOW
        )
        result = _effective_permissions(self.user, self.org)
        self.assertIn("test.perm_c", result)

    def test_org_deny_override_removes_from_org_set(self):
        self.user_role.permissions.add(self.perm_a)
        self.org_cap.permissions.add(self.perm_a)
        self.org.capabilities.add(self.org_cap)
        self._make_membership(role=self.user_role)
        OrganizationPermissionOverride.objects.create(
            organization=self.org, permission=self.perm_a, effect=OrganizationPermissionOverride.Effect.DENY
        )
        result = _effective_permissions(self.user, self.org)
        self.assertNotIn("test.perm_a", result)

    def test_result_is_intersection(self):
        # perm_a in user set only, perm_b in org set only, perm_c in both
        self.user_role.permissions.add(self.perm_a, self.perm_c)
        self.org_cap.permissions.add(self.perm_b, self.perm_c)
        self.org.capabilities.add(self.org_cap)
        self._make_membership(role=self.user_role)
        result = _effective_permissions(self.user, self.org)
        self.assertNotIn("test.perm_a", result)
        self.assertNotIn("test.perm_b", result)
        self.assertIn("test.perm_c", result)

    def test_result_is_cached(self):
        self.user_role.permissions.add(self.perm_a)
        self.org_cap.permissions.add(self.perm_a)
        self.org.capabilities.add(self.org_cap)
        self._make_membership(role=self.user_role)
        r1 = _effective_permissions(self.user, self.org)
        r2 = _effective_permissions(self.user, self.org)
        self.assertIs(r1, r2)


# ---------------------------------------------------------------------------
# member_permission / application_permission predicate composition tests
# ---------------------------------------------------------------------------


class MemberPermissionPredicateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.perm = Permission.objects.create(code="test.mp_perm", description="mp perm")
        cls.user_role = PermissionGroup.objects.create(name="MP Test Role", scope=Scope.USER)
        cls.user_role.permissions.add(cls.perm)
        cls.org_cap = PermissionGroup.objects.create(name="MP Test Cap", scope=Scope.ORGANIZATION)
        cls.org_cap.permissions.add(cls.perm)

        cls.member = make_user()
        cls.non_member = make_user()
        cls.staff = make_user(is_staff=True)

        cls.active_org = make_org(owner=cls.member, status=Organization.Status.APPROVED)
        cls.active_org.capabilities.add(cls.org_cap)
        cls.draft_org = make_org(owner=cls.member, status=Organization.Status.DRAFT)
        cls.draft_org.capabilities.add(cls.org_cap)

        make_membership(cls.member, cls.active_org, role=cls.user_role)
        make_membership(cls.member, cls.draft_org, role=cls.user_role)

        cls.predicate = member_permission("test.mp_perm")
        cls.app_predicate = application_permission("test.mp_perm")

    def setUp(self):
        # Clear permission cache between tests
        for user in (self.member, self.non_member, self.staff):
            if hasattr(user, "_permission_cache"):
                del user._permission_cache

    def test_member_with_permission_in_active_org(self):
        self.member.current_organization = self.active_org
        self.assertTrue(self.predicate(self.member))

    def test_non_member_denied(self):
        self.non_member.current_organization = self.active_org
        self.assertFalse(self.predicate(self.non_member))

    def test_member_denied_when_org_not_active(self):
        self.member.current_organization = self.draft_org
        self.assertFalse(self.predicate(self.member))

    def test_member_denied_with_no_org(self):
        if hasattr(self.member, "current_organization"):
            del self.member.current_organization
        self.assertFalse(self.predicate(self.member))

    def test_staff_bypass_in_active_org(self):
        self.staff.current_organization = self.active_org
        self.assertTrue(self.predicate(self.staff))

    def test_staff_bypass_in_draft_org(self):
        self.staff.current_organization = self.draft_org
        self.assertTrue(self.predicate(self.staff))

    def test_staff_denied_without_current_org(self):
        if hasattr(self.staff, "current_organization"):
            del self.staff.current_organization
        self.assertFalse(self.predicate(self.staff))

    def test_application_permission_member_in_draft_org(self):
        self.member.current_organization = self.draft_org
        self.assertTrue(self.app_predicate(self.member))

    def test_application_permission_member_denied_in_active_org(self):
        self.member.current_organization = self.active_org
        self.assertFalse(self.app_predicate(self.member))


# ---------------------------------------------------------------------------
# TenantScopedQuerySet tests
# ---------------------------------------------------------------------------


class TenantScopedManagerTests(TestCase):
    """Tests using Membership as a proxy for a tenant-scoped model, patching tenant_field."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user()
        cls.other_owner = make_user()
        cls.org = make_org(owner=cls.owner, status=Organization.Status.APPROVED)
        cls.other_org = make_org(owner=cls.other_owner, status=Organization.Status.APPROVED)
        cls.member = make_user()
        cls.staff = make_user(is_staff=True)
        make_membership(cls.member, cls.org)
        make_membership(cls.member, cls.other_org)

    def _make_request(self, user, organization):
        rf = RequestFactory()
        request = rf.get("/")
        request.user = user
        request.organization = organization
        return request

    def _qs_with_tenant(self):
        """Return a TenantScopedQuerySet backed by Membership with tenant_field='organization'."""
        Membership.tenant_field = "organization"
        try:
            return TenantScopedQuerySet(model=Membership, using="default")
        finally:
            del Membership.tenant_field

    def test_for_request_returns_only_current_org_rows(self):
        Membership.tenant_field = "organization"
        try:
            qs = TenantScopedQuerySet(model=Membership, using="default")
            request = self._make_request(self.member, self.org)
            result = qs.for_request(request)
            orgs = list(result.values_list("organization_id", flat=True))
            self.assertTrue(all(o == self.org.pk for o in orgs))
        finally:
            del Membership.tenant_field

    def test_for_request_returns_all_for_staff(self):
        Membership.tenant_field = "organization"
        try:
            qs = TenantScopedQuerySet(model=Membership, using="default")
            request = self._make_request(self.staff, self.org)
            result = qs.for_request(request)
            self.assertEqual(result.count(), Membership.objects.count())
        finally:
            del Membership.tenant_field

    def test_for_request_returns_none_when_no_org(self):
        Membership.tenant_field = "organization"
        try:
            qs = TenantScopedQuerySet(model=Membership, using="default")
            request = self._make_request(self.member, None)
            request.organization = None
            result = qs.for_request(request)
            self.assertEqual(result.count(), 0)
        finally:
            del Membership.tenant_field

    def test_for_organization_filters_correctly(self):
        Membership.tenant_field = "organization"
        try:
            qs = TenantScopedQuerySet(model=Membership, using="default")
            result = qs.for_organization(self.org)
            orgs = list(result.values_list("organization_id", flat=True))
            self.assertTrue(all(o == self.org.pk for o in orgs))
        finally:
            del Membership.tenant_field

    def test_for_organization_returns_none_when_org_is_none(self):
        Membership.tenant_field = "organization"
        try:
            qs = TenantScopedQuerySet(model=Membership, using="default")
            result = qs.for_organization(None)
            self.assertEqual(result.count(), 0)
        finally:
            del Membership.tenant_field

    def test_raises_improperly_configured_when_tenant_field_missing(self):
        qs = TenantScopedQuerySet(model=Membership, using="default")
        with self.assertRaises(ImproperlyConfigured):
            qs._tenant_field()


# ---------------------------------------------------------------------------
# Override uniqueness tests
# ---------------------------------------------------------------------------


class OverrideUniquenessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_user()
        cls.org = make_org(owner=cls.user)
        cls.membership = make_membership(cls.user, cls.org)
        cls.perm = Permission.objects.create(code="test.unique_perm", description="Unique test perm")

    def test_org_override_unique_together(self):
        OrganizationPermissionOverride.objects.create(
            organization=self.org, permission=self.perm, effect=OrganizationPermissionOverride.Effect.ALLOW
        )
        with self.assertRaises(IntegrityError):
            OrganizationPermissionOverride.objects.create(
                organization=self.org, permission=self.perm, effect=OrganizationPermissionOverride.Effect.DENY
            )

    def test_membership_override_unique_together(self):
        MembershipPermissionOverride.objects.create(
            membership=self.membership, permission=self.perm, effect=MembershipPermissionOverride.Effect.ALLOW
        )
        with self.assertRaises(IntegrityError):
            MembershipPermissionOverride.objects.create(
                membership=self.membership, permission=self.perm, effect=MembershipPermissionOverride.Effect.DENY
            )


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


class RegistryTests(TestCase):
    def setUp(self):
        # Save and restore the registry state around each test
        from organizations import registry

        self._orig_descriptions = dict(registry._registry)
        self._orig_rules = dict(rules.permissions.permissions)

    def tearDown(self):
        from organizations import registry

        registry._registry.clear()
        registry._registry.update(self._orig_descriptions)
        rules.permissions.permissions.clear()
        rules.permissions.permissions.update(self._orig_rules)

    def test_register_permission_records_description(self):
        register_permission("test.registry_perm", "Registry test", rule=rules.always_true)
        self.assertIn("test.registry_perm", registered_permissions())
        self.assertEqual(registered_permissions()["test.registry_perm"], "Registry test")

    def test_register_permission_adds_to_rules(self):
        register_permission("test.rules_perm", "Rules test", rule=rules.always_true)
        self.assertIn("test.rules_perm", rules.permissions.permissions)

    def test_register_permission_raises_on_duplicate(self):
        register_permission("test.dup_perm", "First", rule=rules.always_true)
        with self.assertRaises(RuntimeError, msg="Permission 'test.dup_perm' is already registered"):
            register_permission("test.dup_perm", "Second", rule=rules.always_true)

    def test_registered_permissions_returns_copy(self):
        result = registered_permissions()
        result["test.mutated"] = "mutated"
        self.assertNotIn("test.mutated", registered_permissions())


# ---------------------------------------------------------------------------
# System check tests
# ---------------------------------------------------------------------------


class SystemCheckE001Tests(TestCase):
    """E001: stray rules.add_perm() that bypassed register_permission()."""

    def setUp(self):
        from organizations import registry

        self._orig_descriptions = dict(registry._registry)
        self._orig_rules = dict(rules.permissions.permissions)

    def tearDown(self):
        from organizations import registry

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
        from organizations import registry

        self._orig_descriptions = dict(registry._registry)
        self._orig_rules = dict(rules.permissions.permissions)

    def tearDown(self):
        from organizations import registry

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


# ---------------------------------------------------------------------------
# Middleware tests
# ---------------------------------------------------------------------------


class MiddlewareTests(TestCase):
    def test_middleware_pins_organization_onto_user(self):
        from unittest.mock import MagicMock, patch

        user = make_user()
        org = make_org(owner=user)

        request = MagicMock()
        request.session = {}
        request.user = user

        with patch("organizations.middleware.get_current_organization", return_value=org):
            request.organization = org
            if hasattr(request, "user"):
                request.user.current_organization = request.organization

        self.assertIs(user.current_organization, org)

    def test_middleware_sets_current_organization_via_call(self):
        from unittest.mock import MagicMock, patch

        from .middleware import CurrentOrganizationMiddleware

        user = make_user()
        org = make_org(owner=user)

        def get_response(req):
            # By the time get_response runs, current_organization should be set
            assert hasattr(req.user, "current_organization")
            return MagicMock()

        middleware = CurrentOrganizationMiddleware(get_response)

        request = MagicMock()
        request.session = {}
        request.user = user

        with patch("organizations.middleware.get_current_organization", return_value=org):
            middleware(request)

        self.assertIs(user.current_organization, request.organization)
