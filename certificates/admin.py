from django.contrib import admin
from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):

    list_display = (
        "certificate_id",
        "student",
        "course",
        "issued_at",
    )

    search_fields = (
        "certificate_id",
        "student__username",
    )
