from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User
from .forms import (
    CustomUserCreationForm,
    CustomUserChangeForm,
)


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = (
        "username",
        "email",
        "is_student",
        "is_instructor",
        "is_staff",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "LMS Roles",
            {
                "fields": (
                    "is_student",
                    "is_instructor",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "is_student",
                    "is_instructor",
                ),
            },
        ),
    )


admin.site.register(User, CustomUserAdmin)
