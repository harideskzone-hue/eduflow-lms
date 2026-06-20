"""
reports/exporters/excel.py

Four Excel export views — enrollments, quiz results, certificates, audit logs.
Uses openpyxl with freeze_panes + auto-fit columns for usability.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.utils import timezone

from enrollments.models import Enrollment
from quizzes.models import QuizAttempt
from certificates.models import Certificate
from monitoring.models import AuditLog
from monitoring.utils import log_audit, get_client_ip

from .helpers import create_report_workbook, auto_fit_columns

_XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@staff_member_required
def export_enrollments_excel(request):
    """Export all enrollments as a formatted Excel spreadsheet."""
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response = HttpResponse(content_type=_XLSX_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="enrollments_{timestamp}.xlsx"'

    qs = Enrollment.objects.select_related("student", "course").order_by("-enrolled_at")
    count = qs.count()

    wb, ws = create_report_workbook(
        title="Enrollment Report",
        generated_by=request.user.username,
        record_count=count,
        sheet_name="Enrollments",
        headers=["Student Username", "Student Email", "Course Title", "Progress %", "Date Enrolled"],
    )
    for e in qs.iterator(chunk_size=1000):
        ws.append([
            e.student.username,
            e.student.email,
            e.course.title,
            e.get_progress_percentage(),
            e.enrolled_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    auto_fit_columns(ws)
    ws.freeze_panes = "A7"
    wb.save(response)

    log_audit(
        user=request.user,
        action="EXPORT_REPORT",
        object_type="EnrollmentExcel",
        details=f"Exported {count} enrollment records",
        ip_address=get_client_ip(request),
    )
    return response


@staff_member_required
def export_quiz_results_excel(request):
    """Export all quiz attempt results as a formatted Excel spreadsheet."""
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response = HttpResponse(content_type=_XLSX_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="quiz_results_{timestamp}.xlsx"'

    qs = QuizAttempt.objects.select_related("student", "quiz__course").order_by("-attempted_at")
    count = qs.count()

    wb, ws = create_report_workbook(
        title="Quiz Results Report",
        generated_by=request.user.username,
        record_count=count,
        sheet_name="Quiz Results",
        headers=["Student Username", "Course Title", "Quiz Title", "Score %", "Passed", "Date Attempted"],
    )
    for a in qs.iterator(chunk_size=1000):
        ws.append([
            a.student.username,
            a.quiz.course.title,
            a.quiz.title,
            a.score,
            a.passed,
            a.attempted_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    auto_fit_columns(ws)
    ws.freeze_panes = "A7"
    wb.save(response)

    log_audit(
        user=request.user,
        action="EXPORT_REPORT",
        object_type="QuizAttemptExcel",
        details=f"Exported {count} quiz results records",
        ip_address=get_client_ip(request),
    )
    return response


@staff_member_required
def export_certificates_excel(request):
    """Export all certificates as a formatted Excel spreadsheet."""
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response = HttpResponse(content_type=_XLSX_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="certificates_{timestamp}.xlsx"'

    qs = Certificate.objects.select_related("student", "course").order_by("-issued_at")
    count = qs.count()

    wb, ws = create_report_workbook(
        title="Certificates Report",
        generated_by=request.user.username,
        record_count=count,
        sheet_name="Certificates",
        headers=["Student Username", "Student Email", "Course Title", "Date Issued"],
    )
    for c in qs.iterator(chunk_size=1000):
        ws.append([
            c.student.username,
            c.student.email,
            c.course.title,
            c.issued_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    auto_fit_columns(ws)
    ws.freeze_panes = "A7"
    wb.save(response)

    log_audit(
        user=request.user,
        action="EXPORT_REPORT",
        object_type="CertificateExcel",
        details=f"Exported {count} certificates records",
        ip_address=get_client_ip(request),
    )
    return response


@staff_member_required
def export_audit_logs_excel(request):
    """Export all audit logs as a formatted Excel spreadsheet."""
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response = HttpResponse(content_type=_XLSX_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="audit_logs_{timestamp}.xlsx"'

    qs = AuditLog.objects.select_related("user").order_by("-created_at")
    count = qs.count()

    wb, ws = create_report_workbook(
        title="Audit Log Report",
        generated_by=request.user.username,
        record_count=count,
        sheet_name="Audit Logs",
        headers=["Timestamp", "User", "IP Address", "Action", "Target Type", "Target ID", "Details"],
    )
    for log in qs.iterator(chunk_size=1000):
        ws.append([
            log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            log.user.username if log.user else "Deleted User",
            log.ip_address or "-",
            log.action,
            log.object_type or "-",
            log.object_id or "-",
            log.details or "-",
        ])

    auto_fit_columns(ws)
    ws.freeze_panes = "A7"
    wb.save(response)

    log_audit(
        user=request.user,
        action="EXPORT_REPORT",
        object_type="AuditLogExcel",
        details=f"Exported {count} audit logs records",
        ip_address=get_client_ip(request),
    )
    return response
