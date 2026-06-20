from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    render,
    get_object_or_404
)
from django.http import HttpResponse
from .pdf import build_certificate_pdf

from .models import Certificate


@login_required
def certificate_list(request):

    certificates = Certificate.objects.filter(
        student=request.user
    ).select_related("course")

    return render(
        request,
        "certificates/certificate_list.html",
        {
            "certificates": certificates
        }
    )


@login_required
def certificate_detail(
    request,
    certificate_id
):
    certificate = get_object_or_404(
        Certificate,
        certificate_id=certificate_id,
        student=request.user
    )

    return render(
        request,
        "certificates/certificate_detail.html",
        {
            "certificate": certificate
        }
    )


def verify_certificate(
    request,
    certificate_id
):
    certificate = get_object_or_404(
        Certificate,
        certificate_id=certificate_id
    )

    return render(
        request,
        "certificates/verify_certificate.html",
        {
            "certificate": certificate
        }
    )


@login_required
def download_certificate(
    request,
    certificate_id
):
    certificate = get_object_or_404(
        Certificate,
        certificate_id=certificate_id,
        student=request.user
    )

    pdf_data = build_certificate_pdf(
        certificate
    )

    response = HttpResponse(
        pdf_data,
        content_type="application/pdf"
    )

    response[
        "Content-Disposition"
    ] = (
        f'attachment; '
        f'filename="{certificate.certificate_id}.pdf"'
    )

    return response


@login_required
def certificate_success(request, certificate_id):
    certificate = get_object_or_404(
        Certificate,
        certificate_id=certificate_id,
        student=request.user
    )

    return render(
        request,
        "certificates/success.html",
        {
            "certificate": certificate
        }
    )


@login_required
def student_learning_report(request, course_id):
    from django.utils import timezone
    from django.shortcuts import redirect
    from courses.models import Course
    from enrollments.models import Enrollment
    from quizzes.models import QuizAttempt
    from progress.models import LessonProgress, CourseCompletion
    from monitoring.utils import log_audit, get_client_ip
    from utils.security import user_is_enrolled
    from materials.models import Material

    course = get_object_or_404(Course, id=course_id)

    # Verify enrollment or staff
    if not request.user.is_staff and not user_is_enrolled(request.user, course):
        log_audit(
            user=request.user,
            action="UNAUTHORIZED_ACCESS_ATTEMPT",
            object_type="Report",
            object_id=course.id,
            details=f"Unenrolled user attempted to access learning report for: {course.title}",
            ip_address=get_client_ip(request)
        )
        return redirect("course_detail", pk=course.id)

    # Get enrollment date
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    enrolled_at = enrollment.enrolled_at if enrollment else None

    # Get lesson completion history
    lesson_progresses = LessonProgress.objects.filter(
        student=request.user,
        material__course=course,
        completed=True
    ).select_related("material").order_by("completed_at")

    # Get quiz attempts
    quiz_attempts = QuizAttempt.objects.filter(
        student=request.user,
        quiz__course=course
    ).select_related("quiz").order_by("attempted_at")

    # Get certificate if any
    certificate = Certificate.objects.filter(student=request.user, course=course).first()
    completion = CourseCompletion.objects.filter(student=request.user, course=course).first()
    completed_at = completion.completed_at if completion else (certificate.issued_at if certificate else None)

    # Log report viewed
    log_audit(
        user=request.user,
        action="REPORT_VIEWED",
        object_type="Report",
        object_id=course.id,
        details=f"Viewed learning report for course {course.title}",
        ip_address=get_client_ip(request)
    )

    # Build timeline events chronologically
    timeline = []
    if enrolled_at:
        timeline.append({
            "title": "Course Started 🚀",
            "date": enrolled_at,
            "description": f"Enrolled in {course.title}.",
            "completed": True
        })

    for lp in lesson_progresses:
        timeline.append({
            "title": f"Lesson Completed: {lp.material.title} ✅",
            "date": lp.completed_at,
            "description": f"Completed lesson {lp.material.order}.",
            "completed": True
        })

    for qa in quiz_attempts:
        status = "Passed 🎉" if qa.passed else "Failed ✗"
        timeline.append({
            "title": f"Quiz Attempt: {qa.quiz.title} ({status})",
            "date": qa.attempted_at,
            "description": f"Scored {qa.score}% (Passing is {qa.quiz.passing_score}%).",
            "completed": qa.passed
        })

    if certificate:
        timeline.append({
            "title": "Certificate Earned 🏆",
            "date": certificate.issued_at,
            "description": f"Certificate ID: {certificate.certificate_id}",
            "completed": True
        })

    # Sort timeline by date
    timeline.sort(key=lambda x: x["date"] if x["date"] else timezone.now())

    return render(
        request,
        "reports/student_learning_report.html",
        {
            "course": course,
            "certificate": certificate,
            "timeline": timeline,
            "completed_lessons": len(lesson_progresses),
            "total_lessons": Material.objects.filter(course=course).count(),
            "enrolled_at": enrolled_at,
            "completed_at": completed_at,
            "quiz_attempts": quiz_attempts,
        }
    )


