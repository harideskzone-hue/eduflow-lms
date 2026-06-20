from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import Course, CourseReview
from enrollments.models import Enrollment


@receiver(post_save, sender=Course)
@receiver(post_delete, sender=Course)
def invalidate_course_caches(sender, instance, **kwargs):
    cache.delete("featured_courses:v1")
    cache.delete("popular_courses:v1")


@receiver(post_save, sender=CourseReview)
@receiver(post_delete, sender=CourseReview)
def invalidate_review_caches(sender, instance, **kwargs):
    cache.delete("popular_courses:v1")


@receiver(post_save, sender=Enrollment)
@receiver(post_delete, sender=Enrollment)
def invalidate_enrollment_caches(sender, instance, **kwargs):
    cache.delete("popular_courses:v1")
    if instance.student:
        cache.delete(f"recommendations:v1:{instance.student.id}")
