from django.contrib.admin.views.decorators import (
    staff_member_required
)
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)
from django.contrib.auth import get_user_model

from .forms import AnnouncementForm
from .models import Announcement
from notifications.utils import send_notification
from enrollments.models import Enrollment
from utils.logging_utils import log_event, log_error
from monitoring.utils import log_audit, AuditActions, get_client_ip


@staff_member_required
def manage_announcements(request):
    announcements = (
        Announcement.objects
        .order_by("-created_at")
    )

    return render(
        request,
        "announcements/manage.html",
        {
            "announcements": announcements
        }
    )


@staff_member_required
def create_announcement(request):
    if request.method == "POST":
        form = AnnouncementForm(
            request.POST
        )

        if form.is_valid():
            announcement = form.save(
                commit=False
            )

            announcement.created_by = (
                request.user
            )

            announcement.save()

            return redirect(
                "manage_announcements"
            )

    else:
        form = AnnouncementForm()

    return render(
        request,
        "announcements/create.html",
        {
            "form": form
        }
    )


@staff_member_required
def publish_announcement(request, pk):

    announcement = get_object_or_404(
        Announcement,
        pk=pk
    )

    if request.method == "POST":

        if not announcement.is_published:
            try:
                User = get_user_model()

                if announcement.course:
                    students = User.objects.filter(
                        id__in=Enrollment.objects.filter(
                            course=announcement.course
                        ).values_list(
                            "student_id",
                            flat=True
                        ),
                        is_staff=False
                    ).distinct()
                else:
                    students = User.objects.filter(
                        is_staff=False
                    )

                for student in students:
                    send_notification(
                        student,
                        f"📢 {announcement.title}",
                        announcement.message,
                        "announcements"
                    )

                announcement.is_published = True
                announcement.save()
                log_audit(
                    user=request.user,
                    action=AuditActions.PUBLISH_ANNOUNCEMENT,
                    object_type="Announcement",
                    object_id=announcement.id,
                    details=f"Published announcement: {announcement.title}",
                    ip_address=get_client_ip(request)
                )

                if announcement.course:
                    log_event(
                        f'EVENT=ANNOUNCEMENT_PUBLISHED '
                        f'title="{announcement.title}" '
                        f'course="{announcement.course.title}" '
                        f'recipients={students.count()}'
                    )
                else:
                    log_event(
                        f'EVENT=ANNOUNCEMENT_PUBLISHED '
                        f'title="{announcement.title}" '
                        f'recipients={students.count()}'
                    )
            except Exception:
                log_error(
                    f'EVENT=ANNOUNCEMENT_PUBLISH_FAILED '
                    f'title="{announcement.title}"',
                    exc_info=True
                )
                raise

    return redirect(
        "manage_announcements"
    )
