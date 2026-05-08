from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CollaborationChatMessageForm, CollaborationSpaceRequestForm
from .models import CollaborationSpace, CollaborationSpaceRequest


@login_required
def collaboration_list(request):
    spaces = CollaborationSpace.objects.visible_to(request.user)
    user_requests = CollaborationSpaceRequest.objects.filter(requested_by_user=request.user)
    pending_requests = CollaborationSpaceRequest.objects.none()

    if request.user.is_staff:
        pending_requests = CollaborationSpaceRequest.objects.filter(status=CollaborationSpaceRequest.Status.PENDING)

    return render(
        request,
        "collaborations/list.html",
        {
            "spaces": spaces,
            "user_requests": user_requests,
            "pending_requests": pending_requests,
        },
    )


@login_required
def collaboration_request_create(request):
    if request.method == "POST":
        form = CollaborationSpaceRequestForm(request.POST, user=request.user)
        if form.is_valid():
            collaboration_request = form.save(commit=False)
            collaboration_request.requested_by_user = request.user
            collaboration_request.save()
            return redirect("collaborations:request_detail", request_id=collaboration_request.id)
    else:
        form = CollaborationSpaceRequestForm(user=request.user)

    return render(request, "collaborations/request_form.html", {"form": form})


@login_required
def collaboration_request_detail(request, request_id):
    collaboration_request = get_object_or_404(CollaborationSpaceRequest, pk=request_id)

    if collaboration_request.requested_by_user != request.user and not request.user.is_staff:
        raise PermissionDenied

    return render(
        request,
        "collaborations/request_detail.html",
        {
            "collaboration_request": collaboration_request,
        },
    )


@login_required
def collaboration_detail(request, space_id):
    space = get_object_or_404(CollaborationSpace.objects.visible_to(request.user), pk=space_id)
    chat_form = CollaborationChatMessageForm() if space.can_post(request.user) else None

    return render(
        request,
        "collaborations/detail.html",
        {
            "space": space,
            "chat_form": chat_form,
            "can_post": space.can_post(request.user),
        },
    )


@login_required
def collaboration_chat_message_create(request, space_id):
    space = get_object_or_404(CollaborationSpace.objects.visible_to(request.user), pk=space_id)
    if not space.can_post(request.user):
        raise PermissionDenied

    if request.method != "POST":
        return redirect("collaborations:detail", space_id=space.id)

    form = CollaborationChatMessageForm(request.POST)
    if form.is_valid():
        message = form.save(commit=False)
        message.space = space
        message.author = request.user
        message.save()
        space.last_activity_at = timezone.now()
        space.save(update_fields=["last_activity_at", "updated_at"])

    return redirect("collaborations:detail", space_id=space.id)
