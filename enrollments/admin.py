from django.contrib import admin
from .models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "course",
        "is_active",
        "enrolled_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "student__username",
        "course__title",
    )
