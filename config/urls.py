"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from courses.views import search_courses
from notifications.views import notification_preferences
from utils.health import health_check, ready_check

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("ready/", ready_check, name="ready_check"),
    path(
        "",
        include("dashboard.urls")
    ),

    path(
        "admin/reports/",
        include("reports.urls")
    ),

    path(
        "admin/monitoring/",
        include("monitoring.urls")
    ),

    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "progress/",
        include("progress.urls")
    ),

    path(
        "accounts/",
        include("accounts.urls")
    ),

    path(
        "accounts/",
        include("django.contrib.auth.urls")
    ),

    path(
        "courses/",
        include("courses.urls")
    ),

    path(
        "enrollments/",
        include("enrollments.urls")
    ),

    path(
        "materials/",
        include("materials.urls")
    ),

    path(
        "quizzes/",
        include("quizzes.urls")
    ),

    path(
        "dashboard/",
        include("dashboard.urls")
    ),

    path(
        "certificates/",
        include("certificates.urls")
    ),

    path(
        "profile/",
        include("profiles.urls")
    ),
    path(
        "search/",
        search_courses,
        name="search_courses"
    ),
    path(
        "instructor/",
        include("instructor.urls")
    ),
    path(
        "notifications/",
        include("notifications.urls")
    ),
    path(
        "settings/notifications/",
        notification_preferences,
        name="notification_preferences"
    ),
    path(
        "announcements/",
        include("announcements.urls")
    ),
    path(
        "",
        include("discussions.urls")
    ),
    path("ai/", include("ai.urls")),
    path("paths/", include("paths.urls")),
]

# Serve media files during development
import os
SHOW_DEBUG_TOOLBAR = os.getenv("SHOW_DEBUG_TOOLBAR", "False") == "True"

if settings.DEBUG and SHOW_DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
