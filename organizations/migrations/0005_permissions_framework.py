import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0004_organizationapplication_form_statuses"),
    ]

    operations = [
        migrations.CreateModel(
            name="Permission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=200, unique=True)),
                ("description", models.CharField(blank=True, max_length=500)),
            ],
            options={
                "verbose_name": "permission",
                "verbose_name_plural": "permissions",
                "ordering": ("code",),
            },
        ),
        migrations.CreateModel(
            name="PermissionGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("scope", models.PositiveSmallIntegerField(choices=[(1, "User role"), (2, "Organization capability")])),
                ("description", models.CharField(blank=True, max_length=500)),
                ("is_system", models.BooleanField(default=False)),
                (
                    "permissions",
                    models.ManyToManyField(
                        blank=True,
                        related_name="groups",
                        to="organizations.permission",
                    ),
                ),
            ],
            options={
                "verbose_name": "permission group",
                "verbose_name_plural": "permission groups",
                "ordering": ("scope", "name"),
                "unique_together": {("name", "scope")},
            },
        ),
        migrations.AddField(
            model_name="organization",
            name="capabilities",
            field=models.ManyToManyField(
                blank=True,
                help_text="The capabilities this organization has been granted.",
                limit_choices_to={"scope": 2},
                related_name="organizations",
                to="organizations.permissiongroup",
                verbose_name="capabilities",
            ),
        ),
        migrations.AddField(
            model_name="organization",
            name="permission_version",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="membership",
            name="role",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"scope": 1},
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="memberships",
                to="organizations.permissiongroup",
                verbose_name="role",
            ),
        ),
        migrations.AddField(
            model_name="membership",
            name="permission_version",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name="OrganizationPermissionOverride",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("effect", models.PositiveSmallIntegerField(choices=[(1, "Allow"), (2, "Deny")])),
                (
                    "permission",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="organizations.permission"),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="permission_overrides",
                        to="organizations.organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "organization permission override",
                "verbose_name_plural": "organization permission overrides",
                "unique_together": {("organization", "permission")},
            },
        ),
        migrations.CreateModel(
            name="MembershipPermissionOverride",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("effect", models.PositiveSmallIntegerField(choices=[(1, "Allow"), (2, "Deny")])),
                (
                    "permission",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="organizations.permission"),
                ),
                (
                    "membership",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="permission_overrides",
                        to="organizations.membership",
                    ),
                ),
            ],
            options={
                "verbose_name": "membership permission override",
                "verbose_name_plural": "membership permission overrides",
                "unique_together": {("membership", "permission")},
            },
        ),
    ]
