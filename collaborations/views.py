from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from organizations.models import Membership, Organization

from .forms import CollaborationChatMessageForm, CollaborationSpaceRequestForm
from .models import CollaborationSpace, CollaborationSpaceRequest


@login_required
def collaboration_list(request):
    spaces = (
        CollaborationSpace.objects.visible_to(request.user)
        .select_related("owner", "moderator", "created_by")
        .annotate(
            message_count=Count("chat_messages", distinct=True),
            latest_message_at=Max("chat_messages__created_at"),
            linked_record_count=Count("linked_objects", distinct=True),
        )
    )

    return render(
        request,
        "collaborations/list.html",
        {
            "spaces": spaces,
            "collaboration_nav_active": "collaborations",
            "collaboration_header_title": "Collaboration Spaces",
            "collaboration_header_description": "Browse coordination spaces by topic, region, and visibility.",
        },
    )


@login_required
def collaboration_request_list(request):
    applications = CollaborationSpaceRequest.objects.select_related("requested_by_user", "space")
    if request.user.is_staff:
        applications = applications.order_by("-created_at")
    else:
        applications = applications.filter(requested_by_user=request.user).order_by("-created_at")

    return render(
        request,
        "collaborations/request_list.html",
        {
            "applications": applications,
            "collaboration_nav_active": "applications",
            "collaboration_header_title": "Collaboration Applications",
            "collaboration_header_description": "Submit, track, and review requests for new collaboration spaces.",
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

    return render(
        request,
        "collaborations/request_form.html",
        {
            "form": form,
            "collaboration_nav_active": "applications",
            "collaboration_header_title": "Request New Collaboration",
            "collaboration_header_description": "Submit the coordination space details for admin review.",
        },
    )


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
            "collaboration_nav_active": "applications",
            "collaboration_header_title": collaboration_request.title,
            "collaboration_header_description": "Collaboration application detail and review status.",
        },
    )


def _get_collaboration_space(user, space_id):
    return get_object_or_404(CollaborationSpace.objects.visible_to(user), pk=space_id)


def _build_collaboration_detail_context(space, section):
    return {
        "space": space,
        "collaboration_detail_section": section,
        "collaboration_nav_active": "collaborations",
        "collaboration_header_title": space.title,
        "collaboration_header_description": space.purpose,
    }


@login_required
def collaboration_detail(request, space_id):
    return redirect("collaborations:detail_overview", space_id=space_id)


@login_required
def collaboration_detail_overview(request, space_id):
    space = _get_collaboration_space(request.user, space_id)

    return render(
        request,
        "collaborations/detail.html",
        {
            **_build_collaboration_detail_context(space, "overview"),
            "collaboration_detail_template": "collaborations/_detail_overview.html",
        },
    )


@login_required
def collaboration_detail_members(request, space_id):
    space = _get_collaboration_space(request.user, space_id)
    user_memberships = space.user_memberships.select_related("user").filter(left_at__isnull=True)
    organization_memberships = list(
        space.organization_memberships.select_related("organization").filter(left_at__isnull=True)
    )
    organization_ids = {membership.organization_id for membership in organization_memberships}
    participant_org_memberships = (
        Membership.objects.filter(
            user_id__in=user_memberships.values_list("user_id", flat=True),
            organization__is_active=True,
            organization__status__in=[
                Organization.Status.APPROVED,
                Organization.Status.APPROVED_LIMITED,
            ],
        )
        .select_related("organization")
        .order_by("organization__name")
    )
    participant_orgs = {}
    participant_space_orgs = {}
    for membership in participant_org_memberships:
        participant_orgs.setdefault(membership.user_id, membership.organization)
        if membership.organization_id in organization_ids:
            participant_space_orgs.setdefault(membership.user_id, membership.organization)

    member_rows = []
    for membership in user_memberships:
        organization = participant_space_orgs.get(membership.user_id) or participant_orgs.get(membership.user_id)
        member_rows.append(
            {
                "name": membership.user.get_full_name() or str(membership.user),
                "organization_name": organization.name if organization else "Unaffiliated",
                "access": "Direct user",
                "role": membership.get_role_display(),
            }
        )
    for membership in organization_memberships:
        member_rows.append(
            {
                "name": "Organization members",
                "organization_name": membership.organization.name,
                "access": "Organization",
                "role": membership.get_role_display(),
            }
        )

    return render(
        request,
        "collaborations/detail.html",
        {
            **_build_collaboration_detail_context(space, "members"),
            "collaboration_detail_template": "collaborations/_detail_members.html",
            "member_rows": member_rows,
        },
    )


@login_required
def collaboration_detail_links(request, space_id):
    space = _get_collaboration_space(request.user, space_id)
    linked_objects = space.linked_objects.select_related("content_type")

    return render(
        request,
        "collaborations/detail.html",
        {
            **_build_collaboration_detail_context(space, "links"),
            "collaboration_detail_template": "collaborations/_detail_links.html",
            "linked_objects": linked_objects,
        },
    )


@login_required
def collaboration_detail_chat(request, space_id):
    space = _get_collaboration_space(request.user, space_id)
    messages = space.chat_messages.select_related("author").order_by("created_at")

    return render(
        request,
        "collaborations/detail.html",
        {
            **_build_collaboration_detail_context(space, "chat"),
            "collaboration_detail_template": "collaborations/_detail_chat.html",
            "messages": messages,
            "chat_form": CollaborationChatMessageForm() if space.can_post(request.user) else None,
            "can_post": space.can_post(request.user),
        },
    )


@login_required
def collaboration_detail_admin(request, space_id):
    if not request.user.is_staff:
        raise PermissionDenied

    space = _get_collaboration_space(request.user, space_id)

    return render(
        request,
        "collaborations/detail.html",
        {
            **_build_collaboration_detail_context(space, "admin"),
            "collaboration_detail_template": "collaborations/_detail_admin.html",
        },
    )


@login_required
def collaboration_chat_message_create(request, space_id):
    space = _get_collaboration_space(request.user, space_id)
    if not space.can_post(request.user):
        raise PermissionDenied

    if request.method != "POST":
        return redirect("collaborations:detail_chat", space_id=space.id)

    form = CollaborationChatMessageForm(request.POST)
    if form.is_valid():
        message = form.save(commit=False)
        message.space = space
        message.author = request.user
        message.save()
        space.last_activity_at = timezone.now()
        space.save(update_fields=["last_activity_at", "updated_at"])

    return redirect("collaborations:detail_chat", space_id=space.id)
