from django.contrib import admin
from .models import Profile, NotificationLog


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at")
    search_fields = ("user__username", "user__email")


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("recipient", "subject", "sent_at", "status")
    list_filter = ("status",)
    search_fields = ("recipient__username", "subject")
