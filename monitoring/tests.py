import os
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from monitoring.models import AuditLog
from monitoring.utils import log_audit, AuditActions
from courses.models import Course, Category, Tag
from quizzes.models import Quiz, QuizAttempt
from announcements.models import Announcement
from progress.models import LessonProgress
from materials.models import Material
from certificates.services import generate_certificate

User = get_user_model()


class MonitoringDashboardTests(TestCase):
    def setUp(self):
        # Create a staff user and a student user
        self.staff_user = User.objects.create_user(
            username="admin_monitor",
            email="admin@example.com",
            password="password123",
            is_staff=True
        )
        self.student = User.objects.create_user(
            username="student_monitor",
            email="student@example.com",
            password="password123",
            is_staff=False
        )
        self.dashboard_url = reverse("monitoring_dashboard")

    def test_anonymous_redirection(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)

    def test_student_redirection(self):
        self.client.login(username="student_monitor", password="password123")
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)

    def test_staff_access_and_missing_log_resiliency(self):
        # Temporarily rename/remove log paths to test missing log file resilience
        app_log_path = os.path.join(settings.LOG_DIR, "app.log")
        error_log_path = os.path.join(settings.LOG_DIR, "error.log")
        
        backup_app = app_log_path + ".bak"
        backup_err = error_log_path + ".bak"

        if os.path.exists(app_log_path):
            os.rename(app_log_path, backup_app)
        if os.path.exists(error_log_path):
            os.rename(error_log_path, backup_err)

        try:
            self.client.login(username="admin_monitor", password="password123")
            response = self.client.get(self.dashboard_url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "monitoring/dashboard.html")
            
            # Verifying resilient context
            self.assertEqual(response.context["total_events"], 0)
            self.assertEqual(response.context["total_errors"], 0)
            self.assertEqual(response.context["health_status"], "Healthy")
        finally:
            # Restore log files
            if os.path.exists(backup_app):
                os.rename(backup_app, app_log_path)
            if os.path.exists(backup_err):
                os.rename(backup_err, error_log_path)

    def test_log_rendering_and_counting(self):
        # Temporarily backup existing logs
        app_log_path = os.path.join(settings.LOG_DIR, "app.log")
        error_log_path = os.path.join(settings.LOG_DIR, "error.log")
        
        backup_app = app_log_path + ".bak"
        backup_err = error_log_path + ".bak"

        if os.path.exists(app_log_path):
            os.rename(app_log_path, backup_app)
        if os.path.exists(error_log_path):
            os.rename(error_log_path, backup_err)

        try:
            # Write mock data to logs
            with open(app_log_path, "w", encoding="utf-8") as f:
                f.write('[2026-06-19 11:15:36,249] INFO eduflow EVENT=ENROLLMENT user=hari course="Python Full Stack"\n')
                f.write('[2026-06-19 11:15:36,249] INFO eduflow EVENT=QUIZ_ATTEMPT user=hari quiz="Module 1" score=85 passed=True\n')
            
            with open(error_log_path, "w", encoding="utf-8") as f:
                f.write('[2026-06-19 11:19:07,896] ERROR eduflow EVENT=EMAIL_DELIVERY_FAILED user=hari title="Quiz Passed"\n')
                f.write('Traceback (most recent call last):\n')
                f.write('  File "<string>", line 4, in <module>\n')
                f.write('ValueError: Test Error\n')

            self.client.login(username="admin_monitor", password="password123")
            response = self.client.get(self.dashboard_url)
            self.assertEqual(response.status_code, 200)

            # Assert context variables
            self.assertEqual(response.context["total_events"], 2)
            self.assertEqual(response.context["total_errors"], 1)
            self.assertEqual(response.context["health_status"], "Warning") # 1 error is <= 5

            # Assert parsed values
            self.assertEqual(response.context["event_counts"]["ENROLLMENT"], 1)
            self.assertEqual(response.context["event_counts"]["QUIZ_ATTEMPT"], 1)
            self.assertEqual(response.context["error_counts"]["EMAIL_DELIVERY_FAILED"], 1)

            # Assert page renders data
            self.assertContains(response, "user=hari course=&quot;Python Full Stack&quot;")
            self.assertContains(response, "Enrollment")
            self.assertContains(response, "user=hari title=&quot;Quiz Passed&quot;")
            self.assertContains(response, "EMAIL_DELIVERY_FAILED")
            self.assertContains(response, "ValueError: Test Error")
        finally:
            # Restore backups
            if os.path.exists(app_log_path):
                os.remove(app_log_path)
            if os.path.exists(error_log_path):
                os.remove(error_log_path)

            if os.path.exists(backup_app):
                os.rename(backup_app, app_log_path)
            if os.path.exists(backup_err):
                os.rename(backup_err, error_log_path)


class AuditLogTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="staff_audit",
            email="staff_audit@example.com",
            password="password123",
            is_staff=True
        )
        self.student = User.objects.create_user(
            username="student_audit",
            email="student_audit@example.com",
            password="password123",
            is_staff=False
        )
        self.category = Category.objects.create(name="Design")
        self.tag = Tag.objects.create(name="UX")
        self.course = Course.objects.create(
            title="UI/UX Principles",
            description="Learn UX design.",
            category=self.category
        )
        self.course.tags.add(self.tag)
        self.quiz = Quiz.objects.create(
            course=self.course,
            title="UX Quiz 1",
            passing_score=80
        )
        self.announcement = Announcement.objects.create(
            title="UX Webinar",
            message="Join us tomorrow.",
            created_by=self.staff_user
        )
        self.audit_dashboard_url = reverse("audit_dashboard")

    def test_log_audit_utility(self):
        # Authenticated user
        log = log_audit(
            user=self.staff_user,
            action=AuditActions.CREATE_COURSE,
            object_type="Course",
            object_id=1,
            details="Log course details",
            ip_address="127.0.0.1"
        )
        self.assertEqual(log.user, self.staff_user)
        self.assertEqual(log.action, AuditActions.CREATE_COURSE)
        self.assertEqual(log.object_type, "Course")
        self.assertEqual(log.object_id, "1")
        self.assertEqual(log.details, "Log course details")
        self.assertEqual(log.ip_address, "127.0.0.1")

        # Anonymous user
        anon = AnonymousUser()
        log_anon = log_audit(
            user=anon,
            action=AuditActions.ISSUE_CERTIFICATE,
            object_type="Certificate",
            object_id=10,
            details="System action"
        )
        self.assertIsNone(log_anon.user)
        self.assertEqual(log_anon.action, AuditActions.ISSUE_CERTIFICATE)
        self.assertEqual(log_anon.object_id, "10")

    def test_audit_dashboard_permissions(self):
        # Anonymous redirect
        response = self.client.get(self.audit_dashboard_url)
        self.assertEqual(response.status_code, 302)

        # Student redirect
        self.client.login(username="student_audit", password="password123")
        response = self.client.get(self.audit_dashboard_url)
        self.assertEqual(response.status_code, 302)

        # Staff access
        self.client.login(username="staff_audit", password="password123")
        response = self.client.get(self.audit_dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "monitoring/audit_dashboard.html")

    def test_course_crud_and_analytics_auditing(self):
        self.client.login(username="staff_audit", password="password123")

        # Create Course
        response = self.client.post(
            reverse("create_course"),
            {
                "title": "New Audited Course",
                "description": "Details",
                "category": self.category.id,
                "tags": [self.tag.id]
            }
        )
        self.assertEqual(response.status_code, 302)
        course_log = AuditLog.objects.filter(action=AuditActions.CREATE_COURSE).first()
        self.assertIsNotNone(course_log)
        self.assertEqual(course_log.user, self.staff_user)
        self.assertEqual(course_log.object_type, "Course")
        self.assertIn("New Audited Course", course_log.details)

        # Edit Course
        response = self.client.post(
            reverse("edit_course", args=[self.course.id]),
            {
                "title": "UI/UX Principles Updated",
                "description": "Updated Details",
                "category": self.category.id,
                "tags": [self.tag.id]
            }
        )
        self.assertEqual(response.status_code, 302)
        edit_log = AuditLog.objects.filter(action=AuditActions.UPDATE_COURSE).first()
        self.assertIsNotNone(edit_log)
        self.assertEqual(edit_log.object_id, str(self.course.id))

        # View Analytics
        response = self.client.get(reverse("course_analytics", args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        analytics_log = AuditLog.objects.filter(action=AuditActions.VIEW_COURSE_ANALYTICS).first()
        self.assertIsNotNone(analytics_log)
        self.assertEqual(analytics_log.object_id, str(self.course.id))

        # Delete Course
        response = self.client.post(reverse("delete_course", args=[self.course.id]))
        self.assertEqual(response.status_code, 302)
        delete_log = AuditLog.objects.filter(action=AuditActions.DELETE_COURSE).first()
        self.assertIsNotNone(delete_log)
        self.assertEqual(delete_log.object_id, str(self.course.id))
        self.assertIn("UI/UX Principles", delete_log.details)

    def test_category_tag_crud_auditing(self):
        self.client.login(username="staff_audit", password="password123")

        # Category Create
        response = self.client.post(reverse("create_category"), {"name": "New Category"})
        self.assertEqual(response.status_code, 302)
        cat_log = AuditLog.objects.filter(action=AuditActions.CREATE_CATEGORY).first()
        self.assertIsNotNone(cat_log)
        self.assertEqual(cat_log.object_type, "Category")

        # Category Edit
        response = self.client.post(reverse("edit_category", args=[self.category.id]), {"name": "Design Updated"})
        self.assertEqual(response.status_code, 302)
        cat_edit = AuditLog.objects.filter(action=AuditActions.UPDATE_CATEGORY).first()
        self.assertIsNotNone(cat_edit)

        # Category Delete
        response = self.client.post(reverse("delete_category", args=[self.category.id]))
        self.assertEqual(response.status_code, 302)
        cat_del = AuditLog.objects.filter(action=AuditActions.DELETE_CATEGORY).first()
        self.assertIsNotNone(cat_del)

        # Tag Create
        response = self.client.post(reverse("create_tag"), {"name": "New Tag"})
        self.assertEqual(response.status_code, 302)
        tag_log = AuditLog.objects.filter(action=AuditActions.CREATE_TAG).first()
        self.assertIsNotNone(tag_log)

        # Tag Edit
        response = self.client.post(reverse("edit_tag", args=[self.tag.id]), {"name": "UX Updated"})
        self.assertEqual(response.status_code, 302)
        tag_edit = AuditLog.objects.filter(action=AuditActions.UPDATE_TAG).first()
        self.assertIsNotNone(tag_edit)

        # Tag Delete
        response = self.client.post(reverse("delete_tag", args=[self.tag.id]))
        self.assertEqual(response.status_code, 302)
        tag_del = AuditLog.objects.filter(action=AuditActions.DELETE_TAG).first()
        self.assertIsNotNone(tag_del)

    def test_quiz_crud_auditing(self):
        self.client.login(username="staff_audit", password="password123")

        # Quiz Create
        response = self.client.post(reverse("create_quiz"), {
            "course": self.course.id,
            "title": "Audited Quiz",
            "passing_score": 75
        })
        self.assertEqual(response.status_code, 302)
        quiz_log = AuditLog.objects.filter(action=AuditActions.CREATE_QUIZ).first()
        self.assertIsNotNone(quiz_log)

        # Quiz Edit
        response = self.client.post(reverse("edit_quiz", args=[self.quiz.id]), {
            "course": self.course.id,
            "title": "UX Quiz 1 Updated",
            "passing_score": 85
        })
        self.assertEqual(response.status_code, 302)
        quiz_edit = AuditLog.objects.filter(action=AuditActions.UPDATE_QUIZ).first()
        self.assertIsNotNone(quiz_edit)

        # Quiz Delete
        response = self.client.post(reverse("delete_quiz", args=[self.quiz.id]))
        self.assertEqual(response.status_code, 302)
        quiz_del = AuditLog.objects.filter(action=AuditActions.DELETE_QUIZ).first()
        self.assertIsNotNone(quiz_del)

    def test_announcement_publishing_auditing(self):
        self.client.login(username="staff_audit", password="password123")
        response = self.client.post(reverse("publish_announcement", args=[self.announcement.id]))
        self.assertEqual(response.status_code, 302)
        pub_log = AuditLog.objects.filter(action=AuditActions.PUBLISH_ANNOUNCEMENT).first()
        self.assertIsNotNone(pub_log)
        self.assertEqual(pub_log.object_id, str(self.announcement.id))

    def test_certificate_generation_auditing(self):
        material = Material.objects.create(
            course=self.course,
            title="Lesson 1",
            content="Read this."
        )
        LessonProgress.objects.create(
            student=self.student,
            material=material,
            completed=True
        )
        QuizAttempt.objects.create(
            student=self.student,
            quiz=self.quiz,
            score=90,
            passed=True
        )

        cert = generate_certificate(self.student, self.course)
        self.assertIsNotNone(cert)
        
        cert_log = AuditLog.objects.filter(action=AuditActions.ISSUE_CERTIFICATE).first()
        self.assertIsNotNone(cert_log)
        self.assertEqual(cert_log.user, self.student)
        self.assertEqual(cert_log.object_id, str(cert.id))

