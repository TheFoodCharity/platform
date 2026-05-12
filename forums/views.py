from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ForumSpaceRequestForm
from .models import ForumSpaceRequest, can_request_forum


@login_required
def forum_request_list(request):
    applications = ForumSpaceRequest.objects.select_related("requested_by_user", "space")
    if request.user.is_staff:
        applications = applications.order_by("-created_at")
    else:
        applications = applications.filter(requested_by_user=request.user).order_by("-created_at")

    return render(
        request,
        "forums/request_list.html",
        {
            "applications": applications,
            "can_request": can_request_forum(request.user),
            "forum_nav_active": "applications",
            "forum_header_title": "Forum Applications",
            "forum_header_description": "Submit, track, and review requests for new forum spaces.",
        },
    )


@login_required
def forum_request_create(request):
    if not can_request_forum(request.user):
        raise PermissionDenied

    if request.method == "POST":
        form = ForumSpaceRequestForm(request.POST, user=request.user)
        if form.is_valid():
            forum_request = form.save(commit=False)
            forum_request.requested_by_user = request.user
            forum_request.save()
            return redirect("forums:request_detail", request_id=forum_request.id)
    else:
        form = ForumSpaceRequestForm(user=request.user)

    return render(
        request,
        "forums/request_form.html",
        {
            "form": form,
            "forum_nav_active": "applications",
            "forum_header_title": "Request New Forum",
            "forum_header_description": "Submit the discussion space details for admin review.",
        },
    )


@login_required
def forum_request_detail(request, request_id):
    forum_request = get_object_or_404(ForumSpaceRequest, pk=request_id)

    if forum_request.requested_by_user != request.user and not request.user.is_staff:
        raise PermissionDenied

    return render(
        request,
        "forums/request_detail.html",
        {
            "forum_request": forum_request,
            "forum_nav_active": "applications",
            "forum_header_title": forum_request.title,
            "forum_header_description": "Forum application detail and review status.",
        },
    )
