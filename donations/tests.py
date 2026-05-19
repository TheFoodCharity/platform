from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from organizations.models import Membership, Organization
from organizations.services import SESSION_KEY
from permissions import Scope, SystemCapability, SystemRole
from permissions.models import PermissionGroup
from storage.models import StorageLocation

from .forms import (
    FOOD_TYPE_INTAKE,
    DonationFoodItemFormSet,
    DonationForm,
    FoodRequestAllocationFormSet,
    FoodRequestForm,
)
from .models import Donation, DonationFoodItem, FoodRequest, FoodRequestAllocation

User = get_user_model()


def select_client_organization(client, organization):
    session = client.session
    session[SESSION_KEY] = organization.pk
    session.save()


def permission_group(name, scope):
    return PermissionGroup.objects.get(name=name, scope=scope)


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


def grant_donor_access(user, organization):
    grant_capabilities(organization, SystemCapability.FOOD_DONOR)
    return add_membership(user, organization)


def grant_receiver_access(user, organization):
    grant_capabilities(organization, SystemCapability.FOOD_RECEIVER)
    return add_membership(user, organization)


class DonationFormTests(SimpleTestCase):
    def test_intake_form_has_reference_style_sections(self):
        form = DonationForm()

        self.assertNotIn("company_name", form.fields)
        self.assertNotIn("donor_name", form.fields)
        self.assertNotIn("contact_email", form.fields)
        self.assertIn("pickup_day", form.fields)
        self.assertIn("pickup_ready_time", form.fields)
        self.assertIn("pickup_end_time", form.fields)
        self.assertNotIn("pickup_deadline", form.fields)
        self.assertIn("receiver_limit", form.fields)
        self.assertIn("preferred_receiver_organization", form.fields)
        self.assertIn("people_fed_estimate", form.fields)
        self.assertIn("fits_in_car", form.fields)
        self.assertIn("food_safety_agreement", form.fields)

    def test_food_items_are_captured_in_a_formset(self):
        formset = DonationFoodItemFormSet()

        self.assertEqual(formset.min_num, 1)
        self.assertIn("selected", formset.forms[0].fields)
        self.assertIn("food_category", formset.forms[0].fields)
        self.assertIn("packaging", formset.forms[0].fields)
        self.assertIn("quantity", formset.forms[0].fields)
        self.assertIn("description", formset.forms[0].fields)

    def test_status_is_not_user_editable(self):
        form = DonationForm()

        self.assertNotIn("status", form.fields)

    def test_receiver_limit_defaults_to_one_receiver(self):
        form = DonationForm()

        self.assertEqual(form["receiver_limit"].value(), Donation.ReceiverLimit.ONE)

    def test_unit_fields_use_dropdown_choices(self):
        form = DonationForm()

        self.assertEqual(list(form.fields["pickup_day"].choices), list(Donation.PickupDay.choices))
        self.assertEqual(list(form.fields["pickup_ready_time"].choices), list(Donation.PickupReadyTime.choices))
        self.assertEqual(list(form.fields["pickup_end_time"].choices), list(Donation.PickupEndTime.choices))


class DonationIntakeViewTests(TestCase):
    def create_user_with_org(self, email="supplier@example.com", organization_name="Supplier Org"):
        user = User.objects.create_user(
            email=email,
            password="password",
            first_name="Sam",
            last_name="Supplier",
            email_verified=True,
        )
        organization = Organization.objects.create(name=organization_name, owner=user, is_active=True)
        grant_donor_access(user, organization)
        return user, organization

    def select_organization(self, organization):
        select_client_organization(self.client, organization)

    def donation_post_data(self):
        data = {
            "pickup_location": "123 Main Street",
            "pickup_day": Donation.PickupDay.TODAY,
            "pickup_ready_time": Donation.PickupReadyTime.READY_NOW,
            "pickup_end_time": Donation.PickupEndTime.BEFORE_5PM,
            "pickup_notes": "Today before 5pm",
            "storage_requirement": Donation.StorageRequirement.DRY,
            "receiver_limit": Donation.ReceiverLimit.ONE,
            "preferred_receiver_organization": "",
            "people_fed_estimate": Donation.PeopleFedEstimate.FIFTY,
            "fits_in_car": "True",
            "food_safety_agreement": "on",
            "other_information": "Use the loading door.",
            "food_items-TOTAL_FORMS": str(len(FOOD_TYPE_INTAKE)),
            "food_items-INITIAL_FORMS": "0",
            "food_items-MIN_NUM_FORMS": "1",
            "food_items-MAX_NUM_FORMS": "1000",
        }

        for index, (food_category, _label, _example) in enumerate(FOOD_TYPE_INTAKE):
            data[f"food_items-{index}-food_category"] = food_category
            data[f"food_items-{index}-packaging"] = ""
            data[f"food_items-{index}-quantity"] = ""
            data[f"food_items-{index}-description"] = ""

        produce_index = next(
            index
            for index, (food_category, _label, _example) in enumerate(FOOD_TYPE_INTAKE)
            if food_category == Donation.FoodCategory.PRODUCE
        )
        data[f"food_items-{produce_index}-selected"] = "on"
        data[f"food_items-{produce_index}-packaging"] = DonationFoodItem.Packaging.BOXES
        data[f"food_items-{produce_index}-quantity"] = "12"
        data[f"food_items-{produce_index}-description"] = "Mixed produce"
        return data

    def test_create_donation_saves_food_items(self):
        user, organization = self.create_user_with_org()
        self.client.force_login(user)
        self.select_organization(organization)

        response = self.client.post(reverse("donations:create"), self.donation_post_data())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Donation.objects.count(), 1)
        self.assertEqual(DonationFoodItem.objects.count(), 1)

        donation = Donation.objects.get()
        self.assertRedirects(response, reverse("donations:donation_thanks", args=[donation.pk]))
        self.assertEqual(donation.submitted_by, user)
        self.assertEqual(donation.supplier_organization, organization)
        self.assertEqual(donation.food_category, Donation.FoodCategory.PRODUCE)
        self.assertEqual(donation.quantity, 12)
        self.assertEqual(donation.receiver_limit, Donation.ReceiverLimit.ONE)
        self.assertEqual(donation.status, Donation.Status.AVAILABLE)
        self.assertIsNotNone(donation.pickup_deadline)

        thanks_response = self.client.get(reverse("donations:donation_thanks", args=[donation.pk]))
        self.assertContains(thanks_response, "Donation Submitted")
        self.assertContains(thanks_response, "Thank you for helping fight hunger")
        self.assertContains(thanks_response, donation.ticket_number)

    def test_logged_in_user_donation_is_attached_to_user_and_organization(self):
        user, organization = self.create_user_with_org()
        self.client.force_login(user)
        self.select_organization(organization)

        response = self.client.post(reverse("donations:create"), self.donation_post_data())

        self.assertEqual(response.status_code, 302)
        donation = Donation.objects.get()
        self.assertEqual(donation.submitted_by, user)
        self.assertEqual(donation.supplier_organization, organization)

    def test_logged_in_user_gets_donor_info_prefilled_from_account_and_organization(self):
        user = User.objects.create_user(
            email="supplier@example.com",
            password="password",
            first_name="Sam",
            last_name="Supplier",
            email_verified=True,
        )
        organization = Organization.objects.create(
            name="Supplier Org",
            owner=user,
            is_active=True,
            address_line_1="1081 Burrard St",
            address_line_2="Suite 200",
            municipality="Vancouver",
            region="BC",
            postal_code="V6Z 1Y6",
            service_area="123 Farm Road",
            email="donations@supplier.example",
            phone="6045550100",
        )
        grant_donor_access(user, organization)
        self.client.force_login(user)
        self.select_organization(organization)

        response = self.client.get(reverse("donations:create"))

        self.assertContains(response, "Supplier Org")
        self.assertContains(response, "1081 Burrard St, Suite 200, Vancouver, BC V6Z 1Y6")
        self.assertContains(response, "donations@supplier.example")
        self.assertContains(response, "6045550100")
        self.assertContains(response, "Sam Supplier")
        self.assertContains(response, 'name="pickup_location"')
        self.assertContains(response, 'value="1081 Burrard St, Suite 200, Vancouver, BC V6Z 1Y6"')

    def test_donation_form_uses_current_switched_organization(self):
        user, _first_organization = self.create_user_with_org(organization_name="First Org")
        second_organization = Organization.objects.create(
            name="Second Org",
            owner=user,
            is_active=True,
            address_line_1="222 Switch Street",
            municipality="Burnaby",
            region="BC",
            postal_code="V5A 1A1",
            email="second@example.com",
        )
        grant_donor_access(user, second_organization)
        self.client.force_login(user)
        self.select_organization(second_organization)

        response = self.client.get(reverse("donations:create"))

        self.assertContains(response, "Second Org")
        self.assertContains(response, "second@example.com")

    def test_created_donation_uses_current_switched_organization(self):
        user, first_organization = self.create_user_with_org(organization_name="First Org")
        second_organization = Organization.objects.create(name="Second Org", owner=user, is_active=True)
        grant_donor_access(user, second_organization)
        self.client.force_login(user)
        self.select_organization(second_organization)

        response = self.client.post(reverse("donations:create"), self.donation_post_data())

        donation = Donation.objects.get()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(donation.supplier_organization, second_organization)
        self.assertNotEqual(donation.supplier_organization, first_organization)

    def test_org_members_share_supplier_donation_list(self):
        owner = User.objects.create_user(
            email="owner@example.com",
            password="password",
            first_name="Owner",
            last_name="User",
            email_verified=True,
        )
        member = User.objects.create_user(
            email="member@example.com",
            password="password",
            first_name="Member",
            last_name="User",
            email_verified=True,
        )
        other_user = User.objects.create_user(
            email="other@example.com",
            password="password",
            first_name="Other",
            last_name="User",
            email_verified=True,
        )
        organization = Organization.objects.create(name="Shared Org", owner=owner, is_active=True)
        other_organization = Organization.objects.create(name="Other Org", owner=other_user, is_active=True)
        grant_donor_access(owner, organization)
        add_membership(member, organization)
        grant_donor_access(other_user, other_organization)
        Donation.objects.create(
            submitted_by=owner,
            supplier_organization=organization,
            food_category=Donation.FoodCategory.PRODUCE,
            food_type=[Donation.FoodCategory.PRODUCE],
            quantity=12,
            unit=Donation.QuantityUnit.BOXES,
            pickup_location="123 Main Street",
            pickup_deadline=timezone.now() + timezone.timedelta(days=1),
            storage_requirement=Donation.StorageRequirement.DRY,
            receiver_limit=Donation.ReceiverLimit.NO_LIMIT,
            status=Donation.Status.SUBMITTED,
        )
        Donation.objects.create(
            submitted_by=other_user,
            supplier_organization=other_organization,
            food_category=Donation.FoodCategory.DAIRY,
            food_type=[Donation.FoodCategory.DAIRY],
            quantity=4,
            unit=Donation.QuantityUnit.BOXES,
            pickup_location="456 Main Street",
            pickup_deadline=timezone.now() + timezone.timedelta(days=1),
            storage_requirement=Donation.StorageRequirement.REFRIGERATED,
            status=Donation.Status.SUBMITTED,
        )
        self.client.force_login(member)
        self.select_organization(organization)

        response = self.client.get(reverse("donations:list"))

        self.assertContains(response, "Shared Org")
        self.assertNotContains(response, "Other Org")

    def test_donation_list_shows_total_quantity_for_food_items(self):
        user, organization = self.create_user_with_org()
        donation = Donation.objects.create(
            submitted_by=user,
            supplier_organization=organization,
            food_category=Donation.FoodCategory.MEAT_PROTEIN,
            food_type=[Donation.FoodCategory.MEAT_PROTEIN, Donation.FoodCategory.OTHER],
            quantity=9,
            unit=Donation.QuantityUnit.BOXES,
            pickup_location="123 Main Street",
            pickup_deadline=timezone.now() + timezone.timedelta(days=1),
            storage_requirement=Donation.StorageRequirement.REFRIGERATED,
            status=Donation.Status.SUBMITTED,
        )
        DonationFoodItem.objects.create(
            donation=donation,
            food_category=Donation.FoodCategory.MEAT_PROTEIN,
            packaging=DonationFoodItem.Packaging.BOXES,
            quantity=5,
            description="Meat",
        )
        DonationFoodItem.objects.create(
            donation=donation,
            food_category=Donation.FoodCategory.OTHER,
            packaging=DonationFoodItem.Packaging.BOXES,
            quantity=4,
            description="Other food",
        )
        self.client.force_login(user)
        self.select_organization(organization)

        response = self.client.get(reverse("donations:list"))

        self.assertContains(response, "Total:</span> 9 Boxes", html=False)
        self.assertContains(response, "Today, Before 5pm")

    def test_read_only_organization_can_view_all_donation_history(self):
        user = User.objects.create_user(
            email="readonly@example.com",
            password="password",
            first_name="Read",
            last_name="Only",
            email_verified=True,
        )
        organization = Organization.objects.create(name="Read Only Org", owner=user, is_active=True)
        grant_capabilities(organization, SystemCapability.READ_ONLY)
        add_membership(user, organization)
        donation = Donation.objects.create(
            submitted_by=user,
            supplier_organization=organization,
            food_category=Donation.FoodCategory.PRODUCE,
            food_type=[Donation.FoodCategory.PRODUCE],
            quantity=12,
            unit=Donation.QuantityUnit.BOXES,
            pickup_location="123 Main Street",
            pickup_deadline=timezone.now() + timezone.timedelta(days=1),
            storage_requirement=Donation.StorageRequirement.DRY,
            status=Donation.Status.SUBMITTED,
        )
        other_user = User.objects.create_user(
            email="other-donor@example.com",
            password="password",
            first_name="Other",
            last_name="Donor",
            email_verified=True,
        )
        other_organization = Organization.objects.create(name="Other Donor Org", owner=other_user, is_active=True)
        other_donation = Donation.objects.create(
            submitted_by=other_user,
            supplier_organization=other_organization,
            food_category=Donation.FoodCategory.DAIRY,
            food_type=[Donation.FoodCategory.DAIRY],
            quantity=4,
            unit=Donation.QuantityUnit.BOXES,
            pickup_location="456 Main Street",
            pickup_deadline=timezone.now() + timezone.timedelta(days=1),
            storage_requirement=Donation.StorageRequirement.REFRIGERATED,
            status=Donation.Status.SUBMITTED,
        )
        self.client.force_login(user)
        self.select_organization(organization)

        list_response = self.client.get(reverse("donations:list"))
        detail_response = self.client.get(reverse("donations:detail", args=[donation.pk]))
        other_detail_response = self.client.get(reverse("donations:detail", args=[other_donation.pk]))
        create_response = self.client.get(reverse("donations:create"))

        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, donation.ticket_number)
        self.assertContains(list_response, other_donation.ticket_number)
        self.assertContains(list_response, '<span class="btn btn-disabled">', html=False)
        self.assertNotContains(list_response, reverse("donations:create"))
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(other_detail_response.status_code, 200)
        self.assertEqual(create_response.status_code, 403)

    def test_donation_list_shows_exact_pickup_deadline_after_deadline_passes(self):
        user, organization = self.create_user_with_org()
        deadline = timezone.now() - timezone.timedelta(days=1)
        donation = Donation.objects.create(
            submitted_by=user,
            supplier_organization=organization,
            food_category=Donation.FoodCategory.PRODUCE,
            food_type=[Donation.FoodCategory.PRODUCE],
            quantity=12,
            unit=Donation.QuantityUnit.BOXES,
            pickup_location="123 Main Street",
            pickup_deadline=deadline,
            storage_requirement=Donation.StorageRequirement.DRY,
            status=Donation.Status.AVAILABLE,
        )
        DonationFoodItem.objects.create(
            donation=donation,
            food_category=Donation.FoodCategory.PRODUCE,
            packaging=DonationFoodItem.Packaging.BOXES,
            quantity=12,
            description="Mixed produce",
        )
        self.client.force_login(user)
        self.select_organization(organization)

        response = self.client.get(reverse("donations:list"))

        expected_deadline = date_format(timezone.localtime(deadline), "M j, Y g:i A")
        self.assertContains(response, expected_deadline)
        self.assertNotContains(response, "Today, Before 5pm")

    def test_same_day_pickup_deadline_is_not_marked_expired(self):
        user, organization = self.create_user_with_org()
        deadline = timezone.localtime(timezone.now()).replace(hour=0, minute=0, second=0, microsecond=0)
        donation = Donation.objects.create(
            submitted_by=user,
            supplier_organization=organization,
            food_category=Donation.FoodCategory.PRODUCE,
            food_type=[Donation.FoodCategory.PRODUCE],
            quantity=12,
            unit=Donation.QuantityUnit.BOXES,
            pickup_location="123 Main Street",
            pickup_deadline=deadline,
            storage_requirement=Donation.StorageRequirement.DRY,
            status=Donation.Status.AVAILABLE,
        )
        self.client.force_login(user)
        self.select_organization(organization)

        response = self.client.get(reverse("donations:detail", args=[donation.pk]))

        self.assertContains(response, "Available")
        donation.refresh_from_db()
        self.assertEqual(donation.status, Donation.Status.AVAILABLE)

    def test_past_deadline_donation_is_marked_expired(self):
        user, organization = self.create_user_with_org()
        donation = Donation.objects.create(
            submitted_by=user,
            supplier_organization=organization,
            food_category=Donation.FoodCategory.PRODUCE,
            food_type=[Donation.FoodCategory.PRODUCE],
            quantity=12,
            unit=Donation.QuantityUnit.BOXES,
            pickup_location="123 Main Street",
            pickup_deadline=timezone.now() - timezone.timedelta(days=1),
            storage_requirement=Donation.StorageRequirement.DRY,
            status=Donation.Status.AVAILABLE,
        )
        self.client.force_login(user)
        self.select_organization(organization)

        response = self.client.get(reverse("donations:detail", args=[donation.pk]))

        self.assertContains(response, "Expired")
        donation.refresh_from_db()
        self.assertEqual(donation.status, Donation.Status.EXPIRED)

    def test_donation_detail_shows_allocation_and_request_history_sections(self):
        supplier, supplier_organization = self.create_user_with_org()
        receiver = User.objects.create_user(
            email="receiver@example.com",
            password="password",
            first_name="Rae",
            last_name="Receiver",
            email_verified=True,
        )
        receiver_organization = Organization.objects.create(name="Receiver Org", owner=receiver, is_active=True)
        grant_receiver_access(receiver, receiver_organization)
        donation = Donation.objects.create(
            submitted_by=supplier,
            supplier_organization=supplier_organization,
            food_category=Donation.FoodCategory.PRODUCE,
            food_type=[Donation.FoodCategory.PRODUCE],
            quantity=12,
            unit=Donation.QuantityUnit.BOXES,
            pickup_location="123 Main Street",
            pickup_deadline=timezone.now() + timezone.timedelta(days=1),
            storage_requirement=Donation.StorageRequirement.DRY,
            receiver_limit=Donation.ReceiverLimit.NO_LIMIT,
            status=Donation.Status.SUBMITTED,
        )
        food_item = DonationFoodItem.objects.create(
            donation=donation,
            food_category=Donation.FoodCategory.PRODUCE,
            packaging=DonationFoodItem.Packaging.BOXES,
            quantity=12,
            description="Mixed produce",
        )
        food_request = FoodRequest.objects.create(
            donation=donation,
            requested_by=receiver,
            receiver_organization=receiver_organization,
            status=FoodRequest.Status.SUBMITTED,
        )
        FoodRequestAllocation.objects.create(
            food_request=food_request,
            donation_food_item=food_item,
            quantity=4,
        )
        self.client.force_login(supplier)
        self.select_organization(supplier_organization)

        response = self.client.get(reverse("donations:detail", args=[donation.pk]))

        self.assertContains(response, "Current Remaining Food")
        self.assertContains(response, "Receiver Requests")
        self.assertContains(response, "Description")
        self.assertContains(response, donation.ticket_number)
        self.assertContains(response, food_request.ticket_number)
        self.assertContains(response, "Mixed produce")
        self.assertContains(response, "12 Boxes")
        self.assertContains(response, "4 Boxes")
        self.assertContains(response, "8 Boxes")
        self.assertContains(response, "Receiver Org")
        self.assertContains(response, "Receiver preference")
        self.assertContains(response, "No limit")
        self.assertContains(response, reverse("donations:request_detail", args=[food_request.pk]))


class FoodRequestTests(TestCase):
    def select_organization(self, organization):
        select_client_organization(self.client, organization)

    def setUp(self):
        self.supplier = User.objects.create_user(
            email="supplier@example.com",
            password="password",
            first_name="Sam",
            last_name="Supplier",
            email_verified=True,
        )
        self.supplier_organization = Organization.objects.create(
            name="Supplier Org",
            owner=self.supplier,
            is_active=True,
            phone="6045550199",
        )
        grant_donor_access(self.supplier, self.supplier_organization)

        self.donation = Donation.objects.create(
            submitted_by=self.supplier,
            supplier_organization=self.supplier_organization,
            food_category=Donation.FoodCategory.PRODUCE,
            food_type=[Donation.FoodCategory.PRODUCE],
            quantity=12,
            unit=Donation.QuantityUnit.BOXES,
            pickup_location="123 Main Street",
            pickup_deadline=timezone.now() + timezone.timedelta(days=1),
            storage_requirement=Donation.StorageRequirement.DRY,
            receiver_limit=Donation.ReceiverLimit.NO_LIMIT,
            status=Donation.Status.SUBMITTED,
        )
        self.food_item = DonationFoodItem.objects.create(
            donation=self.donation,
            food_category=Donation.FoodCategory.PRODUCE,
            packaging=DonationFoodItem.Packaging.BOXES,
            quantity=12,
            description="Mixed produce",
        )
        self.storage = StorageLocation.objects.create(
            name="Third Party Cold Storage",
            address="456 Storage Road",
            municipality="Burnaby",
            region="Metro Vancouver",
            storage_type=StorageLocation.StorageType.REFRIGERATED,
            available_space=20,
            capacity_status=StorageLocation.CapacityStatus.AVAILABLE,
            approval_status=StorageLocation.ApprovalStatus.APPROVED,
            is_active=True,
        )

        self.receiver = User.objects.create_user(
            email="receiver-user@example.com",
            password="password",
            first_name="Rae",
            last_name="Receiver",
            email_verified=True,
        )
        self.receiver_organization = Organization.objects.create(
            name="Receiver Org",
            owner=self.receiver,
            is_active=True,
        )
        grant_receiver_access(self.receiver, self.receiver_organization)

    def test_receiver_can_view_available_donation_list(self):
        self.client.force_login(self.receiver)
        self.select_organization(self.receiver_organization)
        response = self.client.get(reverse("donations:available_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Available Donations")
        self.assertContains(response, self.donation.ticket_number)
        self.assertContains(response, "Fresh Produce")
        self.assertContains(response, "Supplier Org")
        self.assertContains(response, "Available")
        self.assertContains(response, "Request this food")

    def test_read_only_organization_can_view_available_donations_but_not_request(self):
        read_only_user = User.objects.create_user(
            email="readonly-receiver@example.com",
            password="password",
            first_name="Read",
            last_name="Receiver",
            email_verified=True,
        )
        read_only_organization = Organization.objects.create(name="Read Only Receiver", owner=read_only_user)
        grant_capabilities(read_only_organization, SystemCapability.READ_ONLY)
        add_membership(read_only_user, read_only_organization)
        self.client.force_login(read_only_user)
        self.select_organization(read_only_organization)

        list_response = self.client.get(reverse("donations:available_list"))
        detail_response = self.client.get(reverse("donations:available_detail", args=[self.donation.pk]))
        request_response = self.client.get(reverse("donations:request_create", args=[self.donation.pk]))

        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, '<span class="btn btn-sm btn-disabled">Request this food</span>', html=False)
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, '<span class="btn btn-disabled">', html=False)
        self.assertNotContains(detail_response, reverse("donations:request_create", args=[self.donation.pk]))
        self.assertEqual(request_response.status_code, 403)

    def test_available_donation_list_can_filter_by_category(self):
        self.client.force_login(self.receiver)
        self.select_organization(self.receiver_organization)

        other_donation = Donation.objects.create(
            submitted_by=self.supplier,
            supplier_organization=self.supplier_organization,
            food_category=Donation.FoodCategory.DAIRY,
            food_type=[Donation.FoodCategory.DAIRY],
            quantity=4,
            unit=Donation.QuantityUnit.BOXES,
            pickup_location="456 Main Street",
            pickup_deadline=timezone.now() + timezone.timedelta(days=1),
            storage_requirement=Donation.StorageRequirement.REFRIGERATED,
            status=Donation.Status.SUBMITTED,
        )
        DonationFoodItem.objects.create(
            donation=other_donation,
            food_category=Donation.FoodCategory.DAIRY,
            packaging=DonationFoodItem.Packaging.BOXES,
            quantity=4,
            description="Milk",
        )

        response = self.client.get(
            reverse("donations:available_list"),
            {"category": Donation.FoodCategory.DAIRY},
        )

        self.assertContains(response, "Dairy")
        self.assertContains(response, other_donation.ticket_number)
        self.assertNotContains(response, "Mixed produce")

    def test_available_donation_list_prioritizes_preferred_receiver(self):
        self.donation.preferred_receiver_organization = self.receiver_organization
        self.donation.save(update_fields=["preferred_receiver_organization"])
        newer_donation = Donation.objects.create(
            submitted_by=self.supplier,
            supplier_organization=self.supplier_organization,
            food_category=Donation.FoodCategory.DAIRY,
            food_type=[Donation.FoodCategory.DAIRY],
            quantity=4,
            unit=Donation.QuantityUnit.BOXES,
            pickup_location="456 Main Street",
            pickup_deadline=timezone.now() + timezone.timedelta(days=1),
            storage_requirement=Donation.StorageRequirement.REFRIGERATED,
            status=Donation.Status.SUBMITTED,
        )
        DonationFoodItem.objects.create(
            donation=newer_donation,
            food_category=Donation.FoodCategory.DAIRY,
            packaging=DonationFoodItem.Packaging.BOXES,
            quantity=4,
            description="Milk",
        )
        self.client.force_login(self.receiver)
        self.select_organization(self.receiver_organization)

        response = self.client.get(reverse("donations:available_list"))

        content = response.content.decode()
        self.assertContains(response, "Preferred for your organization")
        self.assertLess(content.index(self.donation.ticket_number), content.index(newer_donation.ticket_number))

    def test_available_donation_list_can_filter_by_allocation_status(self):
        self.client.force_login(self.receiver)
        self.select_organization(self.receiver_organization)

        food_request = FoodRequest.objects.create(
            donation=self.donation,
            requested_by=self.receiver,
            receiver_organization=self.receiver_organization,
            status=FoodRequest.Status.SUBMITTED,
        )
        FoodRequestAllocation.objects.create(
            food_request=food_request,
            donation_food_item=self.food_item,
            quantity=12,
        )

        available_response = self.client.get(
            reverse("donations:available_list"),
            {"availability": "available"},
        )
        fully_requested_response = self.client.get(
            reverse("donations:available_list"),
            {"availability": "fully_requested"},
        )

        self.assertNotContains(available_response, "Mixed produce")
        self.assertContains(fully_requested_response, "Fully requested")
        self.assertContains(fully_requested_response, self.donation.ticket_number)

    def test_receiver_can_view_available_donation_detail(self):
        self.client.force_login(self.receiver)
        self.select_organization(self.receiver_organization)
        response = self.client.get(reverse("donations:available_detail", args=[self.donation.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Donation Details")
        self.assertContains(response, self.donation.ticket_number)
        self.assertContains(response, "Supplier Org")
        self.assertContains(response, "123 Main Street")
        self.assertContains(response, "Current Remaining Food")
        self.assertContains(response, "Mixed produce")
        self.assertContains(response, "Fresh Produce")
        self.assertContains(response, "Request this food")

    def test_receiver_can_submit_food_request(self):
        self.client.force_login(self.receiver)
        self.select_organization(self.receiver_organization)

        response = self.client.post(
            reverse("donations:request_create", args=[self.donation.pk]),
            {
                "allocations-TOTAL_FORMS": "1",
                "allocations-INITIAL_FORMS": "0",
                "allocations-MIN_NUM_FORMS": "1",
                "allocations-MAX_NUM_FORMS": "1000",
                "allocations-0-food_item_id": self.food_item.id,
                "allocations-0-quantity": 4,
                "storage_required": "on",
                "preferred_storage": self.storage.pk,
                "storage_notes": "Receiver has no cold storage capacity.",
                "notes": "Can pick up after 9 AM.",
            },
        )

        self.assertEqual(FoodRequest.objects.count(), 1)

        food_request = FoodRequest.objects.get()
        self.assertRedirects(response, reverse("donations:request_thanks", args=[food_request.pk]))
        self.assertEqual(food_request.donation, self.donation)
        self.assertTrue(food_request.storage_required)
        self.assertEqual(food_request.preferred_storage, self.storage)
        self.assertEqual(food_request.status, FoodRequest.Status.SUBMITTED)
        self.assertEqual(food_request.requested_by, self.receiver)
        self.assertEqual(food_request.receiver_organization, self.receiver_organization)
        self.assertEqual(food_request.receiver_display_name, "Rae Receiver")
        self.assertEqual(food_request.receiver_organization_display, "Receiver Org")
        self.assertEqual(food_request.allocations.count(), 1)
        self.assertEqual(food_request.allocations.get().donation_food_item, self.food_item)
        self.assertEqual(food_request.allocations.get().quantity, 4)

        thanks_response = self.client.get(reverse("donations:request_thanks", args=[food_request.pk]))
        self.assertContains(thanks_response, food_request.ticket_number)
        self.assertContains(thanks_response, self.donation.ticket_number)

    def test_receiver_can_view_food_request_detail(self):
        self.client.force_login(self.receiver)
        self.select_organization(self.receiver_organization)
        self.receiver_organization.address_line_1 = "555 Receiver Road"
        self.receiver_organization.municipality = "Vancouver"
        self.receiver_organization.region = "BC"
        self.receiver_organization.postal_code = "V6B 1A1"
        self.receiver_organization.save(
            update_fields=[
                "address_line_1",
                "municipality",
                "region",
                "postal_code",
            ],
        )
        food_request = FoodRequest.objects.create(
            donation=self.donation,
            requested_by=self.receiver,
            receiver_organization=self.receiver_organization,
            storage_required=True,
            preferred_storage=self.storage,
            storage_notes="Keep cold until pickup.",
            notes="Can arrive after lunch.",
            status=FoodRequest.Status.SUBMITTED,
        )
        FoodRequestAllocation.objects.create(
            food_request=food_request,
            donation_food_item=self.food_item,
            quantity=5,
        )

        response = self.client.get(reverse("donations:request_detail", args=[food_request.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Request Details")
        self.assertContains(response, food_request.ticket_number)
        self.assertContains(response, self.donation.ticket_number)
        self.assertContains(response, "Receiver Org")
        self.assertContains(response, "555 Receiver Road, Vancouver, BC V6B 1A1")
        self.assertContains(response, "Mixed produce")
        self.assertContains(response, "5 Boxes")
        self.assertContains(response, "Keep cold until pickup.")
        self.assertContains(response, "Can arrive after lunch.")

    def test_one_receiver_limit_forces_request_to_all_remaining_food(self):
        self.donation.receiver_limit = Donation.ReceiverLimit.ONE
        self.donation.save(update_fields=["receiver_limit"])
        self.client.force_login(self.receiver)
        self.select_organization(self.receiver_organization)

        response = self.client.post(
            reverse("donations:request_create", args=[self.donation.pk]),
            {
                "allocations-TOTAL_FORMS": "1",
                "allocations-INITIAL_FORMS": "0",
                "allocations-MIN_NUM_FORMS": "1",
                "allocations-MAX_NUM_FORMS": "1000",
                "allocations-0-food_item_id": self.food_item.id,
                "allocations-0-quantity": 4,
                "storage_required": "",
                "preferred_storage": "",
                "storage_notes": "",
                "notes": "",
            },
        )

        food_request = FoodRequest.objects.get()
        self.assertRedirects(response, reverse("donations:request_thanks", args=[food_request.pk]))
        self.assertEqual(food_request.allocations.get().quantity, 12)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, Donation.Status.COMPLETED)

    def test_second_receiver_gets_all_remaining_food_for_two_receiver_limit(self):
        self.donation.receiver_limit = Donation.ReceiverLimit.TWO
        self.donation.save(update_fields=["receiver_limit"])
        first_receiver = User.objects.create_user(
            email="first-receiver@example.com",
            password="password",
            email_verified=True,
        )
        first_organization = Organization.objects.create(name="First Receiver", owner=first_receiver, is_active=True)
        FoodRequestAllocation.objects.create(
            food_request=FoodRequest.objects.create(
                donation=self.donation,
                requested_by=first_receiver,
                receiver_organization=first_organization,
            ),
            donation_food_item=self.food_item,
            quantity=5,
        )
        second_receiver = User.objects.create_user(
            email="second-receiver@example.com",
            password="password",
            email_verified=True,
        )
        second_organization = Organization.objects.create(name="Second Receiver", owner=second_receiver, is_active=True)
        grant_receiver_access(second_receiver, second_organization)
        self.client.force_login(second_receiver)
        self.select_organization(second_organization)

        response = self.client.post(
            reverse("donations:request_create", args=[self.donation.pk]),
            {
                "allocations-TOTAL_FORMS": "1",
                "allocations-INITIAL_FORMS": "0",
                "allocations-MIN_NUM_FORMS": "1",
                "allocations-MAX_NUM_FORMS": "1000",
                "allocations-0-food_item_id": self.food_item.id,
                "allocations-0-quantity": 1,
                "storage_required": "",
                "preferred_storage": "",
                "storage_notes": "",
                "notes": "",
            },
        )

        food_request = FoodRequest.objects.latest("created_at")
        self.assertRedirects(response, reverse("donations:request_thanks", args=[food_request.pk]))
        self.assertEqual(food_request.allocations.get().quantity, 7)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, Donation.Status.COMPLETED)

    def test_requesting_all_remaining_food_marks_donation_completed(self):
        self.client.force_login(self.receiver)
        self.select_organization(self.receiver_organization)

        response = self.client.post(
            reverse("donations:request_create", args=[self.donation.pk]),
            {
                "allocations-TOTAL_FORMS": "1",
                "allocations-INITIAL_FORMS": "0",
                "allocations-MIN_NUM_FORMS": "1",
                "allocations-MAX_NUM_FORMS": "1000",
                "allocations-0-food_item_id": self.food_item.id,
                "allocations-0-quantity": 12,
                "storage_required": "",
                "preferred_storage": "",
                "storage_notes": "",
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, Donation.Status.COMPLETED)

    def test_food_request_form_shows_donor_and_pickup_information(self):
        self.donation.requires_van = True
        self.donation.requires_pallet_jack = True
        self.donation.loading_dock_available = True
        self.donation.save()

        self.client.force_login(self.receiver)
        self.select_organization(self.receiver_organization)

        response = self.client.get(reverse("donations:request_create", args=[self.donation.pk]))

        self.assertContains(response, "Donation information")
        self.assertContains(response, "Description")
        self.assertContains(response, self.donation.ticket_number)
        self.assertContains(response, "Mixed produce")
        self.assertContains(response, "Supplier Org")
        self.assertContains(response, "6045550199")
        self.assertContains(response, "123 Main Street")
        self.assertContains(response, "Today")
        self.assertContains(response, "Pickup")
        self.assertContains(response, "Logistics")
        self.assertContains(response, "Dry Storage")
        self.assertContains(response, "Requires van")
        self.assertContains(response, "Pallet jack")
        self.assertContains(response, "Loading dock available")
        self.assertNotContains(response, "Forklift")
        self.assertContains(response, 'name="allocations-0-quantity"')
        self.assertContains(response, 'value="12"')

    def test_food_request_form_exposes_storage_fields_not_internal_fields(self):
        form = FoodRequestForm()

        self.assertNotIn("status", form.fields)
        self.assertNotIn("donation", form.fields)
        self.assertNotIn("intended_use", form.fields)
        self.assertNotIn("receiver_name", form.fields)
        self.assertNotIn("organization", form.fields)
        self.assertNotIn("email", form.fields)
        self.assertNotIn("phone", form.fields)
        self.assertNotIn("requested_quantity", form.fields)
        self.assertNotIn("requested_unit", form.fields)
        self.assertIn("storage_required", form.fields)
        self.assertIn("preferred_storage", form.fields)

    def test_food_request_form_only_lists_available_approved_storage(self):
        unavailable_storage = StorageLocation.objects.create(
            name="Full Storage",
            address="789 Storage Road",
            municipality="Vancouver",
            region="Metro Vancouver",
            storage_type=StorageLocation.StorageType.DRY,
            available_space=0,
            capacity_status=StorageLocation.CapacityStatus.FULL,
            approval_status=StorageLocation.ApprovalStatus.APPROVED,
            is_active=True,
        )

        form = FoodRequestForm()

        self.assertIn(self.storage, form.fields["preferred_storage"].queryset)
        self.assertNotIn(unavailable_storage, form.fields["preferred_storage"].queryset)

    def test_request_allocation_tracks_remaining_quantity_per_food_item(self):
        self.client.force_login(self.receiver)

        food_request = FoodRequest.objects.create(
            donation=self.donation,
            requested_by=self.receiver,
            receiver_organization=self.receiver_organization,
            status=FoodRequest.Status.SUBMITTED,
        )
        FoodRequestAllocation.objects.create(
            food_request=food_request,
            donation_food_item=self.food_item,
            quantity=5,
        )

        self.assertEqual(self.food_item.allocated_quantity, 5)
        self.assertEqual(self.food_item.remaining_quantity, 7)

    def test_request_allocation_formset_rejects_more_than_remaining_quantity(self):
        formset = FoodRequestAllocationFormSet(
            {
                "allocations-TOTAL_FORMS": "1",
                "allocations-INITIAL_FORMS": "0",
                "allocations-MIN_NUM_FORMS": "1",
                "allocations-MAX_NUM_FORMS": "1000",
                "allocations-0-food_item_id": self.food_item.id,
                "allocations-0-quantity": 13,
            },
            donation=self.donation,
        )

        self.assertFalse(formset.is_valid())
