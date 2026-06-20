from django import forms
from .models import Announcement
from courses.models import Course


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = [
            "title",
            "message",
            "course",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["course"].queryset = (
            Course.objects.order_by("title")
        )
        self.fields["course"].required = False
