import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("donations", "0014_require_donation_and_request_provenance"),
        ("organizations", "0005_organization_address_line_1_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="donation",
            name="preferred_receiver_organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="preferred_donations",
                to="organizations.organization",
                verbose_name="preferred receiver",
            ),
        ),
        migrations.AddField(
            model_name="donation",
            name="receiver_limit",
            field=models.CharField(
                "maximum number of receivers",
                choices=[
                    ("one", "1 receiver only"),
                    ("two", "Maximum 2 receivers"),
                    ("no_limit", "No limit"),
                ],
                default="one",
                max_length=20,
            ),
        ),
    ]
