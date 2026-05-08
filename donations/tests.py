from django import forms
from django.test import SimpleTestCase

from .forms import DonationTicketForm
from .models import DonationTicket


class DonationTicketFormTests(SimpleTestCase):
    def test_food_type_allows_multiple_choices(self):
        form = DonationTicketForm()

        self.assertIsInstance(form.fields["food_type"], forms.MultipleChoiceField)
        self.assertTrue(form.fields["food_type"].widget.allow_multiple_selected)

    def test_status_is_not_user_editable(self):
        form = DonationTicketForm()

        self.assertNotIn("status", form.fields)

    def test_unit_fields_use_dropdown_choices(self):
        form = DonationTicketForm()

        self.assertEqual(list(form.fields["unit"].choices), list(DonationTicket.QuantityUnit.choices))
        self.assertEqual(list(form.fields["estimated_weight_unit"].choices), list(DonationTicket.WeightUnit.choices))
