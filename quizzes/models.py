from django.conf import settings
from django.db import models
from courses.models import Course


class Quiz(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="quizzes"
    )

    title = models.CharField(max_length=200)

    description = models.TextField(
        blank=True,
        null=True
    )

    passing_score = models.PositiveIntegerField(
        default=50
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = (
        ("MCQ", "Multiple Choice"),
        ("TF", "True/False"),
    )

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    text = models.TextField()

    option_a = models.CharField(
        max_length=255
    )

    option_b = models.CharField(
        max_length=255
    )

    option_c = models.CharField(
        max_length=255,
        blank=True
    )

    option_d = models.CharField(
        max_length=255,
        blank=True
    )

    correct_answer = models.CharField(
        max_length=1,
        choices=(
            ("A", "A"),
            ("B", "B"),
            ("C", "C"),
            ("D", "D"),
        )
    )

    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPES,
        default="MCQ"
    )

    points = models.PositiveIntegerField(
        default=1
    )

    def __str__(self):
        return self.text[:50]


class QuizAttempt(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )


    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE
    )

    score = models.PositiveIntegerField(
        default=0
    )

    passed = models.BooleanField(
        default=False
    )

    attempted_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["student", "passed"]),
            models.Index(fields=["quiz", "-attempted_at"]),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title}"


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers"
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )

    selected_answer = models.CharField(
        max_length=1
    )

    is_correct = models.BooleanField(
        default=False
    )

    def __str__(self):
        return (
            f"{self.attempt.student.username}"
            f" - {self.question.id}"
        )
