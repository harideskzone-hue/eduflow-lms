from django.db import models
from django.contrib.auth import get_user_model

from materials.models import Material

User = get_user_model()


class LessonProgress(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE
    )

    completed = models.BooleanField(
        default=False
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        unique_together = (
            "student",
            "material"
        )

    def __str__(self):
        return (
            f"{self.student.username} - "
            f"{self.material.title}"
        )


class CourseCompletion(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="course_completions"
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="completions"
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "course")

    def __str__(self):
        return f"{self.student.username} completed {self.course.title}"

