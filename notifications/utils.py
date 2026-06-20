from .models import Notification, NotificationPreference
from profiles.utils import send_lms_notification
from utils.logging_utils import log_error


def create_notification(
    user,
    title,
    message
):
    Notification.objects.create(
        user=user,
        title=title,
        message=message
    )


def send_notification(
    user,
    title,
    message,
    category
):
    # 1. Create in-app notification
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
    )

    # 2. Check preferences
    preferences, _ = (
        NotificationPreference.objects.get_or_create(
            user=user
        )
    )

    # 3. Get preference status
    email_allowed = getattr(
        preferences,
        f"email_{category}",
        True,
    )

    # 4. Send email if enabled
    if email_allowed:
        clean_title = title
        if clean_title.startswith("📢 "):
            clean_title = clean_title[2:]

        try:
            send_lms_notification(
                user,
                f"[EduFlow] {clean_title}",
                message,
            )
        except Exception:
            log_error(
                f"EVENT=EMAIL_DELIVERY_FAILED user={user.username} "
                f'title="{clean_title}"',
                exc_info=True
            )
