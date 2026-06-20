from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from courses.models import Course
from .models import Enrollment
from notifications.utils import send_notification
from utils.logging_utils import log_event


@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(
        Course,
        id=course_id
    )

    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course
    )

    if created:
        log_event(
            f'EVENT=ENROLLMENT user={request.user.username} '
            f'course="{course.title}"'
        )
        send_notification(
            request.user,
            "Course Enrollment Successful",
            f"You have enrolled in {course.title}",
            "enrollments"
        )

    return redirect("course_detail", pk=course.id)

