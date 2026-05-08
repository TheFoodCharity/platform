from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from donations.models import DonationTicket
from storage.models import StorageLocation

from .forms import FoodRequestForm
from .models import FoodRequest


class ReceiverFoodRequestTests(TestCase):
    def setUp(self):
        self.ticket = DonationTicket.objects.create(
            donor_name="Neighbourhood Market",
            donor_contact="donor@example.com",
            food_category=DonationTicket.FoodCategory.PRODUCE,
            food_type=[DonationTicket.FoodCategory.PRODUCE],
            quantity=12,
            unit=DonationTicket.QuantityUnit.BOXES,
            pickup_location="123 Main Street",
            pickup_deadline=timezone.now() + timezone.timedelta(days=1),
            storage_requirement=DonationTicket.StorageRequirement.DRY,
            status=DonationTicket.Status.SUBMITTED,
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

    def test_receiver_can_view_donation_list(self):
        response = self.client.get(reverse("receivers:donation_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Available Donations")
        self.assertContains(response, "Fresh Produce")
        self.assertContains(response, "Request this food")

    def test_receiver_can_view_donation_detail(self):
        response = self.client.get(reverse("receivers:donation_detail", args=[self.ticket.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fresh Produce")
        self.assertContains(response, "Request this food")

    def test_receiver_can_submit_food_request(self):
        response = self.client.post(
            reverse("receivers:request_create", args=[self.ticket.pk]),
            {
                "receiver_name": "City Shelter",
                "organization": "City Shelter",
                "email": "receiver@example.com",
                "phone": "604-555-0100",
                "requested_quantity": 4,
                "requested_unit": DonationTicket.QuantityUnit.BOXES,
                "storage_required": "on",
                "preferred_storage": self.storage.pk,
                "storage_notes": "Receiver has no cold storage capacity.",
                "notes": "Can pick up after 9 AM.",
            },
        )

        self.assertRedirects(response, reverse("receivers:request_thanks", args=[1]))
        self.assertEqual(FoodRequest.objects.count(), 1)

        food_request = FoodRequest.objects.get()
        self.assertEqual(food_request.donation_ticket, self.ticket)
        self.assertEqual(food_request.receiver_name, "City Shelter")
        self.assertTrue(food_request.storage_required)
        self.assertEqual(food_request.preferred_storage, self.storage)
        self.assertEqual(food_request.status, FoodRequest.Status.SUBMITTED)

    def test_food_request_form_exposes_storage_fields_not_internal_fields(self):
        form = FoodRequestForm()

        self.assertNotIn("status", form.fields)
        self.assertNotIn("donation_ticket", form.fields)
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
