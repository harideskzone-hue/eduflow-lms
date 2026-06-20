from django import forms
from .models import CourseReview


class ReviewForm(forms.ModelForm):

    class Meta:
        model = CourseReview

        fields = [
            "rating",
            "comment"
        ]
