from django.db import models
from accounts.models import LearnerProfile

class RewardItem(models.Model):
    TYPE_CHOICES = (
        ('avatar', 'Avatar Profile Picture'),
        ('theme', 'Dashboard Color Theme'),
        ('badge', 'Special Badge Frame'),
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    cost_coins = models.PositiveIntegerField(default=50)
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='avatar')
    asset_name = models.CharField(max_length=50)  # e.g., "theme-neon", "avatar-robot"

    def __str__(self):
        return f"{self.name} ({self.get_item_type_display()}) - {self.cost_coins} coins"

class UserRewardUnlock(models.Model):
    profile = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE, related_name='unlocked_rewards')
    reward = models.ForeignKey(RewardItem, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('profile', 'reward')

    def __str__(self):
        return f"{self.profile.user.username} unlocked {self.reward.name}"

class UserAchievement(models.Model):
    profile = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE, related_name='achievements')
    badge_name = models.CharField(max_length=100)
    description = models.TextField()
    icon_class = models.CharField(max_length=50, default='fa-trophy')  # FontAwesome class
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('profile', 'badge_name')

    def __str__(self):
        return f"{self.profile.user.username} earned {self.badge_name}"

class Notification(models.Model):
    TYPE_CHOICES = (
        ('streak', 'Streak Fire Update 🔥'),
        ('reward', 'Reward Unlocked 🎉'),
        ('achievement', 'Achievement Earned 🏆'),
        ('system', 'System Message 📣'),
    )
    profile = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.profile.user.username}: {self.title}"
