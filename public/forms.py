from django import forms


class FoodDonationForm(forms.Form):
    donor_name = forms.CharField(
        label="Donor name",
        max_length=120,
        widget=forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Jane Smith"}),
    )
    organization = forms.CharField(
        label="Organization",
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Optional"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "jane@example.com"}),
    )
    phone = forms.CharField(
        label="Phone",
        max_length=30,
        widget=forms.TextInput(attrs={"autocomplete": "tel", "placeholder": "604-555-0123"}),
    )
    food_type = forms.ChoiceField(
        label="Food type",
        choices=[
            ("", "Choose a category"),
            ("produce", "Fresh produce"),
            ("bakery", "Bakery"),
            ("packaged", "Packaged goods"),
            ("prepared", "Prepared meals"),
            ("frozen", "Frozen items"),
            ("other", "Other"),
        ],
    )
    quantity = forms.CharField(
        label="Approximate quantity",
        max_length=80,
        widget=forms.TextInput(attrs={"placeholder": "e.g. 12 boxes, 40 meals, 25 kg"}),
    )
    best_before = forms.DateField(
        label="Best before date",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    pickup_address = forms.CharField(
        label="Pickup address",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Street address, city, province, postal code"}),
    )
    pickup_window = forms.CharField(
        label="Pickup window",
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "e.g. Weekdays 9 AM-3 PM"}),
    )
    notes = forms.CharField(
        label="Notes",
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 4, "placeholder": "Storage needs, allergens, packaging, or access details"},
        ),
    )
    confirm_safe = forms.BooleanField(
        label="I confirm this donation has been stored safely and is fit for redistribution.",
    )
