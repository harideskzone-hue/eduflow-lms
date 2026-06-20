from django.urls import path
from .views import (
    register_view,
    CustomLoginView,
    CustomPasswordResetView,
    CustomPasswordResetConfirmView,
)

urlpatterns = [
    path(
        "register/",
        register_view,
        name="register"
    ),
    path(
        "login/",
        CustomLoginView.as_view(),
        name="login"
    ),
    path(
        "password_reset/",
        CustomPasswordResetView.as_view(),
        name="password_reset"
    ),
    path(
        "reset/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm"
    ),
]
