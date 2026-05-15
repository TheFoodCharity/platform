from django.core.exceptions import ImproperlyConfigured
from django.db import models


class TenantScopedQuerySet(models.QuerySet):
    """A queryset that can filter to the acting organization.

    The model must declare a ``tenant_field`` class attribute naming the ForeignKey
    that points at the owning ``organizations.Organization``. Without it, calling
    ``for_request`` or ``for_organization`` raises ``ImproperlyConfigured`` so the
    misconfiguration is caught at first use rather than silently bypassed.
    """

    def _tenant_field(self) -> str:
        field = getattr(self.model, "tenant_field", None)
        if not field:
            raise ImproperlyConfigured(
                f"{self.model.__name__} uses TenantScopedManager but does not declare a "
                "`tenant_field` class attribute pointing at its owning Organization ForeignKey."
            )
        return field

    def for_request(self, request):
        """Filter rows to the organization the request user is acting as.

        Returns none() when there is no acting organization, all rows for staff acting
        in an organization (matching the staff bypass in permission checks), and the
        tenant-filtered queryset otherwise.
        """
        organization = getattr(request, "organization", None)
        if organization is None:
            return self.none()
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.is_staff:
            return self.all()
        return self.filter(**{self._tenant_field(): organization})

    def for_organization(self, organization):
        """Filter rows by a specific organization. Use outside the request cycle."""
        if organization is None:
            return self.none()
        return self.filter(**{self._tenant_field(): organization})


class TenantScopedManager(models.Manager.from_queryset(TenantScopedQuerySet)):
    pass
