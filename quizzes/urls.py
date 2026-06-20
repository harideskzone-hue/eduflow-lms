from django.urls import path
from .views import quiz_detail, quiz_result

urlpatterns = [
    path(
        "<int:pk>/",
        quiz_detail,
        name="quiz_detail"
    ),
    path(
        "result/<int:pk>/",
        quiz_result,
        name="quiz_result"
    ),
]
