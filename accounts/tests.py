from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import LearnerProfile, TopicProgress
from datetime import date, timedelta

User = get_user_model()

class AccountsConfigTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='sammy',
            password='secretpassword123',
            role='child'
        )
        self.profile = LearnerProfile.objects.create(
            user=self.user,
            age=8,
            learning_style='visual'
        )

    def test_custom_user_role(self):
        """Verify role fields are saved correctly."""
        self.assertEqual(self.user.role, 'child')
        self.assertIsNone(self.user.parent)

    def test_learner_profile_creation(self):
        """Verify LearnerProfile fields default values."""
        self.assertEqual(self.profile.xp, 0)
        self.assertEqual(self.profile.coins, 0)
        self.assertEqual(self.profile.streak, 0)
        self.assertEqual(self.profile.avatar, 'buddy_normal')
        self.assertEqual(self.profile.selected_theme, 'theme-light')

    def test_topic_progress_creation(self):
        """Verify TopicProgress database mappings."""
        progress = TopicProgress.objects.create(
            profile=self.profile,
            subject='math',
            topic='fractions',
            mastery_score=75.0,
            confidence=80.0
        )
        self.assertEqual(progress.mastery_score, 75.0)
        self.assertEqual(progress.confidence, 80.0)
        self.assertEqual(self.profile.topic_progress.count(), 1)
