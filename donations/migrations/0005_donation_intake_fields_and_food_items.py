import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("donations", "0004_foodrequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="donation",
            name="company_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="donation",
            name="address_1",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="donation",
            name="address_2",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="donation",
            name="city",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="donation",
            name="province_or_state",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="donation",
            name="postal_code",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="donation",
            name="contact_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="donation",
            name="contact_phone",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="donation",
            name="pickup_day",
            field=models.CharField(
                choices=[
                    ("today", "Today"),
                    ("tomorrow", "Tomorrow"),
                ],
                default="today",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="donation",
            name="pickup_ready_time",
            field=models.CharField(
                choices=[
                    ("ready_now", "It is packaged and ready to go"),
                    ("12pm", "From 12pm"),
                    ("1pm", "From 1pm"),
                    ("2pm", "From 2pm"),
                    ("3pm", "From 3pm"),
                ],
                default="ready_now",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="donation",
            name="pickup_end_time",
            field=models.CharField(
                choices=[
                    ("before_2pm", "Before 2pm"),
                    ("before_3pm", "Before 3pm"),
                    ("before_4pm", "Before 4pm"),
                    ("before_5pm", "Before 5pm"),
                ],
                default="before_5pm",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="donation",
            name="people_fed_estimate",
            field=models.PositiveIntegerField(
                blank=True,
                choices=[
                    (5, "5"),
                    (10, "10"),
                    (15, "15"),
                    (20, "20"),
                    (25, "25"),
                    (30, "30"),
                    (40, "40"),
                    (50, "50"),
                    (75, "75"),
                    (100, "100"),
                    (150, "150"),
                    (200, "200"),
                    (300, "300"),
                ],
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="donation",
            name="fits_in_car",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="donation",
            name="food_safety_agreement",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="donation",
            name="other_information",
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name="DonationFoodItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "food_category",
                    models.CharField(
                        choices=[
                            ("produce", "Fresh Produce"),
                            ("refrigerated", "Perishable Refrigerated"),
                            ("frozen", "Frozen"),
                            ("dry_goods", "Dry Goods"),
                            ("canned", "Canned/Shelf-Stable"),
                            ("prepared", "Prepared Food"),
                            ("bulk", "Bulk Ingredients"),
                            ("palletized", "Palletized Goods"),
                            ("mixed", "Small Mixed Donation"),
                            ("other", "Other"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "packaging",
                    models.CharField(
                        choices=[
                            ("small_bags", "Small bags"),
                            ("large_bags", "Large bags"),
                            ("boxes", "Boxes"),
                            ("cases", "Cases"),
                            ("crates", "Crates"),
                            ("flats", "Flats"),
                            ("gallons", "Gallons"),
                            ("pallets", "Pallets"),
                            ("trays", "Trays"),
                            ("other", "Other"),
                        ],
                        max_length=50,
                    ),
                ),
                ("quantity", models.PositiveIntegerField()),
                ("description", models.CharField(blank=True, max_length=255)),
                (
                    "donation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="food_items",
                        to="donations.donation",
                    ),
                ),
            ],
            options={
                "verbose_name": "Donation Food Item",
                "verbose_name_plural": "Donation Food Items",
                "ordering": ["id"],
            },
        ),
    ]
