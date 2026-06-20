from django.urls import path
from .views import (
    certificate_list,
    certificate_detail,
    verify_certificate,
    download_certificate,
    certificate_success,
    student_learning_report,
)

urlpatterns = [
    path(
        "",
        certificate_list,
        name="certificate_list"
    ),

    path(
        "<str:certificate_id>/success/",
        certificate_success,
        name="certificate_success"
    ),

    path(
        "report/<int:course_id>/",
        student_learning_report,
        name="student_learning_report"
    ),


    path(
        "<str:certificate_id>/",
        certificate_detail,
        name="certificate_detail"
    ),

    path(
        "verify/<str:certificate_id>/",
        verify_certificate,
        name="verify_certificate"
    ),

    path(
        "download/<str:certificate_id>/",
        download_certificate,
        name="download_certificate"
    ),
]
