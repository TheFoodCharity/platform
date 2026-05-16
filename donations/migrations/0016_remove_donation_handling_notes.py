from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("donations", "0015_donation_receiver_preferences"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="donation",
            name="chain_of_custody_notes",
        ),
        migrations.RemoveField(
            model_name="donation",
            name="special_handling_notes",
        ),
        migrations.AlterField(
            model_name="donation",
            name="receiver_limit",
            field=models.CharField(
                "maximum number of receivers",
                choices=[
                    ("one", "1 receiver only"),
                    ("two", "Maximum 2 receivers"),
                    ("no_limit", "No limit"),
                ],
                default="no_limit",
                max_length=20,
            ),
        ),
    ]
