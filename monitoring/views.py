"""
monitoring/views.py

Two views — monitoring_dashboard and audit_dashboard.
All log parsing logic lives in monitoring/parsers.py (LogParser class).
"""

import os

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.shortcuts import render
from django.utils import timezone

from .models import AuditLog
from .parsers import LogParser, get_mtime_safe
from .utils import AuditActions


@staff_member_required
def monitoring_dashboard(request):
    """Real-time log monitoring dashboard with mtime-based cache invalidation."""
    app_log_path   = os.path.join(settings.LOG_DIR, "app.log")
    error_log_path = os.path.join(settings.LOG_DIR, "error.log")

    app_mtime   = get_mtime_safe(app_log_path)
    error_mtime = get_mtime_safe(error_log_path)

    cache_key = "monitoring:dashboard_summary:v1"
    cached = cache.get(cache_key)

    # Cache check — serve log parser data from cache if files unchanged
    data = None
    if (
        cached
        and cached.get("app_log_mtime") == app_mtime
        and cached.get("error_log_mtime") == error_mtime
    ):
        data = cached["data"]
    else:
        parser = LogParser(app_log_path, error_log_path)
        data = parser.parse()
        cache.set(cache_key, {
            "app_log_mtime": app_mtime,
            "error_log_mtime": error_mtime,
            "data": data,
        }, timeout=60)

    # Fetch fresh DB counters for guided learning flow metrics
    today = timezone.now().date()
    db_stats = {
        "lessons_completed_today": AuditLog.objects.filter(action="LESSON_COMPLETED", created_at__date=today).count(),
        "quiz_unlocks": AuditLog.objects.filter(action="QUIZ_UNLOCKED").count(),
        "quiz_passes": AuditLog.objects.filter(action="QUIZ_PASSED").count(),
        "certificates_issued": AuditLog.objects.filter(action="CERTIFICATE_EARNED").count(),
        "reports_generated": AuditLog.objects.filter(action="REPORT_VIEWED").count(),
    }

    context = {
        **data,
        "db_stats": db_stats
    }
    return render(request, "monitoring/dashboard.html", context)


@staff_member_required
def audit_dashboard(request):
    """Compliance audit trail dashboard."""
    total_records = AuditLog.objects.count()
    today_records = AuditLog.objects.filter(created_at__date=timezone.now().date()).count()

    course_actions = AuditLog.objects.filter(
        action__in=[
            AuditActions.CREATE_COURSE,
            AuditActions.UPDATE_COURSE,
            AuditActions.DELETE_COURSE,
            AuditActions.VIEW_COURSE_ANALYTICS,
        ]
    ).count()

    quiz_actions = AuditLog.objects.filter(
        action__in=[
            AuditActions.CREATE_QUIZ,
            AuditActions.UPDATE_QUIZ,
            AuditActions.DELETE_QUIZ,
        ]
    ).count()

    announcement_actions = AuditLog.objects.filter(action=AuditActions.PUBLISH_ANNOUNCEMENT).count()
    certificate_actions  = AuditLog.objects.filter(action=AuditActions.ISSUE_CERTIFICATE).count()
    audit_logs = AuditLog.objects.select_related("user")[:100]

    return render(
        request,
        "monitoring/audit_dashboard.html",
        {
            "total_records":          total_records,
            "today_records":          today_records,
            "course_actions":         course_actions,
            "quiz_actions":           quiz_actions,
            "announcement_actions":   announcement_actions,
            "certificate_actions":    certificate_actions,
            "audit_logs":             audit_logs,
        },
    )
