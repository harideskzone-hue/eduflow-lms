from django.db import models
from django.conf import settings

class ProjectSubmission(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('FEATURED', 'Featured'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255)
    description = models.TextField()
    github_url = models.URLField(blank=True, null=True)
    demo_url = models.URLField(blank=True, null=True)
    
    # Optionally link to a specific path or course
    # For now, it's just a general project in the portfolio
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.user.username}"
