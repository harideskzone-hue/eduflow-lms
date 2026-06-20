from django import forms
from .models import ProjectSubmission

class ProjectSubmissionForm(forms.ModelForm):
    class Meta:
        model = ProjectSubmission
        fields = [
            'title',
            'description',
            'github_url',
            'demo_url',
            'status',
        ]
