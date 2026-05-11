from typing import ClassVar

from django.db import migrations


class Migration(migrations.Migration):
    dependencies: ClassVar = [
        ("public", "0001_initial"),
    ]

    operations: ClassVar = [
        migrations.DeleteModel(
            name="FoodDonation",
        ),
    ]
