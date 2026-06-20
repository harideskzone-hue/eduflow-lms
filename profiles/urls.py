from django.urls import path
from .views import profile_view, onboarding_view, public_portfolio

urlpatterns = [
    path("", profile_view, name="profile"),
    path("onboarding/", onboarding_view, name="onboarding"),
    path("portfolio/<str:username>/", public_portfolio, name="public_portfolio"),
]
