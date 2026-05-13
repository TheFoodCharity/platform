from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from organizations.models import Membership, Organization

from .forms import ForumPostForm, ForumSpaceRequestForm
from .models import (
    ForumPost,
    ForumSpace,
    ForumSpaceOrganizationMembership,
    ForumSpaceRequest,
    ForumSpaceUserMembership,
    can_request_forum,
)


@login_required
def forum_list(request):
    spaces = (
        ForumSpace.objects.visible_to(request.user)
        .select_related("owner", "moderator")
        .annotate(
            post_count=Count("posts", filter=Q(posts__is_removed=False)),
            latest_post_at=Max("posts__created_at", filter=Q(posts__is_removed=False)),
        )
    )

    return render(
        request,
        "forums/list.html",
        {
            "spaces": spaces,
            "can_request": can_request_forum(request.user),
            "forum_nav_active": "forums",
            "forum_header_title": "Forum Spaces",
            "forum_header_description": "Browse member-only discussion spaces by topic, region, and visibility.",
        },
    )


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


def _get_forum_space(user, space_id):
    return get_object_or_404(ForumSpace.objects.visible_to(user), pk=space_id)


def _build_forum_detail_context(space, section):
    return {
        "space": space,
        "forum_detail_section": section,
        "forum_nav_active": "forums",
        "forum_header_title": space.title,
        "forum_header_description": space.description,
    }


def _build_forum_participant_context(space, participant_ids):
    user_memberships = list(space.user_memberships.select_related("user").filter(left_at__isnull=True))
    member_ids = {membership.user_id for membership in user_memberships}
    participant_ids = set(participant_ids) | member_ids

    forum_user_roles = {
        membership.user_id: membership.get_role_display()
        for membership in ForumSpaceUserMembership.objects.filter(
            space=space,
            user_id__in=participant_ids,
            left_at__isnull=True,
        )
    }
    forum_org_memberships = list(
        ForumSpaceOrganizationMembership.objects.filter(space=space, left_at__isnull=True).select_related(
            "organization"
        )
    )
    forum_org_ids = {membership.organization_id for membership in forum_org_memberships}
    forum_org_roles = {
        membership.organization_id: membership.get_role_display() for membership in forum_org_memberships
    }
    participant_org_memberships = (
        Membership.objects.filter(
            user_id__in=participant_ids,
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
    participant_forum_orgs = {}
    for membership in participant_org_memberships:
        participant_orgs.setdefault(membership.user_id, membership.organization)
        if membership.organization_id in forum_org_ids:
            participant_forum_orgs.setdefault(membership.user_id, membership.organization)

    return {
        "user_memberships": user_memberships,
        "forum_user_roles": forum_user_roles,
        "forum_org_roles": forum_org_roles,
        "participant_orgs": participant_orgs,
        "participant_forum_orgs": participant_forum_orgs,
    }


def _forum_role_for_user(user, participant_context):
    organization = participant_context["participant_forum_orgs"].get(user.id) or participant_context[
        "participant_orgs"
    ].get(user.id)
    role = participant_context["forum_user_roles"].get(user.id)
    if not role and organization:
        role = participant_context["forum_org_roles"].get(organization.id)
    if not role and user.is_staff:
        role = "Staff"
    return role or "Member", organization


@login_required
def forum_detail_posts(request, space_id):
    space = _get_forum_space(request.user, space_id)
    posts = space.posts.select_related("author").order_by("created_at")
    if not request.user.is_staff:
        posts = posts.filter(is_removed=False)
    posts = list(posts)

    author_ids = {post.author_id for post in posts}
    participant_context = _build_forum_participant_context(space, author_ids | {request.user.id})

    post_rows = []
    for post in posts:
        author_role, organization = _forum_role_for_user(post.author, participant_context)
        post_rows.append(
            {
                "post": post,
                "author_name": post.author.get_full_name() or str(post.author),
                "author_role": author_role,
                "organization": organization,
            }
        )

    current_user_role, current_user_organization = _forum_role_for_user(request.user, participant_context)

    return render(
        request,
        "forums/detail.html",
        {
            **_build_forum_detail_context(space, "posts"),
            "forum_detail_template": "forums/_detail_posts.html",
            "post_rows": post_rows,
            "post_form": ForumPostForm() if space.can_post(request.user) else None,
            "can_post": space.can_post(request.user),
            "current_user_role": current_user_role,
            "current_user_organization": current_user_organization,
        },
    )


@login_required
def forum_detail_members(request, space_id):
    space = _get_forum_space(request.user, space_id)
    participant_context = _build_forum_participant_context(space, {request.user.id})

    member_rows = []
    for membership in participant_context["user_memberships"]:
        user = membership.user
        organization = participant_context["participant_forum_orgs"].get(user.id) or participant_context[
            "participant_orgs"
        ].get(user.id)
        member_rows.append(
            {
                "name": user.get_full_name() or str(user),
                "organization": organization,
                "role": membership.get_role_display(),
            }
        )

    return render(
        request,
        "forums/detail.html",
        {
            **_build_forum_detail_context(space, "members"),
            "forum_detail_template": "forums/_detail_members.html",
            "member_rows": member_rows,
        },
    )


@login_required
def forum_detail_admin(request, space_id):
    if not request.user.is_staff:
        raise PermissionDenied

    space = _get_forum_space(request.user, space_id)
    return render(
        request,
        "forums/detail.html",
        {
            **_build_forum_detail_context(space, "admin"),
            "forum_detail_template": "forums/_detail_admin.html",
        },
    )


@login_required
def forum_post_create(request, space_id):
    space = _get_forum_space(request.user, space_id)
    if not space.can_post(request.user):
        raise PermissionDenied

    if request.method != "POST":
        return redirect("forums:detail_posts", space_id=space.id)

    form = ForumPostForm(request.POST)
    if form.is_valid():
        post: ForumPost = form.save(commit=False)
        post.space = space
        post.author = request.user
        post.save()
        space.last_activity_at = timezone.now()
        space.save(update_fields=["last_activity_at", "updated_at"])

    return redirect("forums:detail_posts", space_id=space.id)
