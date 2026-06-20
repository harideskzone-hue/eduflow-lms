from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "is_student",
            "is_instructor",
        )


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"
