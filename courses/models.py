from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from utils.validators import FileValidator, validate_image_upload


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    def __str__(self):
        return self.name


class Course(models.Model):

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses"
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="courses"
    )

    skills = models.ManyToManyField(
        'paths.Skill',
        blank=True,
        related_name='courses'
    )

    cover_image = models.ImageField(upload_to="course_covers/", null=True, blank=True, validators=[validate_image_upload])
    level = models.CharField(max_length=20, choices=[('BEGINNER', 'Beginner'), ('INTERMEDIATE', 'Intermediate'), ('ADVANCED', 'Advanced')], default="BEGINNER")

    title = models.CharField(max_length=200)
    description = models.TextField()

    thumbnail = models.ImageField(
        upload_to="course_thumbnails/",
        blank=True,
        null=True,
        validators=[
            FileValidator(
                allowed_extensions=['.png', '.jpg', '.jpeg', '.webp'],
                allowed_mimetypes=['image/png', 'image/jpeg', 'image/webp'],
                max_size=2 * 1024 * 1024
            )
        ]
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    is_featured = models.BooleanField(
        default=False
    )

    @property
    def average_rating(self):
        return (
            self.reviews.aggregate(
                Avg("rating")
            )["rating__avg"]
            or 0
        )

    def __str__(self):
        return self.title


class CourseReview(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    rating = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    comment = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            "course",
            "student"
        )

    def __str__(self):
        return (
            f"{self.student.username} - "
            f"{self.course.title}"
        )
