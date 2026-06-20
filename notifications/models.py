from django.db import models
from django.conf import settings


class Notification(models.Model):

    NOTIFICATION_TYPES = (
        ('ACHIEVEMENT', 'Achievement'),
        ('CERTIFICATE', 'Certificate'),
        ('MILESTONE', 'Milestone'),
        ('DISCUSSION_REPLY', 'Discussion Reply'),
        ('PROJECT_RECOGNITION', 'Project Recognition'),
        ('SYSTEM', 'System'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='SYSTEM')

    title = models.CharField(max_length=255)

    message = models.TextField()

    link = models.URLField(blank=True, null=True, help_text="Optional link to redirect the user to")

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences"
    )

    email_enrollments = models.BooleanField(
        default=True
    )

    email_quizzes = models.BooleanField(
        default=True
    )

    email_certificates = models.BooleanField(
        default=True
    )

    email_discussions = models.BooleanField(
        default=True
    )

    email_announcements = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.user.username}'s Preferences"
