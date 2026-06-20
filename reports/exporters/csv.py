"""
reports/exporters/csv.py

Four CSV export views — enrollments, quiz results, certificates, audit logs.
All use .iterator(chunk_size=1000) for memory-efficient streaming.
"""

import csv

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.utils import timezone

from enrollments.models import Enrollment
from quizzes.models import QuizAttempt
from certificates.models import Certificate
from monitoring.models import AuditLog
from monitoring.utils import log_audit, get_client_ip

from .helpers import write_csv_metadata


@staff_member_required
def export_enrollments_csv(request):
    """Streamed CSV export of all student enrollments."""
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="enrollments_{timestamp}.csv"'

    writer = csv.writer(response)
    qs = Enrollment.objects.select_related("student", "course").order_by("-enrolled_at")
    count = qs.count()

    write_csv_metadata(writer, request, "Enrollment Report", count)
    writer.writerow(["Student Username", "Student Email", "Course Title", "Progress %", "Date Enrolled"])

    for e in qs.iterator(chunk_size=1000):
        writer.writerow([
            e.student.username,
            e.student.email,
            e.course.title,
            e.get_progress_percentage(),
            e.enrolled_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    log_audit(
        user=request.user,
        action="EXPORT_REPORT",
        object_type="EnrollmentCSV",
        details=f"Exported enrollment report ({count} records)",
        ip_address=get_client_ip(request),
    )
    return response


@staff_member_required
def export_quiz_results_csv(request):
    """Streamed CSV export of all student quiz attempts."""
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="quiz_results_{timestamp}.csv"'

    writer = csv.writer(response)
    qs = QuizAttempt.objects.select_related("student", "quiz__course").order_by("-attempted_at")
    count = qs.count()

    write_csv_metadata(writer, request, "Quiz Results Report", count)
    writer.writerow(["Student Username", "Course Title", "Quiz Title", "Score %", "Passed", "Date Attempted"])

    for a in qs.iterator(chunk_size=1000):
        writer.writerow([
            a.student.username,
            a.quiz.course.title,
            a.quiz.title,
            a.score,
            a.passed,
            a.attempted_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    log_audit(
        user=request.user,
        action="EXPORT_REPORT",
        object_type="QuizAttemptCSV",
        details=f"Exported quiz results report ({count} records)",
        ip_address=get_client_ip(request),
    )
    return response


@staff_member_required
def export_certificates_csv(request):
    """Streamed CSV export of all issued student certificates."""
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="certificates_{timestamp}.csv"'

    writer = csv.writer(response)
    qs = Certificate.objects.select_related("student", "course").order_by("-issued_at")
    count = qs.count()

    write_csv_metadata(writer, request, "Certificates Report", count)
    writer.writerow(["Student Username", "Student Email", "Course Title", "Date Issued"])

    for c in qs.iterator(chunk_size=1000):
        writer.writerow([
            c.student.username,
            c.student.email,
            c.course.title,
            c.issued_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    log_audit(
        user=request.user,
        action="EXPORT_REPORT",
        object_type="CertificateCSV",
        details=f"Exported certificates report ({count} records)",
        ip_address=get_client_ip(request),
    )
    return response


@staff_member_required
def export_audit_logs_csv(request):
    """Streamed CSV export of the compliance audit trail."""
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="audit_logs_{timestamp}.csv"'

    writer = csv.writer(response)
    qs = AuditLog.objects.select_related("user").order_by("-created_at")
    count = qs.count()

    write_csv_metadata(writer, request, "Audit Log Report", count)
    writer.writerow(["Timestamp", "User", "IP Address", "Action", "Target Type", "Target ID", "Details"])

    for log in qs.iterator(chunk_size=1000):
        writer.writerow([
            log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            log.user.username if log.user else "Deleted User",
            log.ip_address or "-",
            log.action,
            log.object_type or "-",
            log.object_id or "-",
            log.details or "-",
        ])

    log_audit(
        user=request.user,
        action="EXPORT_REPORT",
        object_type="AuditLogCSV",
        details=f"Exported audit logs report ({count} records)",
        ip_address=get_client_ip(request),
    )
    return response
