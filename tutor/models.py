from django.db import models
from accounts.models import LearnerProfile

class LearningJourneyNode(models.Model):
    SUBJECT_CHOICES = (
        ('math', 'Mathematics'),
        ('science', 'Science & Space'),
        ('english', 'English & Stories'),
        ('coding', 'Code Adventures'),
    )
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    title = models.CharField(max_length=150)
    description = models.TextField()
    order = models.PositiveIntegerField(default=1)
    difficulty_level = models.CharField(max_length=20, default='intermediate')
    xp_reward = models.PositiveIntegerField(default=20)
    content_data = models.JSONField(default=dict, blank=True)  # Story texts, facts, equations, images

    class Meta:
        ordering = ['subject', 'order']

    def __str__(self):
        return f"{self.get_subject_display()} - Node {self.order}: {self.title}"

class UserJourneyProgress(models.Model):
    STATUS_CHOICES = (
        ('locked', 'Locked'),
        ('unlocked', 'Unlocked'),
        ('completed', 'Completed'),
    )
    profile = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE, related_name='journey_progress')
    node = models.ForeignKey(LearningJourneyNode, on_delete=models.CASCADE, related_name='user_progress')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='locked')
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('profile', 'node')

    def __str__(self):
        return f"{self.profile.user.username} - {self.node.title}: {self.status}"

class AIConversationSession(models.Model):
    profile = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE, related_name='sessions')
    subject = models.CharField(max_length=50, blank=True, null=True)
    title = models.CharField(max_length=100, default='New Chat with Buddy')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.profile.user.username} - {self.title} ({self.created_at.strftime('%Y-%m-%d')})"

class AIConversationMessage(models.Model):
    SENDER_CHOICES = (
        ('child', 'Child'),
        ('ai', 'AI Buddy'),
    )
    session = models.ForeignKey(AIConversationSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    text = models.TextField()
    visual_explanations = models.JSONField(default=dict, blank=True)  # Visual cards, diagram structures, LaTeX Math
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.text[:30]}"

class LearningMemory(models.Model):
    CAT_CHOICES = (
        ('interest', "Child's Interest"),
        ('struggle', "Struggling Concept"),
        ('preference', "Teaching Style Preference"),
        ('fact', "Personal Fact"),
    )
    profile = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE, related_name='memories')
    key = models.CharField(max_length=100)  # e.g., "favorite_animal", "decimal_struggle"
    value = models.TextField()
    category = models.CharField(max_length=20, choices=CAT_CHOICES, default='interest')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('profile', 'key')

    def __str__(self):
        return f"{self.profile.user.username}'s memory: {self.key} = {self.value}"
