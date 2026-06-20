from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User model for LMS
    """

    email = models.EmailField(unique=True)

    is_student = models.BooleanField(default=True)

    is_instructor = models.BooleanField(default=False)

    def __str__(self):
        return self.username
