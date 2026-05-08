from django.test import SimpleTestCase
from django.urls import reverse


class HomePageTests(SimpleTestCase):
    def test_home_page_links_to_donation_ticket_create(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Turn surplus food into community support.")
        self.assertContains(response, reverse("donations:create"))
