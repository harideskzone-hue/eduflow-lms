"""
reports/views.py

Dashboard view only. All export views live in reports/exporters/.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.core.cache import cache
from django.contrib.auth import get_user_model

from courses.models import Course
from enrollments.models import Enrollment
from quizzes.models import QuizAttempt
from certificates.models import Certificate
from monitoring.models import AuditLog

User = get_user_model()


@staff_member_required
def reports_dashboard(request):
    """Reports dashboard — cached operational metrics overview."""
    cache_key = "reports:dashboard_metrics:v1"
    metrics = cache.get(cache_key)
    if not metrics:
        metrics = {
            "total_students": User.objects.filter(is_staff=False).count(),
            "total_courses": Course.objects.count(),
            "total_enrollments": Enrollment.objects.count(),
            "total_certificates": Certificate.objects.count(),
            "total_quiz_attempts": QuizAttempt.objects.count(),
            "total_audit_records": AuditLog.objects.count(),
        }
        cache.set(cache_key, metrics, timeout=60)

    return render(request, "reports/dashboard.html", metrics)
