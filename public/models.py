from typing import ClassVar

from django.db import models


class FoodDonation(models.Model):
    FOOD_TYPE_CHOICES: ClassVar = [
        ("produce", "Fresh produce"),
        ("bakery", "Bakery"),
        ("packaged", "Packaged goods"),
        ("prepared", "Prepared meals"),
        ("frozen", "Frozen items"),
        ("other", "Other"),
    ]

    donor_name = models.CharField(max_length=120)
    organization = models.CharField(max_length=120, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    food_type = models.CharField(max_length=20, choices=FOOD_TYPE_CHOICES)
    quantity = models.CharField(max_length=80)
    best_before = models.DateField(null=True, blank=True)
    pickup_address = models.TextField()
    pickup_window = models.CharField(max_length=120)
    notes = models.TextField(blank=True)
    confirm_safe = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.donor_name} - {self.quantity} of {self.get_food_type_display()}"
