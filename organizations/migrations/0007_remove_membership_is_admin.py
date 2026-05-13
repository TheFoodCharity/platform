from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0006_seed_permission_groups"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="membership",
            name="is_admin",
        ),
    ]
