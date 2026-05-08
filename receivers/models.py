from django.db import models

from donations.models import DonationTicket
from storage.models import StorageLocation


class FoodRequest(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        DECLINED = "declined", "Declined"
        FULFILLED = "fulfilled", "Fulfilled"
        CANCELLED = "cancelled", "Cancelled"

    donation_ticket = models.ForeignKey(DonationTicket, on_delete=models.CASCADE, related_name="receiver_requests")
    receiver_name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    requested_quantity = models.PositiveIntegerField()
    requested_unit = models.CharField(
        max_length=50,
        choices=DonationTicket.QuantityUnit.choices,
        default=DonationTicket.QuantityUnit.ITEMS,
    )
    storage_required = models.BooleanField(default=False)
    preferred_storage = models.ForeignKey(
        StorageLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="food_requests",
    )
    storage_notes = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Food Request"
        verbose_name_plural = "Food Requests"

    def __str__(self):
        return f"{self.receiver_name} request for {self.donation_ticket}"
