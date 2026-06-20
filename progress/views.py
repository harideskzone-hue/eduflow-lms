from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from materials.models import Material
from .models import LessonProgress, CourseCompletion
from .services import calculate_course_progress
from certificates.services import generate_certificate
from utils.security import user_is_enrolled
from utils.logging_utils import log_event
from notifications.utils import send_notification
from monitoring.utils import log_audit, AuditActions, get_client_ip
from profiles.utils import award_xp, record_activity, award_achievement


def _process_lesson_completion(user, material, ip_address):
    """
    Helper function to mark a material complete, calculate course progress,
    create CourseCompletion if 100%, and trigger notifications and logs.
    """
    # Create or update progress
    progress_obj, created = LessonProgress.objects.update_or_create(
        student=user,
        material=material,
        defaults={
            "completed": True,
            "completed_at": timezone.now()
        }
    )

    # Log lesson completion to audit log and event log
    log_audit(
        user=user,
        action="LESSON_COMPLETED",
        object_type="Material",
        object_id=material.id,
        details=f"Completed lesson: {material.title} in course: {material.course.title}",
        ip_address=ip_address
    )
    log_event(
        f"EVENT=LESSON_COMPLETED user={user.username} "
        f"course=\"{material.course.title}\" material=\"{material.title}\""
    )

    # --- P2 XP and Activity Logic ---
    if hasattr(user, 'profile'):
        profile = user.profile
        award_xp(profile, 10)  # +10 XP for lesson
        record_activity(profile, minutes=15)  # Estimate 15 mins per lesson
        
        # Award First Lesson Achievement
        if LessonProgress.objects.filter(student=user, completed=True).count() == 1:
            award_achievement(user, "First Lesson")
        
        # Award 7 Day Streak Achievement
        if profile.streak_days >= 7:
            award_achievement(user, "7 Day Streak")
    # --------------------------------

    # Send lesson completed notification
    send_notification(
        user,
        "Lesson Completed ✅",
        f"You completed the lesson: {material.title}.",
        "enrollments"
    )

    # Recalculate progress
    progress = calculate_course_progress(user, material.course)

    # Check for course completion
    if progress["percentage"] == 100:
        completion, completion_created = CourseCompletion.objects.get_or_create(
            student=user,
            course=material.course
        )
        if completion_created:
            # Log quiz unlocked to audit log and event log
            log_audit(
                user=user,
                action="QUIZ_UNLOCKED",
                object_type="Course",
                object_id=material.course.id,
                details=f"Unlocked quiz for course: {material.course.title}",
                ip_address=ip_address
            )
            log_event(
                f"EVENT=QUIZ_UNLOCKED user={user.username} "
                f"course=\"{material.course.title}\""
            )

            # Send quiz unlocked notification
            send_notification(
                user,
                "Quiz Unlocked 🔓",
                f"Congratulations! You completed all lessons in {material.course.title}. The quiz is now unlocked.",
                "quizzes"
            )

            # Also attempt to generate certificate (e.g. if quiz was already passed, though flow usually requires quiz after lessons)
            generate_certificate(user, material.course)

    return progress


@login_required
def complete_lesson(request, material_id):
    material = get_object_or_404(
        Material,
        id=material_id
    )

    if not request.user.is_staff and not user_is_enrolled(request.user, material.course):
        log_audit(
            user=request.user,
            action=AuditActions.UNAUTHORIZED_ACCESS_ATTEMPT,
            object_type="Material",
            object_id=material.id,
            details=f"Unenrolled user attempted to complete material: {material.title}",
            ip_address=get_client_ip(request)
        )
        return redirect("course_detail", pk=material.course.id)

    _process_lesson_completion(request.user, material, get_client_ip(request))

    return redirect(
        "material_detail", pk=material.id
    )


@login_required
@require_POST
def mark_material_complete(request, pk):
    material = get_object_or_404(
        Material,
        id=pk
    )

    if not request.user.is_staff and not user_is_enrolled(request.user, material.course):
        log_audit(
            user=request.user,
            action=AuditActions.UNAUTHORIZED_ACCESS_ATTEMPT,
            object_type="Material",
            object_id=material.id,
            details=f"Unenrolled user attempted to complete material: {material.title}",
            ip_address=get_client_ip(request)
        )
        return JsonResponse({"success": False, "error": "Not enrolled in course"}, status=403)

    progress = _process_lesson_completion(request.user, material, get_client_ip(request))

    return JsonResponse({
        "success": True,
        "percentage": progress["percentage"],
        "completed_lessons": progress["completed_lessons"],
        "total_lessons": progress["total_lessons"],
        "quiz_unlocked": progress["quiz_unlocked"]
    })
