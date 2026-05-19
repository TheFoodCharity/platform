from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from organizations.models import Membership, Organization
from organizations.services import SESSION_KEY
from permissions import Scope, SystemCapability, SystemRole
from permissions.models import PermissionGroup

from .models import StorageLocation

User = get_user_model()


def permission_group(name, scope):
    return PermissionGroup.objects.get(name=name, scope=scope)


def select_client_organization(client, organization):
    session = client.session
    session[SESSION_KEY] = organization.pk
    session.save()


def grant_capabilities(organization, *capabilities):
    organization.status = Organization.Status.APPROVED
    organization.is_active = True
    organization.save(update_fields=["status", "is_active"])
    for capability in capabilities:
        organization.capabilities.add(permission_group(capability, Scope.ORGANIZATION))


def add_membership(user, organization, role=SystemRole.ORGANIZATION_USER):
    return Membership.objects.create(
        user=user,
        organization=organization,
        role=permission_group(role, Scope.USER),
    )


def create_user_with_organization(email, *capabilities):
    user = User.objects.create_user(
        email=email,
        password="password",
        first_name="Storage",
        last_name="User",
        email_verified=True,
    )
    organization = Organization.objects.create(name=f"{email} Org", owner=user)
    grant_capabilities(organization, *capabilities)
    add_membership(user, organization)
    return user, organization


def create_storage_location(**overrides):
    defaults = {
        "name": "Main Storage",
        "owner_operator": "FCACP",
        "address": "123 Storage Street",
        "municipality": "Vancouver",
        "region": "Metro Vancouver",
        "storage_type": StorageLocation.StorageType.DRY,
        "dry_capacity": 100,
        "available_space": 80,
        "capacity_status": StorageLocation.CapacityStatus.AVAILABLE,
        "approval_status": StorageLocation.ApprovalStatus.APPROVED,
        "is_active": True,
    }
    defaults.update(overrides)
    return StorageLocation.objects.create(**defaults)


class StoragePermissionTests(TestCase):
    def test_storage_provider_can_manage_storage_locations(self):
        user, organization = create_user_with_organization(
            "storage-provider@example.com",
            SystemCapability.STORAGE_PROVIDER,
        )
        location = create_storage_location()
        self.client.force_login(user)
        select_client_organization(self.client, organization)

        list_response = self.client.get(reverse("storage:list"))
        detail_response = self.client.get(reverse("storage:detail", args=[location.pk]))
        create_response = self.client.get(reverse("storage:create"))
        edit_response = self.client.get(reverse("storage:edit", args=[location.pk]))

        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "warehouse")
        self.assertContains(list_response, "Add Storage Location")
        self.assertContains(list_response, reverse("storage:edit", args=[location.pk]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, reverse("storage:edit", args=[location.pk]))
        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(edit_response.status_code, 200)

    def test_read_only_organization_can_view_storage_but_not_modify(self):
        user, organization = create_user_with_organization(
            "storage-readonly@example.com",
            SystemCapability.READ_ONLY,
        )
        location = create_storage_location()
        self.client.force_login(user)
        select_client_organization(self.client, organization)

        list_response = self.client.get(reverse("storage:list"))
        detail_response = self.client.get(reverse("storage:detail", args=[location.pk]))
        create_response = self.client.get(reverse("storage:create"))
        edit_response = self.client.get(reverse("storage:edit", args=[location.pk]))

        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "warehouse")
        self.assertContains(list_response, '<span class="btn btn-disabled">', html=False)
        self.assertNotContains(list_response, reverse("storage:create"))
        self.assertNotContains(list_response, reverse("storage:edit", args=[location.pk]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, '<span class="btn btn-disabled">Edit</span>', html=False)
        self.assertEqual(create_response.status_code, 403)
        self.assertEqual(edit_response.status_code, 403)

    def test_organization_without_storage_permission_is_denied_storage_views(self):
        user, organization = create_user_with_organization("no-storage@example.com")
        location = create_storage_location()
        self.client.force_login(user)
        select_client_organization(self.client, organization)

        self.assertEqual(self.client.get(reverse("storage:list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("storage:detail", args=[location.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("storage:create")).status_code, 403)
        self.assertEqual(self.client.get(reverse("storage:edit", args=[location.pk])).status_code, 403)
