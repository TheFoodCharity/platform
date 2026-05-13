import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_required_provenance(apps, schema_editor):
    Donation = apps.get_model("donations", "Donation")
    FoodRequest = apps.get_model("donations", "FoodRequest")
    Membership = apps.get_model("organizations", "Membership")
    only_membership = None
    active_memberships = list(Membership.objects.filter(organization__is_active=True).order_by("id")[:2])
    if len(active_memberships) == 1:
        only_membership = active_memberships[0]

    for donation in Donation.objects.filter(submitted_by__isnull=True).exclude(supplier_organization__isnull=True):
        donation.submitted_by_id = donation.supplier_organization.owner_id
        donation.save(update_fields=["submitted_by"])

    for donation in Donation.objects.filter(supplier_organization__isnull=True).exclude(submitted_by__isnull=True):
        membership = (
            Membership.objects.filter(user_id=donation.submitted_by_id, organization__is_active=True)
            .order_by("id")
            .first()
        )
        if membership is not None:
            donation.supplier_organization_id = membership.organization_id
            donation.save(update_fields=["supplier_organization"])

    if only_membership is not None:
        Donation.objects.filter(submitted_by__isnull=True).update(submitted_by_id=only_membership.user_id)
        Donation.objects.filter(supplier_organization__isnull=True).update(
            supplier_organization_id=only_membership.organization_id,
        )

    for food_request in FoodRequest.objects.filter(requested_by__isnull=True).exclude(
        receiver_organization__isnull=True
    ):
        food_request.requested_by_id = food_request.receiver_organization.owner_id
        food_request.save(update_fields=["requested_by"])

    for food_request in FoodRequest.objects.filter(receiver_organization__isnull=True).exclude(
        requested_by__isnull=True
    ):
        membership = (
            Membership.objects.filter(user_id=food_request.requested_by_id, organization__is_active=True)
            .order_by("id")
            .first()
        )
        if membership is not None:
            food_request.receiver_organization_id = membership.organization_id
            food_request.save(update_fields=["receiver_organization"])

    if only_membership is not None:
        FoodRequest.objects.filter(requested_by__isnull=True).update(requested_by_id=only_membership.user_id)
        FoodRequest.objects.filter(receiver_organization__isnull=True).update(
            receiver_organization_id=only_membership.organization_id,
        )

    untraceable_donation_ids = list(
        Donation.objects.filter(
            models.Q(submitted_by__isnull=True) | models.Q(supplier_organization__isnull=True),
        ).values_list("id", flat=True),
    )
    if untraceable_donation_ids:
        raise ValueError(
            "Cannot require donation provenance while donations have no submitter or supplier organization: "
            f"{untraceable_donation_ids}",
        )

    untraceable_food_request_ids = list(
        FoodRequest.objects.filter(
            models.Q(requested_by__isnull=True) | models.Q(receiver_organization__isnull=True),
        ).values_list("id", flat=True),
    )
    if untraceable_food_request_ids:
        raise ValueError(
            "Cannot require food request provenance while food requests have no requester or receiver organization: "
            f"{untraceable_food_request_ids}",
        )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("donations", "0013_remove_donation_pickup_window_donation_pickup_notes"),
        ("organizations", "0005_organization_address_line_1_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(backfill_required_provenance, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="donation",
            name="submitted_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="submitted_donations",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="donation",
            name="supplier_organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="donations",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="foodrequest",
            name="requested_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="food_requests",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="foodrequest",
            name="receiver_organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="food_requests",
                to="organizations.organization",
            ),
        ),
    ]
