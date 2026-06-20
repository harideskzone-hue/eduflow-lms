from django.db import models
from django.conf import settings

class Skill(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

class CareerTrack(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title

class LearningPath(models.Model):
    career_track = models.ForeignKey(CareerTrack, on_delete=models.CASCADE, related_name='paths', null=True, blank=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    difficulty = models.CharField(max_length=50, choices=[('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')])
    estimated_hours = models.PositiveIntegerField(default=0)
    career_outcome = models.CharField(max_length=200)
    cover_image = models.ImageField(upload_to='paths/', blank=True, null=True)

    def __str__(self):
        return self.title

class LearningPathCourse(models.Model):
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='path_courses')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='path_memberships')
    order = models.PositiveIntegerField(default=0)
    required = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        unique_together = ('learning_path', 'course')

    def __str__(self):
        return f"{self.learning_path.title} - {self.course.title}"

class UserPathProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='path_progresses')
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='user_progresses')
    completion_percent = models.PositiveIntegerField(default=0)
    completed_courses = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'learning_path')

    def __str__(self):
        return f"{self.user.username} - {self.learning_path.title} ({self.completion_percent}%)"
