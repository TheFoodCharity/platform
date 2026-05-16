from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("donations", "0016_remove_donation_handling_notes"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="donation",
            name="assigned_storage",
        ),
    ]
