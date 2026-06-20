from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from courses.models import Course
from enrollments.models import Enrollment
from notifications.models import Notification
from profiles.models import NotificationLog
from announcements.models import Announcement

User = get_user_model()


class AnnouncementEmailTests(TestCase):
    def setUp(self):
        # Create a staff user (admin/instructor)
        self.staff_user = User.objects.create_user(
            username="staff_ann",
            email="staff_ann@example.com",
            password="password123",
            is_staff=True
        )

        # Create two students
        self.student_a = User.objects.create_user(
            username="student_a",
            email="student_a@example.com",
            password="password123",
            is_staff=False
        )
        self.student_b = User.objects.create_user(
            username="student_b",
            email="student_b@example.com",
            password="password123",
            is_staff=False
        )

        # Create a course
        self.course = Course.objects.create(
            title="Notification Targeting Course",
            description="LMS Notifications Targeting Course"
        )

    def test_global_announcement_email_delivery(self):
        # Create a global announcement (course=None)
        announcement = Announcement.objects.create(
            title="Global Alert",
            message="This is a global notice for all students.",
            created_by=self.staff_user,
            course=None
        )

        # Log in as staff to publish
        self.client.login(username="staff_ann", password="password123")
        publish_url = reverse("publish_announcement", kwargs={"pk": announcement.pk})

        # Clear outbox before test
        mail.outbox = []

        response = self.client.post(publish_url)
        self.assertEqual(response.status_code, 302)

        # Check in-app Notifications: 2 notifications created (one for each non-staff student)
        notifications = Notification.objects.filter(title__contains="Global Alert")
        self.assertEqual(notifications.count(), 2)

        # Check mail.outbox: 2 emails sent
        self.assertEqual(len(mail.outbox), 2)
        for email in mail.outbox:
            self.assertIn("[EduFlow] Global Alert", email.subject)
            self.assertEqual(email.body, "This is a global notice for all students.")

        # Check NotificationLog records: 2 created
        self.assertEqual(NotificationLog.objects.count(), 2)
        self.assertTrue(NotificationLog.objects.filter(recipient=self.student_a, subject="[EduFlow] Global Alert").exists())
        self.assertTrue(NotificationLog.objects.filter(recipient=self.student_b, subject="[EduFlow] Global Alert").exists())

    def test_course_announcement_targeting(self):
        # Enroll Student A in target course. Student B remains un-enrolled.
        Enrollment.objects.create(student=self.student_a, course=self.course)

        # Create course announcement
        announcement = Announcement.objects.create(
            title="Course Specific Update",
            message="Only for course enrolled students.",
            created_by=self.staff_user,
            course=self.course
        )

        # Log in as staff to publish
        self.client.login(username="staff_ann", password="password123")
        publish_url = reverse("publish_announcement", kwargs={"pk": announcement.pk})

        # Clear outbox before test
        mail.outbox = []

        response = self.client.post(publish_url)
        self.assertEqual(response.status_code, 302)

        # Check in-app Notifications: only 1 for Student A
        self.assertEqual(Notification.objects.filter(user=self.student_a, title__contains="Course Specific Update").count(), 1)
        self.assertEqual(Notification.objects.filter(user=self.student_b, title__contains="Course Specific Update").count(), 0)

        # Check mail.outbox: 1 email sent to Student A
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.student_a.email])
        self.assertIn("[EduFlow] Course Specific Update", mail.outbox[0].subject)

        # Check NotificationLog: 1 for Student A, 0 for Student B
        self.assertEqual(NotificationLog.objects.filter(recipient=self.student_a, subject="[EduFlow] Course Specific Update").count(), 1)
        self.assertEqual(NotificationLog.objects.filter(recipient=self.student_b, subject="[EduFlow] Course Specific Update").count(), 0)

    def test_duplicate_publish_protection(self):
        # Create a global announcement
        announcement = Announcement.objects.create(
            title="Idempotent Alert",
            message="Unique messaging content.",
            created_by=self.staff_user,
            course=None
        )

        # Log in as staff
        self.client.login(username="staff_ann", password="password123")
        publish_url = reverse("publish_announcement", kwargs={"pk": announcement.pk})

        # Clear outbox
        mail.outbox = []

        # First publish
        response1 = self.client.post(publish_url)
        self.assertEqual(response1.status_code, 302)

        # Check counts after first publish
        notif_count_before = Notification.objects.filter(title__contains="Idempotent Alert").count()
        mail_count_before = len(mail.outbox)
        log_count_before = NotificationLog.objects.filter(subject="[EduFlow] Idempotent Alert").count()

        self.assertEqual(notif_count_before, 2)
        self.assertEqual(mail_count_before, 2)
        self.assertEqual(log_count_before, 2)

        # Second publish attempt
        response2 = self.client.post(publish_url)
        self.assertEqual(response2.status_code, 302)

        # Check counts after second publish: must remain exactly the same
        notif_count_after = Notification.objects.filter(title__contains="Idempotent Alert").count()
        mail_count_after = len(mail.outbox)
        log_count_after = NotificationLog.objects.filter(subject="[EduFlow] Idempotent Alert").count()

        self.assertEqual(notif_count_before, notif_count_after)
        self.assertEqual(mail_count_before, mail_count_after)
        self.assertEqual(log_count_before, log_count_after)
