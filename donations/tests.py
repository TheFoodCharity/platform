from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from organizations.models import Membership, Organization
from storage.models import StorageLocation

from .forms import FOOD_TYPE_INTAKE, DonationFoodItemFormSet, DonationForm, FoodRequestForm
from .models import Donation, DonationFoodItem, FoodRequest

User = get_user_model()


class DonationFormTests(SimpleTestCase):
    def test_intake_form_has_reference_style_sections(self):
        form = DonationForm()

        self.assertIn("company_name", form.fields)
        self.assertIn("pickup_day", form.fields)
        self.assertIn("pickup_ready_time", form.fields)
        self.assertIn("pickup_end_time", form.fields)
        self.assertNotIn("pickup_deadline", form.fields)
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

    def test_unit_fields_use_dropdown_choices(self):
        form = DonationForm()

        self.assertEqual(list(form.fields["pickup_day"].choices), list(Donation.PickupDay.choices))
        self.assertEqual(list(form.fields["pickup_ready_time"].choices), list(Donation.PickupReadyTime.choices))
        self.assertEqual(list(form.fields["pickup_end_time"].choices), list(Donation.PickupEndTime.choices))


class DonationIntakeViewTests(TestCase):
    def donation_post_data(self):
        data = {
            "company_name": "Neighbourhood Market",
            "address_1": "123 Main Street",
            "address_2": "",
            "city": "Vancouver",
            "province_or_state": "BC",
            "postal_code": "V5K 0A1",
            "donor_name": "Jane Smith",
            "donor_contact": "Jane Smith",
            "contact_email": "jane@example.com",
            "contact_phone": "604-555-0100",
            "pickup_location": "123 Main Street",
            "pickup_day": Donation.PickupDay.TODAY,
            "pickup_ready_time": Donation.PickupReadyTime.READY_NOW,
            "pickup_end_time": Donation.PickupEndTime.BEFORE_5PM,
            "pickup_window": "Today before 5pm",
            "storage_requirement": Donation.StorageRequirement.DRY,
            "people_fed_estimate": Donation.PeopleFedEstimate.FIFTY,
            "fits_in_car": "True",
            "food_safety_agreement": "on",
            "special_handling_notes": "",
            "chain_of_custody_notes": "",
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
        response = self.client.post(reverse("donations:create"), self.donation_post_data())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Donation.objects.count(), 1)
        self.assertEqual(DonationFoodItem.objects.count(), 1)

        donation = Donation.objects.get()
        self.assertEqual(donation.company_name, "Neighbourhood Market")
        self.assertEqual(donation.food_category, Donation.FoodCategory.PRODUCE)
        self.assertEqual(donation.quantity, 12)
        self.assertIsNotNone(donation.pickup_deadline)

    def test_logged_in_user_donation_is_attached_to_user_and_organization(self):
        user = User.objects.create_user(
            email="supplier@example.com",
            password="password",
            first_name="Sam",
            last_name="Supplier",
            email_verified=True,
        )
        organization = Organization.objects.create(name="Supplier Org", owner=user, is_active=True)
        Membership.objects.create(user=user, organization=organization)
        self.client.force_login(user)

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
            municipality="Vancouver",
            region="BC",
            email="donations@supplier.example",
            phone="6045550100",
        )
        Membership.objects.create(user=user, organization=organization)
        self.client.force_login(user)

        response = self.client.get(reverse("donations:create"))

        self.assertContains(response, 'value="Supplier Org"')
        self.assertContains(response, 'value="Vancouver"')
        self.assertContains(response, 'value="BC"')
        self.assertContains(response, 'value="donations@supplier.example"')
        self.assertContains(response, 'value="6045550100"')
        self.assertContains(response, 'value="Sam Supplier"')

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
        Membership.objects.create(user=owner, organization=organization)
        Membership.objects.create(user=member, organization=organization)
        Membership.objects.create(user=other_user, organization=other_organization)
        Donation.objects.create(
            donor_name="Shared Donation",
            donor_contact="owner@example.com",
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
        Donation.objects.create(
            donor_name="Hidden Donation",
            donor_contact="other@example.com",
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

        response = self.client.get(reverse("donations:list"))

        self.assertContains(response, "Shared Donation")
        self.assertNotContains(response, "Hidden Donation")


class FoodRequestTests(TestCase):
    def setUp(self):
        self.donation = Donation.objects.create(
            donor_name="Neighbourhood Market",
            donor_contact="donor@example.com",
            food_category=Donation.FoodCategory.PRODUCE,
            food_type=[Donation.FoodCategory.PRODUCE],
            quantity=12,
            unit=Donation.QuantityUnit.BOXES,
            pickup_location="123 Main Street",
            pickup_deadline=timezone.now() + timezone.timedelta(days=1),
            storage_requirement=Donation.StorageRequirement.DRY,
            status=Donation.Status.SUBMITTED,
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

    def test_receiver_can_view_available_donation_list(self):
        response = self.client.get(reverse("donations:available_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Available Donations")
        self.assertContains(response, "Fresh Produce")
        self.assertContains(response, "Request this food")

    def test_receiver_can_view_available_donation_detail(self):
        response = self.client.get(reverse("donations:available_detail", args=[self.donation.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fresh Produce")
        self.assertContains(response, "Request this food")

    def test_receiver_can_submit_food_request(self):
        user = User.objects.create_user(
            email="receiver-user@example.com",
            password="password",
            first_name="Rae",
            last_name="Receiver",
            email_verified=True,
        )
        organization = Organization.objects.create(name="Receiver Org", owner=user, is_active=True)
        Membership.objects.create(user=user, organization=organization)
        self.client.force_login(user)

        response = self.client.post(
            reverse("donations:request_create", args=[self.donation.pk]),
            {
                "receiver_name": "City Shelter",
                "organization": "City Shelter",
                "email": "receiver@example.com",
                "phone": "604-555-0100",
                "requested_quantity": 4,
                "requested_unit": Donation.QuantityUnit.BOXES,
                "storage_required": "on",
                "preferred_storage": self.storage.pk,
                "storage_notes": "Receiver has no cold storage capacity.",
                "notes": "Can pick up after 9 AM.",
            },
        )

        self.assertRedirects(response, reverse("donations:request_thanks", args=[1]))
        self.assertEqual(FoodRequest.objects.count(), 1)

        food_request = FoodRequest.objects.get()
        self.assertEqual(food_request.donation, self.donation)
        self.assertEqual(food_request.receiver_name, "City Shelter")
        self.assertTrue(food_request.storage_required)
        self.assertEqual(food_request.preferred_storage, self.storage)
        self.assertEqual(food_request.status, FoodRequest.Status.SUBMITTED)
        self.assertEqual(food_request.requested_by, user)
        self.assertEqual(food_request.receiver_organization, organization)

    def test_food_request_form_exposes_storage_fields_not_internal_fields(self):
        form = FoodRequestForm()

        self.assertNotIn("status", form.fields)
        self.assertNotIn("donation", form.fields)
        self.assertNotIn("intended_use", form.fields)
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
