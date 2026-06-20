from django.urls import path
from .views import (
    course_discussion,
    thread_detail,
    manage_discussions,
    delete_thread,
    delete_reply
)

urlpatterns = [
    path(
        "courses/<int:course_id>/discussion/",
        course_discussion,
        name="course_discussion"
    ),
    path(
        "threads/<int:thread_id>/",
        thread_detail,
        name="thread_detail"
    ),
    path(
        "instructor/discussions/",
        manage_discussions,
        name="manage_discussions"
    ),
    path(
        "instructor/discussions/thread/<int:thread_id>/delete/",
        delete_thread,
        name="delete_thread"
    ),
    path(
        "instructor/discussions/reply/<int:reply_id>/delete/",
        delete_reply,
        name="delete_reply"
    ),
]
