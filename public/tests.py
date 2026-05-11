from django.test import SimpleTestCase
from django.urls import reverse


class HomePageTests(SimpleTestCase):
    def test_home_page_renders_landing_page(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The unified platform to increase food security across the globe.")
        self.assertContains(response, reverse("demo_interest"))

    def test_demo_interest_renders_feedback(self):
        response = self.client.get(reverse("demo_interest"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thanks! Demo requests are open")
