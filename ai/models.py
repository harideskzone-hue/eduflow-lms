from django.db import models
from django.conf import settings

class AIInteraction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_interactions')
    material = models.ForeignKey('materials.Material', on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50) # "Summarize", "Explain", "Quiz", "Custom"
    prompt = models.TextField(help_text="The full prompt constructed by the PromptBuilder")
    response = models.TextField()
    provider = models.CharField(max_length=50, default='mock')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} ({self.created_at.date()})"
