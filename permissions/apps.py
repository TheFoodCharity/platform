from django.apps import AppConfig


class PermissionsConfig(AppConfig):
    name = "permissions"

    def ready(self):
        from . import checks  # noqa: F401 — registers system checks
