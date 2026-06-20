from django.urls import path
from .views import monitoring_dashboard, audit_dashboard

urlpatterns = [
    path(
        "",
        monitoring_dashboard,
        name="monitoring_dashboard"
    ),
    path(
        "audit/",
        audit_dashboard,
        name="audit_dashboard"
    ),
]
