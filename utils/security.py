from enrollments.models import Enrollment

def user_is_enrolled(user, course):
    """
    Check if a given user is enrolled in a specific course.
    Returns False if user is not authenticated or not enrolled.
    """
    if not user or not user.is_authenticated:
        return False
    return Enrollment.objects.filter(student=user, course=course).exists()
