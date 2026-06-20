from django.db import models
from courses.models import Course
from utils.validators import FileValidator


class Material(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="materials"
    )

    title = models.CharField(
        max_length=255
    )

    content = models.TextField(
        blank=True
    )

    video_url = models.URLField(
        blank=True
    )

    file = models.FileField(
        upload_to="materials/",
        blank=True,
        null=True,
        validators=[
            FileValidator(
                allowed_extensions=['.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg', '.zip', '.ppt', '.pptx'],
                allowed_mimetypes=[
                    'application/pdf',
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'text/plain',
                    'image/png',
                    'image/jpeg',
                    'application/zip',
                    'application/vnd.ms-powerpoint',
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                ],
                max_size=10 * 1024 * 1024
            )
        ]
    )

    order = models.PositiveIntegerField(
        default=1
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title
