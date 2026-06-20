from certificates.models import Certificate
from progress.models import LessonProgress
from materials.models import Material
from quizzes.models import QuizAttempt
from notifications.utils import send_notification
from utils.logging_utils import log_event, log_error
from monitoring.utils import log_audit, AuditActions
from profiles.utils import award_xp, award_achievement


def generate_certificate(student, course):
    from progress.models import CourseCompletion

    # Check if course completion record exists
    completed = CourseCompletion.objects.filter(
        student=student,
        course=course
    ).exists()

    if not completed:
        from progress.services import calculate_course_progress
        progress = calculate_course_progress(student, course)
        if progress["percentage"] == 100:
            CourseCompletion.objects.create(student=student, course=course)
            completed = True

    # Check if passed the quiz
    passed_quiz = QuizAttempt.objects.filter(
        student=student,
        quiz__course=course,
        passed=True
    ).exists()

    if completed and passed_quiz:
        try:
            certificate, created = (
                Certificate.objects.get_or_create(
                    student=student,
                    course=course
                )
            )
        except Exception:
            log_error(
                f'EVENT=CERTIFICATE_GENERATION_FAILED user={student.username} '
                f'course="{course.title}"',
                exc_info=True
            )
            raise

        if created:
            log_event(
                f'EVENT=CERTIFICATE_ISSUED user={student.username} '
                f'course="{course.title}"'
            )
            log_audit(
                user=student,
                action="CERTIFICATE_EARNED",
                object_type="Certificate",
                object_id=certificate.id,
                details=f"Issued certificate for {course.title} to {student.username}"
            )
            
            # --- P3 Recognition Layer ---
            if hasattr(student, 'profile'):
                award_xp(student.profile, 100)
                
            cert_count = Certificate.objects.filter(student=student).count()
            if cert_count == 1:
                award_achievement(student, "First Certificate")
            elif cert_count == 5:
                award_achievement(student, "5 Certificates Earned")
            elif cert_count == 10:
                award_achievement(student, "10 Certificates Earned")
            elif cert_count == 25:
                award_achievement(student, "25 Certificates Earned")
            
            # --- P5 Career Path Progression ---
            from paths.models import UserPathProgress
            from django.utils import timezone
            
            path_memberships = course.path_memberships.select_related('learning_path').all()
            for membership in path_memberships:
                path = membership.learning_path
                progress, p_created = UserPathProgress.objects.get_or_create(
                    user=student,
                    learning_path=path
                )
                
                required_courses = path.path_courses.filter(required=True).values_list('course_id', flat=True)
                total_required = required_courses.count()
                
                if total_required > 0:
                    completed_count = Certificate.objects.filter(
                        student=student, 
                        course_id__in=required_courses
                    ).count()
                    
                    progress.completed_courses = completed_count
                    progress.completion_percent = int((completed_count / total_required) * 100)
                    
                    if progress.completion_percent >= 100 and not progress.completed_at:
                        progress.completed_at = timezone.now()
                        award_achievement(student, "Path Graduate")
                    elif progress.completion_percent >= 75:
                        award_achievement(student, "75% Path Complete")
                    elif progress.completion_percent >= 50:
                        award_achievement(student, "50% Path Complete")
                    elif progress.completion_percent >= 25:
                        award_achievement(student, "25% Path Complete")
                    elif completed_count == 1:
                        award_achievement(student, "Path Starter")
                        
                    progress.save()
            # ---------------------------

            send_notification(
                student,
                "Certificate Earned 🏆",
                f"Congratulations! You earned a certificate for {course.title}.",
                "certificates"
            )
            send_notification(
                student,
                "Report Generated 📊",
                f"Your student learning report is now available for course {course.title}.",
                "certificates"
            )

        return certificate

    return None
