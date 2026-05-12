from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import ForumPost, ForumSpace, ForumSpaceRequest


class ForumPostModelTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(
            email="author@example.com",
            first_name="Author",
            last_name="User",
            password="password",
        )
        self.moderator = get_user_model().objects.create_user(
            email="moderator@example.com",
            first_name="Moderator",
            last_name="User",
            password="password",
        )
        self.space = ForumSpace.objects.create(
            title="General member discussion",
            description="Member-only discussion space.",
            topic_category=ForumSpaceRequest.TopicCategory.GENERAL,
            visibility_level=ForumSpace.VisibilityLevel.APPROVED_MEMBERS,
            status=ForumSpace.Status.ACTIVE,
            owner=self.author,
            created_by=self.moderator,
        )

    def test_remove_marks_post_as_removed_and_sets_moderation_fields(self):
        post = ForumPost.objects.create(
            space=self.space,
            author=self.author,
            body="Initial forum post",
        )

        post.remove(self.moderator, "Removed by moderator.")
        post.refresh_from_db()

        self.assertTrue(post.is_removed)
        self.assertEqual(post.moderated_by, self.moderator)
        self.assertEqual(post.moderation_note, "Removed by moderator.")
        self.assertIsNotNone(post.moderated_at)
        self.assertLessEqual(post.moderated_at, timezone.now())
