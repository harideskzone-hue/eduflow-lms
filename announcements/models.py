from django.db import models
from django.conf import settings


class Announcement(models.Model):
    title = models.CharField(
        max_length=200
    )

    message = models.TextField()

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    course = models.ForeignKey(
        "courses.Course",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="announcements"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    is_published = models.BooleanField(
        default=False,
        db_index=True
    )

    def __str__(self):
        return self.title
