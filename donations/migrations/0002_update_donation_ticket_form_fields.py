import json

from django.db import migrations, models


def wrap_existing_food_type_values(apps, _schema_editor):
    donation_ticket = apps.get_model("donations", "DonationTicket")

    for ticket in donation_ticket.objects.all():
        if ticket.food_type:
            ticket.food_type = json.dumps([ticket.food_type])
            ticket.save(update_fields=["food_type"])


class Migration(migrations.Migration):
    dependencies = [
        ("donations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(wrap_existing_food_type_values, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="donationticket",
            name="food_type",
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name="donationticket",
            name="unit",
            field=models.CharField(
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
        migrations.AddField(
            model_name="donationticket",
            name="estimated_weight_unit",
            field=models.CharField(
                choices=[
                    ("kg", "Kilograms"),
                    ("lb", "Pounds"),
                ],
                default="lb",
                max_length=20,
            ),
        ),
    ]
