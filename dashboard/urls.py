from django.urls import path
from .views import dashboard_view, my_courses_view

urlpatterns = [
    path(
        "",
        dashboard_view,
        name="dashboard"
    ),
    path(
        "my-courses/",
        my_courses_view,
        name="my_courses"
    ),
]
