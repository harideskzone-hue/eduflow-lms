from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from courses.models import Course
from enrollments.models import Enrollment
from progress.models import CourseCompletion
from quizzes.models import Quiz, QuizAttempt
from certificates.models import Certificate
from certificates.services import generate_certificate

User = get_user_model()


class CertificateTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student1",
            email="student1@example.com",
            password="Password123!"
        )
        self.other_student = User.objects.create_user(
            username="student2",
            email="student2@example.com",
            password="Password123!"
        )
        self.course = Course.objects.create(
            title="Django Foundations",
            description="Foundation Django LMS."
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course
        )
        self.quiz = Quiz.objects.create(
            course=self.course,
            title="Final Exam",
            passing_score=80
        )

    def test_certificate_not_generated_without_course_completion(self):
        # Create passing attempt but no CourseCompletion
        QuizAttempt.objects.create(student=self.student, quiz=self.quiz, score=90, passed=True)
        cert = generate_certificate(self.student, self.course)
        self.assertIsNone(cert)
        self.assertFalse(Certificate.objects.filter(student=self.student, course=self.course).exists())

    def test_certificate_not_generated_without_passed_quiz(self):
        # Course completion but no passing attempt
        CourseCompletion.objects.create(student=self.student, course=self.course)
        QuizAttempt.objects.create(student=self.student, quiz=self.quiz, score=40, passed=False)
        cert = generate_certificate(self.student, self.course)
        self.assertIsNone(cert)
        self.assertFalse(Certificate.objects.filter(student=self.student, course=self.course).exists())

    def test_certificate_generated_when_both_satisfied(self):
        # Course completion + passing attempt
        CourseCompletion.objects.create(student=self.student, course=self.course)
        QuizAttempt.objects.create(student=self.student, quiz=self.quiz, score=90, passed=True)
        
        cert = generate_certificate(self.student, self.course)
        self.assertIsNotNone(cert)
        self.assertTrue(Certificate.objects.filter(student=self.student, course=self.course).exists())

    def test_certificate_success_page_renders(self):
        CourseCompletion.objects.create(student=self.student, course=self.course)
        QuizAttempt.objects.create(student=self.student, quiz=self.quiz, score=90, passed=True)
        cert = generate_certificate(self.student, self.course)

        self.client.force_login(self.student)
        url = reverse("certificate_success", kwargs={"certificate_id": cert.certificate_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Certificate Earned")
        self.assertContains(response, "Django Foundations")

    def test_certificate_success_page_blocked_for_other_student(self):
        CourseCompletion.objects.create(student=self.student, course=self.course)
        QuizAttempt.objects.create(student=self.student, quiz=self.quiz, score=90, passed=True)
        cert = generate_certificate(self.student, self.course)

        # Log in as other student
        self.client.force_login(self.other_student)
        url = reverse("certificate_success", kwargs={"certificate_id": cert.certificate_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)  # Get_object_or_404 triggers 404
