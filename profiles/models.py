from django.db import models
from django.conf import settings
from utils.validators import validate_image_upload


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    profile_photo = models.ImageField(
        upload_to="profile_photos/",
        blank=True,
        null=True,
        validators=[validate_image_upload]
    )
    bio = models.TextField(
        blank=True,
        null=True
    )

    # -- P2 Learner Identity Fields --
    level = models.PositiveIntegerField(default=1)
    xp = models.PositiveIntegerField(default=0)
    streak_days = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    learning_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Total time spent learning in minutes."
    )
    
    career_goal = models.CharField(
        max_length=200,
        blank=True, null=True,
        help_text="User's primary career goal (e.g. 'Full Stack Developer')"
    )
    
    goal_progress = models.PositiveIntegerField(
        default=0,
        help_text="Cached progress percentage towards the goal (0-100)"
    )

    target_deadline = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Goal deadline (e.g., '6 Months')"
    )
    
    experience_level = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Experience level (e.g., 'Beginner')"
    )
    
    time_commitment = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Time commitment (e.g., '2 Hours / Day')"
    )

    last_activity_date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=100, default="Learner")

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def get_learning_hours(self):
        return round(self.learning_minutes / 60, 1)

    @property
    def helpful_count(self):
        from discussions.models import Reaction
        return (Reaction.objects.filter(reply__author=self.user, reaction_type='HELPFUL').count() +
                Reaction.objects.filter(thread__author=self.user, reaction_type='HELPFUL').count())

    @property
    def insightful_count(self):
        from discussions.models import Reaction
        return (Reaction.objects.filter(reply__author=self.user, reaction_type='INSIGHTFUL').count() +
                Reaction.objects.filter(thread__author=self.user, reaction_type='INSIGHTFUL').count())

    @property
    def creative_count(self):
        from discussions.models import Reaction
        return (Reaction.objects.filter(reply__author=self.user, reaction_type='CREATIVE').count() +
                Reaction.objects.filter(thread__author=self.user, reaction_type='CREATIVE').count())

    @property
    def reputation_score(self):
        return (self.helpful_count * 2) + (self.insightful_count * 3) + (self.creative_count * 3)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Achievement(models.Model):
    CATEGORY_CHOICES = (
        ("LEARNING", "Learning"),
        ("QUIZ", "Quiz"),
        ("STREAK", "Streak"),
        ("CERTIFICATE", "Certificate"),
        ("SOCIAL", "Social"),
        ("SPECIAL", "Special"),
    )

    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Lucide icon name")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="LEARNING")
    is_gold = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="achievements"
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE
    )
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f"{self.user.username} earned {self.achievement.name}"


class NotificationLog(models.Model):
    STATUS_CHOICES = (
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_logs"
    )

    subject = models.CharField(
        max_length=255
    )

    sent_at = models.DateTimeField(
        auto_now_add=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES
    )

    def __str__(self):
        return f"Notification to {self.recipient.username} - {self.subject} ({self.status})"
