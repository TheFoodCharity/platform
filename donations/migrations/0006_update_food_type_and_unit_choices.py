from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("donations", "0005_donation_intake_fields_and_food_items"),
    ]

    operations = [
        migrations.AlterField(
            model_name="donation",
            name="food_category",
            field=models.CharField(
                choices=[
                    ("baked_goods", "Baked Goods"),
                    ("dairy", "Dairy"),
                    ("meat_protein", "Meat & Protein"),
                    ("non_food", "Non-Food"),
                    ("non_perishable", "Non-Perishable"),
                    ("prepared_individual", "Prepared - Individually Packaged"),
                    ("prepared_trays", "Prepared - Trays/Multi-Serving"),
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
                default="other",
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="donation",
            name="unit",
            field=models.CharField(
                choices=[
                    ("items", "Items"),
                    ("small_bags", "Small bags"),
                    ("large_bags", "Large bags"),
                    ("boxes", "Boxes"),
                    ("cases", "Cases"),
                    ("bags", "Bags"),
                    ("crates", "Crates"),
                    ("flats", "Flats"),
                    ("gallons", "Gallons"),
                    ("gaylords", "Gaylords"),
                    ("pallets", "Pallets"),
                    ("trays", "Trays"),
                    ("kg", "Kilograms"),
                    ("lb", "Pounds"),
                    ("litres", "Litres"),
                    ("other", "Other"),
                ],
                default="items",
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="donationfooditem",
            name="food_category",
            field=models.CharField(
                choices=[
                    ("baked_goods", "Baked Goods"),
                    ("dairy", "Dairy"),
                    ("meat_protein", "Meat & Protein"),
                    ("non_food", "Non-Food"),
                    ("non_perishable", "Non-Perishable"),
                    ("prepared_individual", "Prepared - Individually Packaged"),
                    ("prepared_trays", "Prepared - Trays/Multi-Serving"),
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
        migrations.AlterField(
            model_name="donationfooditem",
            name="packaging",
            field=models.CharField(
                choices=[
                    ("small_bags", "Small bags"),
                    ("large_bags", "Large bags"),
                    ("boxes", "Boxes"),
                    ("cases", "Cases"),
                    ("crates", "Crates"),
                    ("flats", "Flats"),
                    ("gallons", "Gallons"),
                    ("gaylords", "Gaylords"),
                    ("pallets", "Pallets"),
                    ("trays", "Trays"),
                    ("other", "Other"),
                ],
                max_length=50,
            ),
        ),
    ]
