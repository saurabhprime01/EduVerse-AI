from django.db import models
from accounts.models import LearnerProfile

class QuizSession(models.Model):
    profile = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE, related_name='quizzes')
    subject = models.CharField(max_length=50)  # Math, Science, English, Coding
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(default=0.0)  # percentage 0.0 to 100.0
    difficulty_used = models.CharField(max_length=20, default='intermediate')

    def __str__(self):
        return f"{self.profile.user.username} - {self.subject} Quiz ({self.score}%)"

class QuizQuestion(models.Model):
    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    options = models.JSONField(default=list)  # List of choices: e.g., ["A", "B", "C", "D"]
    hint = models.TextField(blank=True, null=True)
    explanation = models.TextField(blank=True, null=True)
    correct_answer = models.CharField(max_length=150)
    user_answer = models.CharField(max_length=150, blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    difficulty = models.CharField(max_length=20, default='intermediate')

    def __str__(self):
        return f"Q: {self.question_text[:30]} ({'Correct' if self.is_correct else 'Incorrect'})"

class FlashcardDeck(models.Model):
    profile = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE, related_name='decks')
    title = models.CharField(max_length=100)
    subject = models.CharField(max_length=50)
    is_ai_generated = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.profile.user.username}"

class FlashcardItem(models.Model):
    deck = models.ForeignKey(FlashcardDeck, on_delete=models.CASCADE, related_name='cards')
    front = models.TextField()  # Question or Prompt
    back = models.TextField()   # Answer details
    hint = models.TextField(blank=True, null=True)
    visual_description = models.TextField(blank=True, null=True)  # Visual diagram description
    next_review = models.DateField(auto_now_add=True)
    interval = models.PositiveIntegerField(default=1)  # Interval in days
    ease_factor = models.FloatField(default=2.5)       # Spaced-repetition ease factor

    def __str__(self):
        return f"Card in {self.deck.title}: {self.front[:20]}"

class StudyPlan(models.Model):
    profile = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE, related_name='plans')
    title = models.CharField(max_length=100, default='My Daily Learning Adventure')
    target_date = models.DateField()
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.profile.user.username} - {self.title} ({self.target_date})"

class StudyPlanItem(models.Model):
    plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name='items')
    task = models.CharField(max_length=255)
    is_done = models.BooleanField(default=False)
    xp_reward = models.PositiveIntegerField(default=10)

    def __str__(self):
        return f"{self.task} ({'Done' if self.is_done else 'Todo'})"
