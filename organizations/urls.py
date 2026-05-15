from django.urls import path

from .views import (
    ActivateView,
    ApplicationBasicDetailsView,
    ApplicationContactView,
    ApplicationDashboardView,
    ApplicationLocationView,
    ApplicationOperationsView,
    ApplyView,
    DispatchView,
    MemberDetailView,
    MemberRemoveView,
    MembersView,
    ProfileView,
    SelectView,
)

app_name = "organizations"

urlpatterns = [
    path("dispatch", DispatchView.as_view(), name="dispatch"),
    path("select", SelectView.as_view(), name="select"),
    path("select/<int:pk>", ActivateView.as_view(), name="activate"),
    path("apply", ApplyView.as_view(), name="apply"),
    path("application", ApplicationDashboardView.as_view(), name="application"),
    path("application/basic", ApplicationBasicDetailsView.as_view(), name="application_basic"),
    path("application/location", ApplicationLocationView.as_view(), name="application_location"),
    path("application/contact", ApplicationContactView.as_view(), name="application_contact"),
    path("application/operations", ApplicationOperationsView.as_view(), name="application_operations"),
    path("profile", ProfileView.as_view(), name="profile"),
    path("members", MembersView.as_view(), name="members"),
    path("members/<int:pk>", MemberDetailView.as_view(), name="member"),
    path("members/<int:pk>/remove", MemberRemoveView.as_view(), name="member_remove"),
]
