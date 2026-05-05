from django.urls import path
from django.views.generic import TemplateView

from .views import DispatchView

app_name = "organizations"

urlpatterns = [
    path("", TemplateView.as_view(template_name="organizations/select.html"), name="select"),
    path("dispatch", DispatchView.as_view(), name="dispatch"),
    path("apply", TemplateView.as_view(template_name="organizations/apply.html"), name="apply"),
]
