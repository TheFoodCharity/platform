from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    name = "organizations"

    def ready(self):
        from . import checks  # noqa: F401 — registers system checks
