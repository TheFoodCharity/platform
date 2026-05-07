from django.urls import path
from django.views.generic import TemplateView

from .views import (
    ApplicationBasicDetailsView,
    ApplicationContactView,
    ApplicationDashboardView,
    ApplicationLocationView,
    ApplicationOperationsView,
    ApplyView,
    DispatchView,
)

app_name = "organizations"

urlpatterns = [
    path("", TemplateView.as_view(template_name="organizations/select.html"), name="select"),
    path("dispatch", DispatchView.as_view(), name="dispatch"),
    path("apply", ApplyView.as_view(), name="apply"),
    path("<int:pk>/application", ApplicationDashboardView.as_view(), name="application"),
    path("<int:pk>/application/basic", ApplicationBasicDetailsView.as_view(), name="application_basic"),
    path("<int:pk>/application/location", ApplicationLocationView.as_view(), name="application_location"),
    path("<int:pk>/application/contact", ApplicationContactView.as_view(), name="application_contact"),
    path("<int:pk>/application/operations", ApplicationOperationsView.as_view(), name="application_operations"),
]
