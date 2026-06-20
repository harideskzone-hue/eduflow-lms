from django.contrib import admin

from .models import Material


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "course",
        "order",
        "created_at",
    )

    list_filter = (
        "course",
    )

    search_fields = (
        "title",
        "course__title",
    )

    ordering = (
        "course",
        "order",
    )
