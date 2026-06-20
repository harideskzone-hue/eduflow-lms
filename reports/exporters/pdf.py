"""
reports/exporters/pdf.py

Four PDF export views using ReportLab:
  - export_audit_summary_pdf
  - export_certificate_statistics_pdf
  - export_student_progress_pdf
  - export_course_analytics_pdf

Each builds on the shared build_pdf_document() initialiser and
standard_table_style from helpers.py.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from courses.models import Course
from enrollments.models import Enrollment
from quizzes.models import QuizAttempt
from certificates.models import Certificate
from monitoring.models import AuditLog
from monitoring.utils import log_audit, get_client_ip
from instructor.views import get_course_analytics_data

from .helpers import build_pdf_document, standard_table_style

User = get_user_model()


def _build_doc(buffer, story):
    """Compile a ReportLab story into the buffer using standard page margins."""
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    doc.build(story)


@staff_member_required
def export_audit_summary_pdf(request):
    """Export a PDF summary of the 100 most recent audit log entries."""
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    buffer, response, styles, story = build_pdf_document(
        filename=f"audit_summary_{timestamp}.pdf",
        title="Audit Summary Report",
        generated_by=request.user.username,
    )

    qs = AuditLog.objects.select_related("user").order_by("-created_at")[:100]
    story.append(Paragraph(f"<b>Total Audit Records:</b> {AuditLog.objects.count()}", styles["DocBody"]))
    story.append(Paragraph("<b>Recent Audit Entries (Showing up to 100):</b>", styles["DocBody"]))
    story.append(Spacer(1, 8))

    headers = [
        Paragraph(h, styles["HeaderCell"])
        for h in ["Timestamp", "User", "Action", "Object Type", "Details"]
    ]
    rows = [headers]
    for log in qs:
        rows.append([
            Paragraph(log.created_at.strftime("%Y-%m-%d %H:%M"), styles["DocBody"]),
            Paragraph(log.user.username if log.user else "Deleted User", styles["DocBody"]),
            Paragraph(log.action, styles["DocBody"]),
            Paragraph(log.object_type or "-", styles["DocBody"]),
            Paragraph(log.details or "-", styles["DocBody"]),
        ])

    t = Table(rows, colWidths=[90, 70, 110, 80, 190])
    t.setStyle(standard_table_style)
    story.append(t)

    _build_doc(buffer, story)
    response.write(buffer.getvalue())
    buffer.close()

    log_audit(
        user=request.user,
        action="EXPORT_REPORT",
        object_type="AuditPDF",
        details="Exported Audit Summary PDF",
        ip_address=get_client_ip(request),
    )
    return response


@staff_member_required
def export_certificate_statistics_pdf(request):
    """Export a PDF showing certificate counts per course."""
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    buffer, response, styles, story = build_pdf_document(
        filename=f"certificate_statistics_{timestamp}.pdf",
        title="Certificate Statistics Report",
        generated_by=request.user.username,
    )

    stats = (
        Certificate.objects.values("course__title")
        .annotate(count=Count("id"))
        .order_by("course__title")
    )
    total_certs = Certificate.objects.count()
    story.append(Paragraph(f"<b>Total Certificates Issued:</b> {total_certs}", styles["DocBody"]))
    story.append(Spacer(1, 8))

    headers = [Paragraph(h, styles["HeaderCell"]) for h in ["Course Name", "Certificates Issued"]]
    rows = [headers]
    for s in stats:
        rows.append([
            Paragraph(s["course__title"] or "Deleted Course", styles["DocBody"]),
            Paragraph(str(s["count"]), styles["DocBody"]),
        ])

    t = Table(rows, colWidths=[400, 140])
    t.setStyle(standard_table_style)
    story.append(t)

    _build_doc(buffer, story)
    response.write(buffer.getvalue())
    buffer.close()

    log_audit(
        user=request.user,
        action="EXPORT_REPORT",
        object_type="CertificatePDF",
        details="Exported Certificate Statistics PDF",
        ip_address=get_client_ip(request),
    )
    return response


@staff_member_required
def export_student_progress_pdf(request, student_id):
    """Export a full progress report PDF for a single student."""
    student = get_object_or_404(User, pk=student_id)
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    buffer, response, styles, story = build_pdf_document(
        filename=f"student_progress_{student.username}_{timestamp}.pdf",
        title=f"Student Progress Report - {student.username}",
        generated_by=request.user.username,
    )

    # Student info block
    story.append(Paragraph("Student Information", styles["DocHeading"]))
    info_data = [
        [Paragraph("<b>Username:</b>", styles["DocBody"]), Paragraph(student.username, styles["DocBody"])],
        [Paragraph("<b>Email:</b>", styles["DocBody"]), Paragraph(student.email, styles["DocBody"])],
        [
            Paragraph("<b>Joined Date:</b>", styles["DocBody"]),
            Paragraph(
                student.date_joined.strftime("%Y-%m-%d %H:%M:%S") if student.date_joined else "-",
                styles["DocBody"],
            ),
        ],
    ]
    info_table = Table(info_data, colWidths=[100, 440])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    # Enrolled courses
    story.append(Paragraph("Enrolled Courses", styles["DocHeading"]))
    enrollments = Enrollment.objects.filter(student=student).select_related("course")
    if enrollments.exists():
        rows = [[Paragraph(h, styles["HeaderCell"]) for h in ["Course Name", "Progress Percentage"]]]
        for e in enrollments:
            rows.append([
                Paragraph(e.course.title, styles["DocBody"]),
                Paragraph(f"{e.get_progress_percentage()}%", styles["DocBody"]),
            ])
        t = Table(rows, colWidths=[400, 140])
        t.setStyle(standard_table_style)
        story.append(t)
    else:
        story.append(Paragraph("No enrolled courses found.", styles["DocBody"]))
    story.append(Spacer(1, 10))

    # Quiz attempts
    story.append(Paragraph("Quiz Attempts", styles["DocHeading"]))
    attempts = QuizAttempt.objects.filter(student=student).select_related("quiz__course").order_by("-attempted_at")
    if attempts.exists():
        rows = [[
            Paragraph(h, styles["HeaderCell"])
            for h in ["Course Name", "Quiz Title", "Score %", "Passed", "Date Attempted"]
        ]]
        for a in attempts:
            rows.append([
                Paragraph(a.quiz.course.title, styles["DocBody"]),
                Paragraph(a.quiz.title, styles["DocBody"]),
                Paragraph(f"{a.score}%", styles["DocBody"]),
                Paragraph("Yes" if a.passed else "No", styles["DocBody"]),
                Paragraph(a.attempted_at.strftime("%Y-%m-%d %H:%M"), styles["DocBody"]),
            ])
        t = Table(rows, colWidths=[150, 150, 60, 60, 120])
        t.setStyle(standard_table_style)
        story.append(t)
    else:
        story.append(Paragraph("No quiz attempts recorded.", styles["DocBody"]))
    story.append(Spacer(1, 10))

    # Certificates earned
    story.append(Paragraph("Certificates Earned", styles["DocHeading"]))
    certs = Certificate.objects.filter(student=student).select_related("course").order_by("-issued_at")
    if certs.exists():
        rows = [[Paragraph(h, styles["HeaderCell"]) for h in ["Course Name", "Date Issued"]]]
        for c in certs:
            rows.append([
                Paragraph(c.course.title, styles["DocBody"]),
                Paragraph(c.issued_at.strftime("%Y-%m-%d %H:%M"), styles["DocBody"]),
            ])
        t = Table(rows, colWidths=[400, 140])
        t.setStyle(standard_table_style)
        story.append(t)
    else:
        story.append(Paragraph("No certificates earned yet.", styles["DocBody"]))

    _build_doc(buffer, story)
    response.write(buffer.getvalue())
    buffer.close()

    log_audit(
        user=request.user,
        action="EXPORT_REPORT",
        object_type="StudentProgressPDF",
        details=f"Exported student progress PDF for student: {student.username}",
        ip_address=get_client_ip(request),
    )
    return response


@staff_member_required
def export_course_analytics_pdf(request, course_id):
    """Export a full analytics PDF for a single course."""
    course = get_object_or_404(Course, pk=course_id)
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    buffer, response, styles, story = build_pdf_document(
        filename=f"course_analytics_{course.id}_{timestamp}.pdf",
        title=f"Course Analytics Report - {course.title}",
        generated_by=request.user.username,
    )

    data = get_course_analytics_data(course)

    # Course overview block
    story.append(Paragraph("Course Overview", styles["DocHeading"]))
    info_data = [
        [Paragraph("<b>Course Title:</b>", styles["DocBody"]), Paragraph(course.title, styles["DocBody"])],
        [Paragraph("<b>Category:</b>", styles["DocBody"]), Paragraph(course.category.name if course.category else "-", styles["DocBody"])],
        [Paragraph("<b>Total Enrollments:</b>", styles["DocBody"]), Paragraph(str(data["total_enrollments"]), styles["DocBody"])],
        [Paragraph("<b>Completion Rate:</b>", styles["DocBody"]), Paragraph(f"{data['completion_rate']}%", styles["DocBody"])],
        [Paragraph("<b>Average Quiz Score:</b>", styles["DocBody"]), Paragraph(f"{data['average_quiz_score']}%", styles["DocBody"])],
        [Paragraph("<b>Certificates Issued:</b>", styles["DocBody"]), Paragraph(str(data["certificate_count"]), styles["DocBody"])],
        [Paragraph("<b>Forum Activity:</b>", styles["DocBody"]), Paragraph(f"{data['discussion_threads']} Threads, {data['discussion_replies']} Replies", styles["DocBody"])],
    ]
    info_table = Table(info_data, colWidths=[130, 410])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))

    # Recent enrollments
    story.append(Paragraph("Recent Enrollments (Last 5)", styles["DocHeading"]))
    recent_enrollments = data["recent_enrollments"]
    if recent_enrollments:
        rows = [[Paragraph(h, styles["HeaderCell"]) for h in ["Student Username", "Email", "Date Enrolled", "Progress"]]]
        for e in recent_enrollments:
            rows.append([
                Paragraph(e.student.username, styles["DocBody"]),
                Paragraph(e.student.email, styles["DocBody"]),
                Paragraph(e.enrolled_at.strftime("%Y-%m-%d %H:%M"), styles["DocBody"]),
                Paragraph(f"{e.get_progress_percentage()}%", styles["DocBody"]),
            ])
        t = Table(rows, colWidths=[120, 180, 140, 100])
        t.setStyle(standard_table_style)
        story.append(t)
    else:
        story.append(Paragraph("No enrollments recorded.", styles["DocBody"]))
    story.append(Spacer(1, 12))

    # Recent quiz attempts
    story.append(Paragraph("Recent Quiz Attempts (Last 5)", styles["DocHeading"]))
    recent_attempts = data["recent_attempts"]
    if recent_attempts:
        rows = [[Paragraph(h, styles["HeaderCell"]) for h in ["Student Username", "Quiz Title", "Score", "Passed", "Date Attempted"]]]
        for a in recent_attempts:
            rows.append([
                Paragraph(a.student.username, styles["DocBody"]),
                Paragraph(a.quiz.title, styles["DocBody"]),
                Paragraph(f"{a.score}%", styles["DocBody"]),
                Paragraph("Yes" if a.passed else "No", styles["DocBody"]),
                Paragraph(a.attempted_at.strftime("%Y-%m-%d %H:%M"), styles["DocBody"]),
            ])
        t = Table(rows, colWidths=[120, 160, 70, 70, 120])
        t.setStyle(standard_table_style)
        story.append(t)
    else:
        story.append(Paragraph("No quiz attempts recorded.", styles["DocBody"]))

    _build_doc(buffer, story)
    response.write(buffer.getvalue())
    buffer.close()

    log_audit(
        user=request.user,
        action="EXPORT_REPORT",
        object_type="CourseAnalyticsPDF",
        details=f"Exported course analytics PDF for course: {course.title}",
        ip_address=get_client_ip(request),
    )
    return response
