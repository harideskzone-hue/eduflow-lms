from django.urls import path

from .views import (
    notification_list,
    mark_notification_read
)
from . import views


urlpatterns = [
    path(
        "",
        notification_list,
        name="notification_list"
    ),
    path(
        "<int:pk>/read/",
        mark_notification_read,
        name="mark_notification_read"
    ),
    path(
        "api/recent/",
        views.api_recent_notifications,
        name="api_recent_notifications"
    ),
    path(
        "api/mark-all-read/",
        views.api_mark_all_read,
        name="api_mark_all_read"
    ),
]
