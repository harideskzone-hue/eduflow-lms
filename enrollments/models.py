from django.conf import settings
from django.db import models
from courses.models import Course


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    enrolled_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        unique_together = ("student", "course")
        indexes = [
            models.Index(fields=["student", "course"]),
        ]

    def get_progress_percentage(self):
        if hasattr(self, "total_materials") and hasattr(self, "completed_materials"):
            total = self.total_materials
            completed = self.completed_materials
        else:
            from materials.models import Material
            from progress.models import LessonProgress
            total = Material.objects.filter(course=self.course).count()
            if total == 0:
                return 0
            completed = LessonProgress.objects.filter(
                student=self.student,
                material__course=self.course,
                completed=True
            ).count()
        return int((completed / total) * 100) if total > 0 else 0

    def __str__(self):
        return f"{self.student.username} - {self.course.title}"
