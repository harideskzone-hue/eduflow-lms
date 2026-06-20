from django.db import models
from django.conf import settings
from courses.models import Course
import uuid


class Certificate(models.Model):

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="certificates"
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    certificate_id = models.CharField(
        max_length=50,
        unique=True
    )

    issued_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        unique_together = (
            "student",
            "course"
        )

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            from datetime import date
            current_year = date.today().year
            last_cert = Certificate.objects.filter(
                certificate_id__startswith=f"EDF-{current_year}-"
            ).order_by('id').last()
            
            if last_cert:
                try:
                    last_num = int(last_cert.certificate_id.split('-')[-1])
                    new_num = last_num + 1
                except ValueError:
                    new_num = 1
            else:
                new_num = 1
                
            self.certificate_id = f"EDF-{current_year}-{new_num:06d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.username} - {self.course.title}"
