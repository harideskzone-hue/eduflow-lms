from django import forms
from courses.models import (
    Course,
    Category,
    Tag,
)
from materials.models import Material
from quizzes.models import Quiz, Question


class CourseCreateForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "title",
            "description",
            "thumbnail",
            "category",
            "tags",
            "skills",
            "is_featured",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = (
            Category.objects.order_by("name")
        )

        self.fields["tags"].queryset = (
            Tag.objects.order_by("name")
        )
        self.fields["tags"].widget = (
            forms.CheckboxSelectMultiple()
        )

        from paths.models import Skill
        self.fields["skills"].queryset = Skill.objects.order_by("name")
        self.fields["skills"].widget = forms.CheckboxSelectMultiple()


class MaterialCreateForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = [
            "title",
            "content",
            "file",
            "course",
        ]


class QuizCreateForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            "title",
            "course",
            "passing_score",
        ]


class QuestionCreateForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            "text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_answer",
            "points",
        ]
        labels = {
            "text": "Question Text",
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            "name",
        ]


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = [
            "name",
        ]
