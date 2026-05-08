import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("receivers", "0001_initial"),
        ("storage", "0002_alter_storagelocation_options_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="foodrequest",
            name="intended_use",
        ),
        migrations.AddField(
            model_name="foodrequest",
            name="storage_required",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="foodrequest",
            name="storage_notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="foodrequest",
            name="preferred_storage",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="food_requests",
                to="storage.storagelocation",
            ),
        ),
    ]
