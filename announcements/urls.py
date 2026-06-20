from django.urls import path

from .views import (
    manage_announcements,
    create_announcement,
    publish_announcement,
)

urlpatterns = [
    path(
        "",
        manage_announcements,
        name="manage_announcements"
    ),

    path(
        "create/",
        create_announcement,
        name="create_announcement"
    ),

    path(
        "<int:pk>/publish/",
        publish_announcement,
        name="publish_announcement"
    ),
]
