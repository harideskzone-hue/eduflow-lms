from django.contrib import admin
from .models import LessonProgress


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "material",
        "completed",
        "completed_at",
    )

    list_filter = (
        "completed",
    )

    search_fields = (
        "student__username",
        "material__title",
    )
