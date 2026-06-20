from django.contrib.auth.models import AnonymousUser
from .models import AuditLog


class AuditActions:
    CREATE_COURSE = "CREATE_COURSE"
    UPDATE_COURSE = "UPDATE_COURSE"
    DELETE_COURSE = "DELETE_COURSE"
    VIEW_COURSE_ANALYTICS = "VIEW_COURSE_ANALYTICS"

    CREATE_CATEGORY = "CREATE_CATEGORY"
    UPDATE_CATEGORY = "UPDATE_CATEGORY"
    DELETE_CATEGORY = "DELETE_CATEGORY"

    CREATE_TAG = "CREATE_TAG"
    UPDATE_TAG = "UPDATE_TAG"
    DELETE_TAG = "DELETE_TAG"

    CREATE_QUIZ = "CREATE_QUIZ"
    UPDATE_QUIZ = "UPDATE_QUIZ"
    DELETE_QUIZ = "DELETE_QUIZ"

    PUBLISH_ANNOUNCEMENT = "PUBLISH_ANNOUNCEMENT"

    ISSUE_CERTIFICATE = "CERTIFICATE_EARNED"

    RATE_LIMIT_TRIGGERED = "RATE_LIMIT_TRIGGERED"
    UNAUTHORIZED_ACCESS_ATTEMPT = "UNAUTHORIZED_ACCESS_ATTEMPT"
    FILE_VALIDATION_FAILED = "FILE_VALIDATION_FAILED"

    LESSON_COMPLETED = "LESSON_COMPLETED"
    QUIZ_UNLOCKED = "QUIZ_UNLOCKED"
    QUIZ_PASSED = "QUIZ_PASSED"
    CERTIFICATE_EARNED = "CERTIFICATE_EARNED"
    REPORT_VIEWED = "REPORT_VIEWED"



def log_audit(user, action, object_type=None, object_id=None, details=None, ip_address=None):
    """
    Log an administrative or educational action into the AuditLog table.
    """
    if user and (user.is_anonymous or isinstance(user, AnonymousUser)):
        user = None

    return AuditLog.objects.create(
        user=user,
        action=action,
        object_type=object_type,
        object_id=str(object_id) if object_id is not None else None,
        details=details,
        ip_address=ip_address
    )


def get_client_ip(request):
    """
    Get IP Address of client from Django request object.
    """
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
