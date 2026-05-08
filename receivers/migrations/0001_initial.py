# Generated manually for the receivers app.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("donations", "0002_update_donation_ticket_form_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="FoodRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("receiver_name", models.CharField(max_length=255)),
                ("organization", models.CharField(blank=True, max_length=255)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("requested_quantity", models.PositiveIntegerField()),
                (
                    "requested_unit",
                    models.CharField(
                        choices=[
                            ("items", "Items"),
                            ("boxes", "Boxes"),
                            ("cases", "Cases"),
                            ("bags", "Bags"),
                            ("pallets", "Pallets"),
                            ("kg", "Kilograms"),
                            ("lb", "Pounds"),
                            ("litres", "Litres"),
                        ],
                        default="items",
                        max_length=50,
                    ),
                ),
                ("intended_use", models.TextField()),
                ("notes", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("submitted", "Submitted"),
                            ("approved", "Approved"),
                            ("declined", "Declined"),
                            ("fulfilled", "Fulfilled"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="submitted",
                        max_length=50,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "donation_ticket",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="receiver_requests",
                        to="donations.donationticket",
                    ),
                ),
            ],
            options={
                "verbose_name": "Food Request",
                "verbose_name_plural": "Food Requests",
                "ordering": ["-created_at"],
            },
        ),
    ]
