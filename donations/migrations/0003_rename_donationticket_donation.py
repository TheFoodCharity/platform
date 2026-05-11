from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("donations", "0002_update_donation_ticket_form_fields"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="DonationTicket",
            new_name="Donation",
        ),
        migrations.AlterModelOptions(
            name="donation",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Donation",
                "verbose_name_plural": "Donations",
            },
        ),
        migrations.AlterModelTable(
            name="donation",
            table="donations_donationticket",
        ),
    ]
