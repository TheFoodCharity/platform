from django.test import TestCase
from django.urls import reverse

from .models import FoodDonation

VALID_DONATION_FORM_DATA = {
    "donor_name": "Jane Smith",
    "organization": "Neighbourhood Market",
    "email": "jane@example.com",
    "phone": "604-555-0123",
    "food_type": "produce",
    "quantity": "12 boxes",
    "best_before": "2026-06-01",
    "pickup_address": "123 Main Street, Vancouver, BC",
    "pickup_window": "Weekdays 9 AM-3 PM",
    "notes": "Please use the loading bay.",
    "confirm_safe": "on",
}


class FoodDonationPageTests(TestCase):
    def test_donation_page_renders_form(self):
        response = self.client.get(reverse("donate_food"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tell us what food you can donate.")
        self.assertContains(response, "Submit donation")

    def test_valid_donation_submission_shows_confirmation(self):
        response = self.client.post(reverse("donate_food"), VALID_DONATION_FORM_DATA)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Donation details received")
        self.assertEqual(FoodDonation.objects.count(), 1)

        donation = FoodDonation.objects.get()
        self.assertEqual(donation.donor_name, "Jane Smith")
        self.assertEqual(donation.organization, "Neighbourhood Market")
        self.assertEqual(donation.email, "jane@example.com")
        self.assertEqual(donation.food_type, "produce")
        self.assertEqual(donation.quantity, "12 boxes")
        self.assertTrue(donation.confirm_safe)

    def test_htmx_submission_returns_form_fragment(self):
        response = self.client.post(
            reverse("donate_food"),
            VALID_DONATION_FORM_DATA,
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="donation-form-panel"')
        self.assertContains(response, "Donation details received")
        self.assertNotContains(response, "<form")
        self.assertNotContains(response, "<!doctype html>")
        self.assertEqual(FoodDonation.objects.count(), 1)

    def test_invalid_donation_submission_reports_required_fields(self):
        response = self.client.post(reverse("donate_food"), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertEqual(FoodDonation.objects.count(), 0)
