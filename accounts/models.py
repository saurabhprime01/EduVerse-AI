from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('child', 'Child'),
        ('parent', 'Parent'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='child')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class LearnerProfile(models.Model):
    STYLE_CHOICES = (
        ('visual', 'Visual (Pictures & Diagrams)'),
        ('auditory', 'Auditory (Listening & Speaking)'),
        ('reading', 'Reading/Writing (Stories & Books)'),
        ('kinesthetic', 'Kinesthetic (Coding & Building)'),
    )
    DIFFICULTY_CHOICES = (
        ('beginner', 'Beginner (Ages 5-8)'),
        ('intermediate', 'Intermediate (Ages 9-12)'),
        ('advanced', 'Advanced (Ages 13-15)'),
    )
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='learner_profile')
    age = models.PositiveIntegerField(default=8)
    learning_style = models.CharField(max_length=20, choices=STYLE_CHOICES, default='visual')
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate')
    xp = models.PositiveIntegerField(default=0)
    coins = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    confidence_score = models.FloatField(default=50.0)  # 0 to 100
    learning_velocity = models.FloatField(default=1.0)
    avatar = models.CharField(max_length=50, default='buddy_normal')
    selected_theme = models.CharField(max_length=50, default='theme-light')

    
    def __str__(self):
        return f"{self.user.username}'s Learning Twin"

class TopicProgress(models.Model):
    profile = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE, related_name='topic_progress')
    subject = models.CharField(max_length=50)  # e.g., Math, Science, English, Coding
    topic = models.CharField(max_length=100)   # e.g., Fractions, Planets, Grammar
    mastery_score = models.FloatField(default=0.0)  # 0.0 to 100.0
    confidence = models.FloatField(default=50.0)    # 0.0 to 100.0
    last_studied = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('profile', 'subject', 'topic')

    def __str__(self):
        return f"{self.profile.user.username} - {self.subject}: {self.topic} ({self.mastery_score}%)"
