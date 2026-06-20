from django.db import models
from django.conf import settings
from materials.models import Material

class DiscussionThread(models.Model):
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name="threads"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=255)

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["-updated_at"]

    @property
    def reply_count(self):
        if hasattr(self, "_replies_count"):
            return self._replies_count
        cache = getattr(self, "_prefetched_objects_cache", {})
        if cache and "replies" in cache:
            return len(self.replies.all())
        return self.replies.count()

    def __str__(self):
        return self.title


class DiscussionReply(models.Model):
    thread = models.ForeignKey(
        DiscussionThread,
        on_delete=models.CASCADE,
        related_name="replies"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply by {self.author.username} on {self.thread.title}"


class Reaction(models.Model):
    REACTION_TYPES = (
        ('HELPFUL', 'Helpful'),
        ('INSIGHTFUL', 'Insightful'),
        ('CREATIVE', 'Creative'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reactions"
    )
    reply = models.ForeignKey(
        DiscussionReply,
        on_delete=models.CASCADE,
        related_name="reactions",
        null=True, blank=True
    )
    thread = models.ForeignKey(
        DiscussionThread,
        on_delete=models.CASCADE,
        related_name="reactions",
        null=True, blank=True
    )
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            ('user', 'reply', 'reaction_type'),
            ('user', 'thread', 'reaction_type'),
        )

    def __str__(self):
        return f"{self.user.username} reacted {self.reaction_type}"
