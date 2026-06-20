from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .models import Quiz, QuizAttempt, StudentAnswer
from certificates.services import generate_certificate
from notifications.utils import send_notification
from utils.logging_utils import log_event
from utils.security import user_is_enrolled
from monitoring.utils import log_audit, AuditActions, get_client_ip
from profiles.utils import award_xp, record_activity, award_achievement


@login_required
def quiz_detail(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    
    if not request.user.is_staff:
        if not user_is_enrolled(request.user, quiz.course):
            log_audit(
                user=request.user,
                action=AuditActions.UNAUTHORIZED_ACCESS_ATTEMPT,
                object_type="Quiz",
                object_id=quiz.id,
                details=f"Unenrolled user attempted to access quiz: {quiz.title}",
                ip_address=get_client_ip(request)
            )
            return redirect("course_detail", pk=quiz.course.id)

        from progress.services import calculate_course_progress
        progress = calculate_course_progress(request.user, quiz.course)
        if progress["percentage"] < 100:
            log_audit(
                user=request.user,
                action=AuditActions.UNAUTHORIZED_ACCESS_ATTEMPT,
                object_type="Quiz",
                object_id=quiz.id,
                details=f"User attempted to access locked quiz: {quiz.title} (progress {progress['percentage']}% < 100%)",
                ip_address=get_client_ip(request)
            )
            return redirect("course_detail", pk=quiz.course.id)

    questions = quiz.questions.all()

    if request.method == "POST":
        score = 0
        answers_data = []

        # Grade each question and prepare answers data
        for question in questions:
            selected = request.POST.get(f"question_{question.id}")
            is_correct = (selected == question.correct_answer)
            if is_correct:
                score += question.points
            answers_data.append((question, selected, is_correct))

        # Calculate final percentage score
        total_points = sum(q.points for q in questions)
        percentage = (score / total_points) * 100 if total_points > 0 else 0
        passed = (percentage >= quiz.passing_score)

        # Wrap all DB writes in a single atomic transaction —
        # prevents partial state if certificate or answer creation fails
        with transaction.atomic():
            attempt = QuizAttempt.objects.create(
                student=request.user,
                quiz=quiz,
                score=int(percentage),
                passed=passed,
            )
            for question, selected, is_correct in answers_data:
                StudentAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_answer=selected or "",
                    is_correct=is_correct,
                )

        log_event(
            f'EVENT=QUIZ_ATTEMPT user={request.user.username} '
            f'quiz="{quiz.title}" score={int(percentage)} '
            f'passed={passed}'
        )

        if passed:
            log_audit(
                user=request.user,
                action="QUIZ_PASSED",
                object_type="Quiz",
                object_id=quiz.id,
                details=f"Passed quiz {quiz.title} with score {int(percentage)}%",
                ip_address=get_client_ip(request)
            )
            
            # --- P2 XP and Activity Logic ---
            if hasattr(request.user, 'profile'):
                profile = request.user.profile
                award_xp(profile, 25)  # +25 XP for passing a quiz
                record_activity(profile, minutes=20)  # Estimate 20 mins for quiz
                
                # Award First Quiz Achievement
                passed_quizzes = QuizAttempt.objects.filter(student=request.user, passed=True).values('quiz').distinct().count()
                if passed_quizzes == 1:
                    award_achievement(request.user, "First Quiz")
                elif passed_quizzes == 5:
                    award_achievement(request.user, "Quiz Master")
            # --------------------------------

            send_notification(
                request.user,
                "Quiz Passed 🎉",
                f"You scored {int(percentage)}% on {quiz.title}.",
                "quizzes",
            )
            generate_certificate(request.user, quiz.course)
        else:
            send_notification(
                request.user,
                "Quiz Attempt Recorded",
                f"You scored {int(percentage)}%. Passing score is {quiz.passing_score}%.",
                "quizzes",
            )

        # Retrieve the generated certificate if one was created
        from certificates.models import Certificate
        certificate = Certificate.objects.filter(student=request.user, course=quiz.course).first()
        if passed and certificate:
            return redirect("certificate_success", certificate_id=certificate.certificate_id)

        return redirect("quiz_result", pk=quiz.id)


    return render(
        request,
        "quizzes/quiz_detail.html",
        {
            "quiz": quiz,
            "questions": questions,
        }
    )


@login_required
def quiz_result(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)

    if not request.user.is_staff:
        if not user_is_enrolled(request.user, quiz.course):
            log_audit(
                user=request.user,
                action=AuditActions.UNAUTHORIZED_ACCESS_ATTEMPT,
                object_type="Quiz",
                object_id=quiz.id,
                details=f"Unenrolled user attempted to access quiz result: {quiz.title}",
                ip_address=get_client_ip(request)
            )
            return redirect("course_detail", pk=quiz.course.id)

        from progress.services import calculate_course_progress
        progress = calculate_course_progress(request.user, quiz.course)
        if progress["percentage"] < 100:
            log_audit(
                user=request.user,
                action=AuditActions.UNAUTHORIZED_ACCESS_ATTEMPT,
                object_type="Quiz",
                object_id=quiz.id,
                details=f"User attempted to access quiz result for locked quiz: {quiz.title} (progress {progress['percentage']}% < 100%)",
                ip_address=get_client_ip(request)
            )
            return redirect("course_detail", pk=quiz.course.id)

    attempt = QuizAttempt.objects.filter(
        student=request.user,
        quiz=quiz
    ).latest("attempted_at")

    return render(
        request,
        "quizzes/result.html",
        {
            "quiz": quiz,
            "attempt": attempt
        }
    )

