"""
dashboard/views.py

Routing dispatcher + three private handler functions — one per user state.
Each function is independently testable and has a single responsibility.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Avg, OuterRef, Subquery, Count, Case, When, IntegerField, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache

from enrollments.models import Enrollment
from progress.models import LessonProgress
from quizzes.models import QuizAttempt
from courses.models import Course
from certificates.models import Certificate
from courses.views import get_popular_courses, get_recommended_courses
from notifications.models import Notification
from announcements.models import Announcement
from materials.models import Material
from paths.models import LearningPath, UserPathProgress, Skill
from profiles.utils import onboarding_required
from datetime import timedelta
import random


# ── Shared subqueries (reused across admin + student dashboards) ──────────────

def _total_materials_subquery():
    return Subquery(
        Material.objects.filter(course=OuterRef("course"))
        .values("course")
        .annotate(count=Count("id"))
        .values("count")
    )


def _completed_materials_subquery():
    return Subquery(
        LessonProgress.objects.filter(
            student=OuterRef("student"),
            material__course=OuterRef("course"),
            completed=True,
        )
        .values("student")
        .annotate(count=Count("id"))
        .values("count")
    )


def _get_notification_context(user):
    """Return unread count + 5 most recent notifications for a logged-in user."""
    return {
        "unread_notifications": Notification.objects.filter(user=user, is_read=False).count(),
        "recent_notifications": list(
            Notification.objects.filter(user=user).order_by("-created_at")[:5]
        ),
    }


# ── Route dispatcher ──────────────────────────────────────────────────────────

@onboarding_required
def dashboard_view(request):
    if not request.user.is_authenticated:
        return _guest_dashboard(request)
    if request.user.is_staff:
        return _admin_dashboard(request)
    return _student_dashboard(request)


# ── Guest (unauthenticated) ───────────────────────────────────────────────────

def _guest_dashboard(request):
    featured_courses = cache.get("featured_courses:v1")
    if not featured_courses:
        featured_courses = list(
            Course.objects.filter(is_featured=True)
            .select_related("category")
            .prefetch_related("tags")[:6]
        )
        cache.set("featured_courses:v1", featured_courses, timeout=300)

    return render(
        request,
        "dashboard/home.html",
        {
            "featured_courses": featured_courses,
            "popular_courses": get_popular_courses(),
            "unread_notifications": 0,
        },
    )


# ── Admin (is_staff) ─────────────────────────────────────────────────────────

def _admin_dashboard(request):
    User = get_user_model()

    total_students = User.objects.filter(is_staff=False).count()
    total_courses = Course.objects.count()
    total_certificates = Certificate.objects.count()
    total_quiz_attempts = QuizAttempt.objects.count()

    # ── Annotated enrollments (single queryset, no Python loops) ─────────────
    enrollments_annotated = Enrollment.objects.select_related(
        "student", "course"
    ).annotate(
        total_materials=Coalesce(_total_materials_subquery(), 0),
        completed_materials=Coalesce(_completed_materials_subquery(), 0),
    )
    total_enrollments = enrollments_annotated.count()

    # Completion rate via DB aggregation — no Python-level iteration
    completed_enrollments = enrollments_annotated.filter(
        total_materials__gt=0,
        completed_materials=F("total_materials"),
    ).count()
    overall_completion_rate = (
        int((completed_enrollments / total_enrollments) * 100)
        if total_enrollments > 0
        else 0
    )

    # Recent activity lists
    latest_enrollments = (
        Enrollment.objects.select_related("student", "course")
        .order_by("-enrolled_at")[:5]
    )
    latest_certificates = (
        Certificate.objects.select_related("student", "course")
        .order_by("-issued_at")[:5]
    )
    latest_quiz_attempts = (
        QuizAttempt.objects.select_related("student", "quiz")
        .order_by("-attempted_at")[:5]
    )

    # Top courses by completion rate
    # Use the same subqueries that power the student dashboard, but from Course perspective
    top_courses_qs = (
        Course.objects.annotate(
            total_enrolled=Count("enrollment", distinct=True),
            _total_materials=Coalesce(
                Subquery(
                    Material.objects.filter(course=OuterRef("pk"))
                    .values("course")
                    .annotate(cnt=Count("id"))
                    .values("cnt")[:1]
                ),
                0,
            ),
        )
        .filter(_total_materials__gt=0, total_enrolled__gt=0)
    )
    # Compute completion rate in Python (small dataset — 5 courses max)
    top_courses = []
    for c in top_courses_qs:
        total_mat = c._total_materials
        completed_count = 0
        for enrollment in Enrollment.objects.filter(course=c).select_related("student"):
            student_completed = LessonProgress.objects.filter(
                student=enrollment.student, material__course=c, completed=True
            ).count()
            if student_completed >= total_mat:
                completed_count += 1
        rate = int((completed_count / c.total_enrolled) * 100) if c.total_enrolled > 0 else 0
        top_courses.append({"title": c.title, "completion_rate": rate})
    top_courses.sort(key=lambda x: x["completion_rate"], reverse=True)
    top_courses = top_courses[:5]

    # Quiz analytics
    avg_score = QuizAttempt.objects.aggregate(Avg("score"))["score__avg"] or 0
    passed_attempts = QuizAttempt.objects.filter(passed=True).count()
    pass_rate = (
        int((passed_attempts / total_quiz_attempts) * 100) if total_quiz_attempts > 0 else 0
    )

    total_announcements = Announcement.objects.count()
    published_announcements = Announcement.objects.filter(is_published=True).count()

    context = {
        "is_admin": True,
        "total_students": total_students,
        "total_courses": total_courses,
        "total_enrollments": total_enrollments,
        "total_certificates": total_certificates,
        "total_quiz_attempts": total_quiz_attempts,
        "completion_rate": overall_completion_rate,
        "latest_enrollments": latest_enrollments,
        "latest_certificates": latest_certificates,
        "latest_quiz_attempts": latest_quiz_attempts,
        "top_courses": top_courses,
        "average_score": round(avg_score),
        "pass_rate": pass_rate,
        "fail_rate": 100 - pass_rate if total_quiz_attempts > 0 else 0,
        "total_announcements": total_announcements,
        "published_announcements": published_announcements,
        **_get_notification_context(request.user),
    }
    return render(request, "dashboard/dashboard.html", context)


# ── Student (authenticated, non-staff) ───────────────────────────────────────

def _student_dashboard(request):
    user = request.user

    total_courses = Enrollment.objects.filter(student=user).count()

    completed_lessons = LessonProgress.objects.filter(
        student=user, completed=True
    ).count()

    quizzes_passed = QuizAttempt.objects.filter(student=user, passed=True).count()

    average_score = (
        QuizAttempt.objects.filter(student=user).aggregate(Avg("score"))["score__avg"] or 0
    )

    my_courses = (
        Enrollment.objects.filter(student=user)
        .select_related("course")
        .annotate(
            total_materials=Coalesce(_total_materials_subquery(), 0),
            completed_materials=Coalesce(_completed_materials_subquery(), 0),
        )
    )

    # Recent activity — merge enrollments + completions, sort, slice
    recent_activities = []

    for e in Enrollment.objects.filter(student=user).select_related("course").order_by("-enrolled_at")[:5]:
        recent_activities.append({
            "type": "enrollment",
            "text": f"Enrolled in {e.course.title}",
            "date": e.enrolled_at,
        })

    for lp in (
        LessonProgress.objects.filter(student=user, completed=True, completed_at__isnull=False)
        .select_related("material")
        .order_by("-completed_at")[:5]
    ):
        recent_activities.append({
            "type": "completion",
            "text": f"Completed {lp.material.title}",
            "date": lp.completed_at,
        })

    recent_activities.sort(
        key=lambda x: x["date"] if x["date"] else timezone.now(), reverse=True
    )

    # --- P4.1 Dashboard Analytics ---
    now = timezone.now()
    last_week = now - timedelta(days=7)
    
    weekly_lessons = LessonProgress.objects.filter(student=user, completed=True, completed_at__gte=last_week).count()
    weekly_quizzes = QuizAttempt.objects.filter(student=user, attempted_at__gte=last_week).count()
    
    weekly_time_hours = round((weekly_lessons * 20 + weekly_quizzes * 15) / 60, 1) # Estimated
    weekly_xp = (weekly_lessons * 10) + (QuizAttempt.objects.filter(student=user, passed=True, attempted_at__gte=last_week).count() * 25)
    
    # --- P4.2 Learning Insights ---
    consistency_score = 0
    if hasattr(user, 'profile') and user.profile.longest_streak > 0:
        consistency_score = int((user.profile.streak_days / max(user.profile.longest_streak, 1)) * 100)
        consistency_score = min(consistency_score, 100)
        
    # Strongest / Weakest areas based on Quiz scores
    quiz_stats = QuizAttempt.objects.filter(student=user).values('quiz__course__title').annotate(avg_score=Avg('score')).order_by('-avg_score')
    strongest_area = quiz_stats.first()['quiz__course__title'] if quiz_stats else "N/A"
    needs_improvement = quiz_stats.last()['quiz__course__title'] if quiz_stats and len(quiz_stats) > 1 else "N/A"
    
    # Next Lesson Recommendation
    next_lesson = None
    active_enrollment = Enrollment.objects.filter(student=user).order_by('-enrolled_at').first()
    if active_enrollment:
        completed_mats = LessonProgress.objects.filter(student=user, material__course=active_enrollment.course, completed=True).values_list('material_id', flat=True)
        next_lesson = Material.objects.filter(course=active_enrollment.course).exclude(id__in=completed_mats).order_by('order').first()

    # --- P4.3 Recommendations (Rule-Based & Trending) ---
    enrolled_course_ids = Enrollment.objects.filter(student=user).values_list('course_id', flat=True)
    completed_course_ids = Certificate.objects.filter(student=user).values_list('course_id', flat=True)
    
    trending_courses = Course.objects.annotate(recent_enrolls=Count('enrollment', filter=models.Q(enrollment__enrolled_at__gte=last_week))).order_by('-recent_enrolls').exclude(id__in=enrolled_course_ids).select_related('category').prefetch_related('tags')[:4]
    
    rule_recommendations = []
    if completed_course_ids:
        # User finished a course, recommend courses in same category they haven't enrolled in
        last_cert = Certificate.objects.filter(student=user).order_by('-issued_at').first()
        if last_cert:
            rule_recommendations = list(Course.objects.filter(category=last_cert.course.category).exclude(id__in=enrolled_course_ids).select_related('category').prefetch_related('tags')[:4])
            
    if not rule_recommendations:
        rule_recommendations = list(Course.objects.filter(is_featured=True).exclude(id__in=enrolled_course_ids)[:4])

    # --- P5 Career Dashboard Logic ---
    path_progress = None
    skills_acquired = []
    skills_remaining = []
    ai_coach_message = ""
    
    if hasattr(user, 'profile') and user.profile.career_goal:
        path = LearningPath.objects.filter(title__icontains=user.profile.career_goal).first()
        if path:
            path_progress, _ = UserPathProgress.objects.get_or_create(user=user, learning_path=path)
            
            # Simple skills evaluation
            completed_courses = Enrollment.objects.filter(student=user, course__path_memberships__learning_path=path).values_list('course_id', flat=True)
            skills_acquired = Skill.objects.filter(courses__in=completed_courses).distinct()
            skills_remaining = Skill.objects.filter(courses__path_memberships__learning_path=path).exclude(id__in=skills_acquired.values_list('id', flat=True)).distinct()
            
            # If empty fallback
            if not skills_acquired and not skills_remaining:
                skills_remaining = ["Django", "React", "REST APIs", "AWS"]
            
        ai_coach_message = f"You completed {weekly_lessons} lessons this week. Your consistency score is {consistency_score}%. At this pace, you can finish the {user.profile.career_goal} path within your target of {user.profile.target_deadline or 'the planned timeframe'}."
        if next_lesson:
            ai_coach_message += f" Recommended next action: Complete {next_lesson.title}."

    context = {
        "is_admin": False,
        "total_courses": total_courses,
        "completed_lessons": completed_lessons,
        "quizzes_passed": quizzes_passed,
        "average_score": round(average_score),
        "my_courses": my_courses,
        "recent_activities": recent_activities[:5],
        
        # P4 Analytics & Insights
        "weekly_time_hours": weekly_time_hours,
        "weekly_lessons": weekly_lessons,
        "weekly_xp": weekly_xp,
        "consistency_score": consistency_score,
        "strongest_area": strongest_area,
        "needs_improvement": needs_improvement,
        "next_lesson": next_lesson,
        
        # P4 Recommendations
        "trending_courses": trending_courses,
        "rule_recommendations": rule_recommendations,
        
        # P5 Career Path
        "path_progress": path_progress,
        "skills_acquired": skills_acquired,
        "skills_remaining": skills_remaining,
        "ai_coach_message": ai_coach_message,
        
        **_get_notification_context(user),
    }
    return render(request, "dashboard/dashboard.html", context)


# ── My Courses (full enrolled courses list) ───────────────────────────────────

@login_required
def my_courses_view(request):
    """Full page showing all enrolled courses with progress."""
    my_courses = (
        Enrollment.objects.filter(student=request.user)
        .select_related("course", "course__category")
        .annotate(
            total_materials=Coalesce(_total_materials_subquery(), 0),
            completed_materials=Coalesce(_completed_materials_subquery(), 0),
        )
    )
    return render(request, "dashboard/my_courses.html", {"my_courses": my_courses})

