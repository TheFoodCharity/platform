from typing import ClassVar

from django.db import models


class FoodHelpLocation(models.Model):
    SERVICE_TYPE_CHOICES: ClassVar = [
        ("food_bank", "Food Bank"),
        ("food_hub", "Food Hub"),
        ("meal_program", "Meal Program"),
        ("community_pantry", "Community Pantry"),
        ("shelter", "Shelter"),
        ("senior_support", "Senior Food Support"),
        ("youth_family", "Youth / Family Support"),
        ("indigenous_program", "Indigenous-led Program"),
        ("emergency_food", "Emergency Food Support"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=160)
    service_type = models.CharField(max_length=40, choices=SERVICE_TYPE_CHOICES)

    address = models.TextField(blank=True)
    municipality = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    service_area = models.CharField(max_length=160, blank=True)

    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    days_open = models.CharField(max_length=120, blank=True)
    hours_open = models.CharField(max_length=120, blank=True)

    eligibility_requirements = models.TextField(blank=True)
    accessibility_notes = models.TextField(blank=True)
    languages_served = models.CharField(max_length=160, blank=True)

    appointment_required = models.BooleanField(default=False)
    walk_ins_accepted = models.BooleanField(default=True)
    registration_required = models.BooleanField(default=False)

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    is_public = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)

    last_verified = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("municipality", "name")

    def __str__(self):
        return self.name
