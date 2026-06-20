from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from courses.models import Course
from enrollments.models import Enrollment
from materials.models import Material
from quizzes.models import Quiz, QuizAttempt
from progress.models import LessonProgress, CourseCompletion
from monitoring.models import AuditLog

User = get_user_model()


class QuizFlowTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student1",
            email="student1@example.com",
            password="Password123!"
        )
        self.course = Course.objects.create(
            title="Django Advanced",
            description="Advanced Django LMS."
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course
        )
        self.material = Material.objects.create(
            course=self.course,
            title="Lesson 1",
            content="Content 1",
            order=1
        )
        self.quiz = Quiz.objects.create(
            course=self.course,
            title="Final Exam",
            passing_score=80
        )

        self.quiz_detail_url = reverse("quiz_detail", kwargs={"pk": self.quiz.id})
        self.quiz_result_url = reverse("quiz_result", kwargs={"pk": self.quiz.id})

    def test_quiz_locked_when_progress_less_than_100(self):
        self.client.force_login(self.student)
        
        # 0% progress -> Locked
        response = self.client.get(self.quiz_detail_url)
        self.assertRedirects(response, reverse("course_detail", kwargs={"pk": self.course.pk}))
        
        # Verify UNAUTHORIZED_ACCESS_ATTEMPT logged
        self.assertTrue(AuditLog.objects.filter(action="UNAUTHORIZED_ACCESS_ATTEMPT").exists())

    def test_quiz_unlocked_at_100_percent(self):
        self.client.force_login(self.student)
        
        # Complete all lessons
        LessonProgress.objects.create(student=self.student, material=self.material, completed=True)
        CourseCompletion.objects.create(student=self.student, course=self.course)

        # 100% progress -> Unlocked
        response = self.client.get(self.quiz_detail_url)
        self.assertEqual(response.status_code, 200)

    def test_quiz_result_locked_when_progress_less_than_100(self):
        self.client.force_login(self.student)
        
        # Lock result page as well
        response = self.client.get(self.quiz_result_url)
        self.assertRedirects(response, reverse("course_detail", kwargs={"pk": self.course.pk}))

    def test_quiz_retake_text_rendered_on_course_detail(self):
        self.client.force_login(self.student)
        
        # 1. First load (no attempts) -> shows "Take Quiz" or similar
        res1 = self.client.get(reverse("course_detail", kwargs={"pk": self.course.pk}))
        self.assertContains(res1, "Take Quiz")
        self.assertNotContains(res1, "Attempt Again")

        # 2. Create an attempt
        QuizAttempt.objects.create(student=self.student, quiz=self.quiz, score=90, passed=True)
        
        # 3. Reload course detail -> shows "Attempt Again"
        res2 = self.client.get(reverse("course_detail", kwargs={"pk": self.course.pk}))
        self.assertContains(res2, "Attempt Again")
        self.assertNotContains(res2, "Take Quiz")
