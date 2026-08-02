from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import LearnerProfile, TopicProgress
from tutor.models import AIConversationSession, LearningMemory
from tutor.services import GeminiTutorService

User = get_user_model()

class TutorCognitiveTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='bobby',
            password='secretpassword123',
            role='child'
        )
        self.profile = LearnerProfile.objects.create(
            user=self.user,
            age=10
        )
        self.session = AIConversationSession.objects.create(
            profile=self.profile,
            subject='math',
            title='Fractions review'
        )
        self.tutor_service = GeminiTutorService()

    def test_tutor_response_json_parsing(self):
        """Verify trailing structural JSON payloads are parsed and cleaned successfully."""
        raw_text = (
            "Fractions are parts of a whole pie! Look at this orbit path:\n"
            "||| {\"visual\": {\"type\": \"orbits\", \"args\": \"4\"}, \"mastery_delta\": 8.0, \"memories\": [{\"key\": \"fav_toy\", \"value\": \"robot\", \"category\": \"interest\"}]} |||"
        )
        
        cleaned_text, parsed_json = self.tutor_service._parse_gemini_structural_response(raw_text)
        
        # Verify text cleaning
        self.assertNotIn("|||", cleaned_text)
        self.assertNotIn("visual", cleaned_text)
        self.assertIn("Fractions are parts of a whole pie!", cleaned_text)
        
        # Verify JSON values
        self.assertIsNotNone(parsed_json)
        self.assertEqual(parsed_json['visual']['type'], 'orbits')
        self.assertEqual(parsed_json['visual']['args'], '4')
        self.assertEqual(parsed_json['mastery_delta'], 8.0)
        self.assertEqual(len(parsed_json['memories']), 1)
        self.assertEqual(parsed_json['memories'][0]['key'], 'fav_toy')

    def test_tutor_apply_twin_updates(self):
        """Verify parsed JSON payloads are saved to profile memory and topic progress models."""
        parsed_json = {
            'visual': {'type': 'fraction', 'args': '2/3'},
            'mastery_delta': 12.0,
            'memories': [
                {'key': 'fraction_gap', 'value': 'Struggles with visual thirds', 'category': 'struggle'},
                {'key': 'fav_pet', 'value': 'dog', 'category': 'interest'}
            ]
        }
        
        self.tutor_service._apply_twin_updates(
            self.profile,
            subject='math',
            topic='Fractions',
            parsed_json=parsed_json,
            user_msg="I don't understand two thirds."
        )
        
        # Check topic mastery score incremented by 12.0
        progress = TopicProgress.objects.get(profile=self.profile, subject='math', topic='Fractions')
        self.assertEqual(progress.mastery_score, 12.0)
        
        # Check memory objects saved
        struggle_mem = LearningMemory.objects.get(profile=self.profile, key='fraction_gap')
        self.assertEqual(struggle_mem.value, 'Struggles with visual thirds')
        self.assertEqual(struggle_mem.category, 'struggle')
        
        interest_mem = LearningMemory.objects.get(profile=self.profile, key='fav_pet')
        self.assertEqual(interest_mem.value, 'dog')
        self.assertEqual(interest_mem.category, 'interest')
