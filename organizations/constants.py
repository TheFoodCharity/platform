from django.db import models


class Scope(models.IntegerChoices):
    USER = 1, "User role"
    ORGANIZATION = 2, "Organization capability"


class SystemRole:
    FOOD_CHARITY_ADMIN = "Food Charity Admin"
    ORGANIZATION_MANAGER = "Organization Manager"
    ORGANIZATION_USER = "Organization User"


class SystemCapability:
    FOOD_DONOR = "Food Donor"
    FOOD_RECEIVER = "Food Receiver"
    STORAGE_PROVIDER = "Storage Provider"
    COLLABORATION_PARTICIPANT = "Collaboration Participant"
    FORUM_PARTICIPANT = "Forum Participant"
    READ_ONLY = "Read-Only"
