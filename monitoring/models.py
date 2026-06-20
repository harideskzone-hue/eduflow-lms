from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs"
    )

    action = models.CharField(
        max_length=50,
        db_index=True
    )

    object_type = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    object_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    details = models.TextField(
        blank=True,
        null=True
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"{user_str} | {self.action} | {self.object_type} ({self.object_id}) | {self.created_at}"
