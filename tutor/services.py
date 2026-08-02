import google.generativeai as genai
from django.conf import settings
from accounts.models import TopicProgress
from .models import LearningMemory
import json
import re

class GeminiTutorService:
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.model_initialized = False
        
        if self.api_key and self.api_key != 'your_gemini_api_key_here':
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.model_initialized = True
            except Exception as e:
                print(f"Error configuring Gemini API: {e}")

    def generate_tutor_response(self, session, message_text):
        profile = session.profile
        memories = LearningMemory.objects.filter(profile=profile)
        subject = session.subject or 'math'

        # 1. Strategy Selector: Observe child's digital twin state
        topic = self._detect_topic(message_text, subject)
        progress = TopicProgress.objects.filter(profile=profile, subject=subject, topic=topic).first()
        mastery = progress.mastery_score if progress else 50.0

        # Choose learning strategy mode based on twin metrics
        strategy_mode = "EXPLAIN_MODE"
        strategy_instruction = "Focus on explaining the concepts with clear, simple steps."

        if mastery < 55.0:
            strategy_mode = "HINT_MODE"
            strategy_instruction = "The child is struggling with this concept (mastery is low). DO NOT give direct answers. Give a patient, small hint and ask a guiding question."
        elif profile.learning_style == 'visual':
            strategy_mode = "VISUAL_MODE"
            strategy_instruction = "The child is a visual learner. Be sure to trigger a visual layout by describing a custom SVG drawing matching this concept."
        elif profile.streak >= 3:
            strategy_mode = "ENCOURAGE_MODE"
            strategy_instruction = "The child has a great streak going! Start your response by congratulating them and keeping them motivated!"

        # 2. Build conversation history
        messages = session.messages.order_by('timestamp')
        history_context = []
        for msg in messages:
            role_label = "Child" if msg.sender == 'child' else "Buddy (Tutor)"
            history_context.append(f"{role_label}: {msg.text}")
        
        history_str = "\n".join(history_context[-6:])

        # Build memories string
        memory_str = ""
        if memories.exists():
            memory_list = [f"- {m.key}: {m.value}" for m in memories]
            memory_str = "\n".join(memory_list)

        # 3. Prompt Engineering with structural JSON output request
        system_instruction = f"""
You are "Buddy", a patient, playful AI tutor for children.
Child Profile context:
- Age: {profile.age} years old
- Learning Style: {profile.get_learning_style_display()}
- Difficulty Level: {profile.get_difficulty_level_display()}

Current AI Tutoring Strategy:
Mode: {strategy_mode}
Strategy Rule: {strategy_instruction}

Child's Personal Context / Memory Facts:
{memory_str}

Follow these tutoring rules:
1. Speak in a warm, encouraging, child-friendly tone. Use stories and analogies.
2. If they ask a question or solve a problem, DO NOT give direct answers. Help them think.
3. Use LaTeX math notation where needed, e.g., \\(\\frac{{1}}{{2}}\\).
4. At the very end of your response, you MUST append a structured JSON block wrapped between '|||' markers. This JSON payload is hidden from the child but tells the system how to update the database twin and draw visuals:
   Format:
   ||| {{"memories": [{{"key": "favorite_color", "value": "blue", "category": "interest"}}], "visual": {{"type": "fraction", "args": "3/4"}}, "mastery_delta": 5.0}} |||
   - "memories" (optional): list of key-value-category facts parsed from child's chat text (interests, struggles).
   - "visual" (optional): instructs the UI to draw a diagram. Types:
     * "fraction" (args: "a/b" fraction value)
     * "orbits" (args: number of orbiting planets, e.g. "3")
     * "blocks" (args: Scratch block structures description)
   - "mastery_delta" (optional): float (e.g. 5.0 or -5.0) indicating if the child showed understanding or struggled.

Active Topic: {topic} in {subject}
Conversation History:
{history_str}

New Message from Child: {message_text}
Buddy's Patient response:
"""

        response_text = ""
        visual_data = None

        if self.model_initialized:
            try:
                response = self.model.generate_content(system_instruction)
                response_text = response.text
            except Exception as e:
                print(f"Gemini API invocation error: {e}")
                response_text = self._offline_tutor_fallback(profile, subject, message_text)
        else:
            response_text = self._offline_tutor_fallback(profile, subject, message_text)

        # 4. Parse the structural JSON payload from Gemini response text
        response_text, parsed_json = self._parse_gemini_structural_response(response_text)

        # 5. Process updates in Digital Twin database
        self._apply_twin_updates(profile, subject, topic, parsed_json, message_text)

        if parsed_json and 'visual' in parsed_json:
            visual_data = parsed_json['visual']

        return response_text, visual_data

    def _parse_gemini_structural_response(self, text):
        """Extract and parse trailing JSON block from Gemini output."""
        pattern = r"\|\|\|\s*(\{.*?\}|\[.*?\])\s*\|\|\|"
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            json_str = match.group(1).strip()
            # Clean text by removing block
            cleaned_text = re.sub(pattern, "", text, flags=re.DOTALL).strip()
            try:
                parsed_json = json.loads(json_str)
                return cleaned_text, parsed_json
            except Exception as e:
                print(f"Error parsing Gemini trailing JSON: {e}")
                return cleaned_text, None
        return text, None

    def _apply_twin_updates(self, profile, subject, topic, parsed_json, user_msg):
        """Update TopicProgress, streaks, XP, and Memory based on parsed JSON payload."""
        mastery_delta = 5.0
        
        # 1. Update based on AI's evaluation in JSON
        if parsed_json:
            mastery_delta = parsed_json.get('mastery_delta', 5.0)
            
            # Save extracted memories
            memories_list = parsed_json.get('memories', [])
            for mem in memories_list:
                key = mem.get('key')
                val = mem.get('value')
                cat = mem.get('category', 'interest')
                if key and val:
                    LearningMemory.objects.update_or_create(
                        profile=profile,
                        key=key,
                        defaults={'value': val, 'category': cat}
                    )

        # 2. Update Topic Mastery
        progress, created = TopicProgress.objects.get_or_create(
            profile=profile,
            subject=subject,
            topic=topic,
            defaults={'mastery_score': max(0.0, min(100.0, mastery_delta)), 'confidence': max(0.0, min(100.0, 50.0 + (mastery_delta * 0.8)))}
        )
        if not created:
            progress.mastery_score = max(0.0, min(100.0, progress.mastery_score + mastery_delta))
            progress.confidence = max(0.0, min(100.0, progress.confidence + (mastery_delta * 0.8)))
            progress.save()

        # 3. Reward XP / Coins
        profile.xp += 5
        profile.coins += 2
        profile.save()

        # 4. Fallback parser if JSON failed
        if not parsed_json:
            # Check for struggle keywords
            if "stuck" in user_msg.lower() or "hard" in user_msg.lower():
                LearningMemory.objects.update_or_create(
                    profile=profile,
                    key=f"{topic.lower()}_struggle",
                    defaults={'value': "Struggling with concept", 'category': 'struggle'}
                )

    def _detect_topic(self, text, subject):
        """Heuristic topic detection based on keywords."""
        msg = text.lower()
        if subject == 'math':
            if 'fraction' in msg or 'slice' in msg:
                return 'Fractions'
            return 'Counting'
        elif subject == 'science':
            if 'planet' in msg or 'solar' in msg or 'sun' in msg:
                return 'Solar System'
            return 'Gravity'
        elif subject == 'coding':
            if 'html' in msg or 'tag' in msg:
                return 'HTML Tags'
            return 'Loops'
        return 'General Concepts'

    def _offline_tutor_fallback(self, profile, subject, message_text):
        """Simulated offline teacher output formatted with the structural JSON markers."""
        msg = message_text.lower()
        
        if 'fraction' in msg or 'half' in msg or 'quarter' in msg:
            return (
                "Think of fractions like dividing a big pizza with your friends! "
                "If we split it into 4 equal slices, 1 slice is \\(\\frac{1}{4}\\). "
                "How many slices would make up a half of the pizza? What do you think?\n"
                "||| {\"visual\": {\"type\": \"fraction\", \"args\": \"1/4\"}, \"mastery_delta\": 5.0} |||"
            )
        elif 'space' in msg or 'planet' in msg or 'orbits' in msg:
            return (
                "Space is awesome! The Sun sits in the center, and planets spin around it like horses on a carousel! "
                "Gravity keeps them in their orbits. Which planet is your absolute favorite?\n"
                "||| {\"visual\": {\"type\": \"orbits\", \"args\": \"3\"}, \"memories\": [{\"key\": \"interest_space\", \"value\": \"highly interested\", \"category\": \"interest\"}]} |||"
            )
        elif 'code' in msg or 'coding' in msg or 'loops' in msg:
            return (
                "Coding is like writing magic spells for computer robots! A loop is a spell that tells the robot "
                "to repeat an action, like dancing, 10 times in a row!\n"
                "||| {\"visual\": {\"type\": \"blocks\", \"args\": \"repeat 10\"}, \"mastery_delta\": 5.0} |||"
            )
            
        return (
            f"That is a great question! Let's explore it together. As a {profile.get_learning_style_display()} learner, "
            "what is your first guess? Tell me, and I'll give you a hint!\n"
            "||| {\"mastery_delta\": 2.0} |||"
        )
