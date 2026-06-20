from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.core.cache import cache

from courses.models import Course
from materials.models import Material
from quizzes.models import Quiz
from monitoring.models import AuditLog
from utils.validators import FileValidator

User = get_user_model()


class SecurityTests(TestCase):
    def setUp(self):
        # Clear cache before each test to ensure rate limits start clean
        cache.clear()

        self.student = User.objects.create_user(
            username="student_sec",
            email="student_sec@example.com",
            password="Password123!",
            is_staff=False
        )
        self.other_student = User.objects.create_user(
            username="other_sec",
            email="other_sec@example.com",
            password="Password123!",
            is_staff=False
        )

        self.course = Course.objects.create(
            title="Secure Programming",
            description="Learn how to secure applications."
        )

        self.material = Material.objects.create(
            course=self.course,
            title="Intro to security headers",
            content="Testing access controls",
            order=1
        )

        self.quiz = Quiz.objects.create(
            course=self.course,
            title="Hardening Quiz",
            passing_score=80
        )

    def test_security_headers_present(self):
        # Check standard headers on dashboard page view
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

        # 1. X-Frame-Options
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")

        # 2. X-Content-Type-Options
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")

        # 3. Referrer-Policy
        self.assertEqual(response.headers.get("Referrer-Policy"), "same-origin")

        # 4. Permissions-Policy
        self.assertEqual(
            response.headers.get("Permissions-Policy"),
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # 5. Content-Security-Policy (CSP)
        self.assertIn("Content-Security-Policy", response.headers)
        csp = response.headers["Content-Security-Policy"]
        self.assertIn("default-src 'self'", csp)
        self.assertIn("https://api.dicebear.com", csp)

    def test_access_control_unenrolled_redirect(self):
        # Log in as other student (not enrolled in the course)
        self.client.force_login(self.other_student)

        # 1. Attempt to view Material details
        url_material = reverse("material_detail", kwargs={"pk": self.material.pk})
        response = self.client.get(url_material)
        
        # Unenrolled student gets redirected to course detail page
        self.assertRedirects(response, reverse("course_detail", kwargs={"pk": self.course.pk}))

        # 2. Attempt to view Quiz details
        url_quiz = reverse("quiz_detail", kwargs={"pk": self.quiz.pk})
        response = self.client.get(url_quiz)
        self.assertRedirects(response, reverse("course_detail", kwargs={"pk": self.course.pk}))

        # 3. Verify that UNAUTHORIZED_ACCESS_ATTEMPT audit log logs were generated
        logs = AuditLog.objects.filter(action="UNAUTHORIZED_ACCESS_ATTEMPT")
        self.assertTrue(logs.exists())
        self.assertEqual(logs.count(), 2)

    def test_rate_limiting_triggered(self):
        url = reverse("login")
        # CustomLoginView is limited to 5 requests/minute.
        # The first 5 requests should not raise 429
        for _ in range(5):
            response = self.client.post(url, {"username": "test", "password": "pwd"})
            self.assertNotEqual(response.status_code, 429)

        # The 6th request should hit the rate limiter and raise 429
        response = self.client.post(url, {"username": "test", "password": "pwd"})
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Too Many Requests", status_code=429)

        # Verify RATE_LIMIT_TRIGGERED audit log recorded
        logs = AuditLog.objects.filter(action="RATE_LIMIT_TRIGGERED")
        self.assertTrue(logs.exists())

    def test_file_validator_validation(self):
        # 1. Test size validator
        file_large = SimpleUploadedFile("too_large.png", b"a" * 15, content_type="image/png")
        validator_size = FileValidator(max_size=10)
        with self.assertRaises(ValidationError):
            validator_size(file_large)

        # Check FILE_VALIDATION_FAILED log
        self.assertTrue(AuditLog.objects.filter(action="FILE_VALIDATION_FAILED").exists())

        # 2. Test extension validator
        file_ext = SimpleUploadedFile("evil.exe", b"content", content_type="application/octet-stream")
        validator_ext = FileValidator(allowed_extensions=[".png", ".jpg"])
        with self.assertRaises(ValidationError):
            validator_ext(file_ext)

        # 3. Test mime validator
        file_mime = SimpleUploadedFile("fake.png", b"content", content_type="text/plain")
        validator_mime = FileValidator(allowed_mimetypes=["image/png"])
        with self.assertRaises(ValidationError):
            validator_mime(file_mime)
