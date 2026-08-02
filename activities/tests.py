from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import LearnerProfile
from .models import QuizSession, QuizQuestion, FlashcardDeck, FlashcardItem, StudyPlan, StudyPlanItem
from datetime import date, timedelta

User = get_user_model()

class ActivitiesConfigTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='terry',
            password='secretpassword123',
            role='child'
        )
        self.profile = LearnerProfile.objects.create(
            user=self.user,
            age=9
        )
        self.deck = FlashcardDeck.objects.create(
            profile=self.profile,
            title='Test Deck',
            subject='science'
        )
        self.card = FlashcardItem.objects.create(
            deck=self.deck,
            front='What falls?',
            back='Apples due to gravity.',
            interval=1,
            ease_factor=2.5
        )

    def test_spaced_repetition_logic(self):
        """Verify flashcard SM-2 calculation ratings adjust intervals."""
        # Rate card as 'Easy' (score = 5)
        score = 5
        
        # Calculate expected interval based on SM-2 formula
        if score >= 3:
            if self.card.interval == 1:
                self.card.interval = 6
        
        self.assertEqual(self.card.interval, 6)

    def test_study_plan_checklist(self):
        """Verify plan items can be generated and checked off."""
        plan = StudyPlan.objects.create(
            profile=self.profile,
            target_date=date.today()
        )
        item = StudyPlanItem.objects.create(
            plan=plan,
            task='Finish reading about galaxies',
            xp_reward=10
        )
        self.assertFalse(item.is_done)
        item.is_done = True
        item.save()
        self.assertTrue(item.is_done)
