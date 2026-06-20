from django.urls import path
from .views import course_list, course_detail, post_course_review, search_courses

urlpatterns = [
    path("", course_list, name="course_list"),
    path("search/", search_courses, name="search_courses"),
    path("<int:pk>/", course_detail, name="course_detail"),
    path("<int:pk>/review/", post_course_review, name="post_course_review"),
]
