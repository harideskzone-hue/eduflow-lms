from django import forms
from .models import DiscussionThread, DiscussionReply


class DiscussionThreadForm(forms.ModelForm):
    class Meta:
        model = DiscussionThread
        fields = [
            "title",
            "content",
        ]

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise forms.ValidationError("Title cannot be empty.")
        return title

    def clean_content(self):
        content = self.cleaned_data.get("content", "").strip()
        if not content:
            raise forms.ValidationError("Content cannot be empty.")
        return content


class DiscussionReplyForm(forms.ModelForm):
    class Meta:
        model = DiscussionReply
        fields = [
            "content",
        ]
        labels = {
            "content": "Your Reply",
        }

    def clean_content(self):
        content = self.cleaned_data.get("content", "").strip()
        if not content:
            raise forms.ValidationError("Reply content cannot be empty.")
        return content
