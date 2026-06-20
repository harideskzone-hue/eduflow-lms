from django.contrib import admin

from .models import (
    Quiz,
    Question,
    QuizAttempt,
    StudentAnswer,
)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "course",
        "passing_score",
        "created_at",
    )

    list_filter = (
        "course",
    )

    search_fields = (
        "title",
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "quiz",
        "correct_answer",
        "points",
    )

    list_filter = (
        "quiz",
    )

    search_fields = (
        "text",
    )


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "quiz",
        "score",
        "passed",
        "attempted_at",
    )

    list_filter = (
        "passed",
        "quiz",
    )


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "attempt",
        "question",
        "selected_answer",
        "is_correct",
    )

    list_filter = (
        "is_correct",
    )
