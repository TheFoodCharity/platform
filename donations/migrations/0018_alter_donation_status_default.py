from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("donations", "0017_remove_donation_assigned_storage"),
    ]

    operations = [
        migrations.AlterField(
            model_name="donation",
            name="status",
            field=models.CharField(
                choices=[
                    ("submitted", "Submitted"),
                    ("available", "Available"),
                    ("in_transit", "In Transit"),
                    ("delivered", "Delivered"),
                    ("completed", "Completed"),
                    ("expired", "Expired"),
                    ("cancelled", "Cancelled"),
                ],
                default="available",
                max_length=50,
            ),
        ),
    ]
