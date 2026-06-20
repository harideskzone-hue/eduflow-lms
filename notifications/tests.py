from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from notifications.models import Notification, NotificationPreference
from notifications.utils import send_notification
from profiles.models import NotificationLog

User = get_user_model()


class NotificationPreferenceTests(TestCase):
    def setUp(self):
        # Create student user
        self.student = User.objects.create_user(
            username="preference_student",
            email="pref@example.com",
            password="password123"
        )

    def test_preference_defaults_are_enabled(self):
        # Trigger get_or_create preferences
        prefs, created = NotificationPreference.objects.get_or_create(user=self.student)
        self.assertTrue(created)
        self.assertTrue(prefs.email_enrollments)
        self.assertTrue(prefs.email_quizzes)
        self.assertTrue(prefs.email_certificates)
        self.assertTrue(prefs.email_discussions)
        self.assertTrue(prefs.email_announcements)

    def test_preference_record_auto_created(self):
        # Assert student has no preference record
        self.assertFalse(NotificationPreference.objects.filter(user=self.student).exists())

        # Calling send_notification should auto-create the preference record
        send_notification(
            user=self.student,
            title="Auto Preference Creation Test",
            message="Testing preference auto-creation.",
            category="quizzes"
        )

        # Assert record now exists
        self.assertTrue(NotificationPreference.objects.filter(user=self.student).exists())

    def test_disabled_preferences_restrict_emails(self):
        # Create user preferences with quizzes and announcements disabled
        prefs, _ = NotificationPreference.objects.get_or_create(user=self.student)
        prefs.email_quizzes = False
        prefs.email_announcements = False
        prefs.save()

        # Clear mail outbox and log counts
        mail.outbox = []
        NotificationLog.objects.all().delete()
        Notification.objects.all().delete()

        # Trigger send_notification for quizzes (disabled)
        send_notification(
            user=self.student,
            title="Quiz Result Fail Notification",
            message="Score details.",
            category="quizzes"
        )

        # Assert: in-app notification is created
        self.assertEqual(Notification.objects.filter(user=self.student).count(), 1)
        # Assert: no outbound email sent, no notification log created
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(NotificationLog.objects.count(), 0)

        # Trigger send_notification for announcements (disabled)
        send_notification(
            user=self.student,
            title="Important Alert",
            message="Announcement details.",
            category="announcements"
        )

        # Assert: 2 in-app notifications exist total
        self.assertEqual(Notification.objects.filter(user=self.student).count(), 2)
        # Assert: no outbound email sent, no notification log created
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(NotificationLog.objects.count(), 0)

    def test_enabled_preferences_allow_emails(self):
        # Ensure preference defaults are enabled
        NotificationPreference.objects.get_or_create(user=self.student)

        # Clear mail outbox
        mail.outbox = []
        NotificationLog.objects.all().delete()

        # Trigger send_notification for quizzes
        send_notification(
            user=self.student,
            title="Quiz Result Successful",
            message="Score details.",
            category="quizzes"
        )

        # Assert: both in-app, email, and audit logs are recorded
        self.assertEqual(Notification.objects.filter(user=self.student, title="Quiz Result Successful").count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "[EduFlow] Quiz Result Successful")
        self.assertEqual(NotificationLog.objects.filter(recipient=self.student).count(), 1)

    def test_preferences_view_post_saves_settings(self):
        # Log in student
        self.client.login(username="preference_student", password="password123")
        pref_url = reverse("notification_preferences")

        # GET request should load preferences successfully
        response = self.client.get(pref_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "notifications/preferences.html")

        # POST request to disable everything except discussions
        response = self.client.post(pref_url, {
            "email_discussions": "on"
        })
        # Assert redirects to avoid resubmission
        self.assertEqual(response.status_code, 302)

        # Verify updated values in DB
        prefs = NotificationPreference.objects.get(user=self.student)
        self.assertFalse(prefs.email_enrollments)
        self.assertFalse(prefs.email_quizzes)
        self.assertFalse(prefs.email_certificates)
        self.assertTrue(prefs.email_discussions)
        self.assertFalse(prefs.email_announcements)
