from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group as AuthGroup  # noqa: TID251


class User(AbstractUser):
    pass


class Group(AuthGroup):
    class Meta:
        proxy = True
