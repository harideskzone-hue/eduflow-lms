from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from courses.models import Course
from enrollments.models import Enrollment
from materials.models import Material
from monitoring.models import AuditLog
from progress.models import LessonProgress, CourseCompletion
from progress.services import calculate_course_progress

User = get_user_model()


class LessonProgressTests(TestCase):
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
        self.staff_user = User.objects.create_user(
            username="staff1",
            email="staff1@example.com",
            password="Password123!",
            is_staff=True
        )

        self.course = Course.objects.create(
            title="Python Basics",
            description="Introductory Python programming."
        )

        self.material = Material.objects.create(
            course=self.course,
            title="Lesson 1: Syntax",
            content="Standard syntax details",
            order=1
        )
        self.material2 = Material.objects.create(
            course=self.course,
            title="Lesson 2: Variables",
            content="Variables details",
            order=2
        )

        # Enroll student in the course
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course
        )

        from quizzes.models import Quiz, Question
        self.quiz = Quiz.objects.create(
            course=self.course,
            title="Basics Quiz",
            passing_score=100
        )
        self.question = Question.objects.create(
            quiz=self.quiz,
            text="Is Python fun?",
            option_a="Yes",
            option_b="No",
            correct_answer="A",
            points=10
        )

        self.complete_url = reverse("complete_lesson", kwargs={"material_id": self.material.id})
        self.ajax_complete_url = reverse("mark_material_complete", kwargs={"pk": self.material.id})

    def test_anonymous_redirected(self):
        response = self.client.post(self.complete_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_enrolled_student_can_complete(self):
        self.client.force_login(self.student)
        response = self.client.post(self.complete_url)
        self.assertRedirects(response, reverse("material_detail", kwargs={"pk": self.material.pk}))

        # Verify LessonProgress was created
        progress = LessonProgress.objects.filter(student=self.student, material=self.material)
        self.assertTrue(progress.exists())
        self.assertTrue(progress.first().completed)

    def test_staff_user_can_complete(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(self.complete_url)
        self.assertRedirects(response, reverse("material_detail", kwargs={"pk": self.material.pk}))

        # Verify LessonProgress was created
        progress = LessonProgress.objects.filter(student=self.staff_user, material=self.material)
        self.assertTrue(progress.exists())
        self.assertTrue(progress.first().completed)

    def test_unenrolled_student_blocked(self):
        self.client.force_login(self.other_student)
        response = self.client.post(self.complete_url)
        # Should redirect to course detail
        self.assertRedirects(response, reverse("course_detail", kwargs={"pk": self.course.pk}))

        # Verify LessonProgress was NOT created
        progress = LessonProgress.objects.filter(student=self.other_student, material=self.material)
        self.assertFalse(progress.exists())

        # Verify UNAUTHORIZED_ACCESS_ATTEMPT audit log was generated
        logs = AuditLog.objects.filter(
            user=self.other_student,
            action="UNAUTHORIZED_ACCESS_ATTEMPT",
            object_type="Material",
            object_id=str(self.material.id)
        )
        self.assertTrue(logs.exists())

    def test_calculate_course_progress(self):
        # Initial progress is 0%
        prog = calculate_course_progress(self.student, self.course)
        self.assertEqual(prog["completed_lessons"], 0)
        self.assertEqual(prog["total_lessons"], 2)
        self.assertEqual(prog["percentage"], 0)
        self.assertFalse(prog["quiz_unlocked"])

        # Complete 1 lesson -> 50%
        LessonProgress.objects.create(student=self.student, material=self.material, completed=True)
        prog = calculate_course_progress(self.student, self.course)
        self.assertEqual(prog["completed_lessons"], 1)
        self.assertEqual(prog["percentage"], 50)
        self.assertFalse(prog["quiz_unlocked"])

        # Complete 2nd lesson -> 100%
        LessonProgress.objects.create(student=self.student, material=self.material2, completed=True)
        prog = calculate_course_progress(self.student, self.course)
        self.assertEqual(prog["completed_lessons"], 2)
        self.assertEqual(prog["percentage"], 100)
        self.assertTrue(prog["quiz_unlocked"])

    def test_ajax_mark_material_complete_success(self):
        self.client.force_login(self.student)
        response = self.client.post(self.ajax_complete_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["percentage"], 50)
        self.assertFalse(data["quiz_unlocked"])

    def test_course_completion_creates_once_at_100_percent(self):
        self.client.force_login(self.student)
        
        # Complete 1st lesson via AJAX
        res1 = self.client.post(reverse("mark_material_complete", kwargs={"pk": self.material.id}), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res1.json()["percentage"], 50)
        self.assertFalse(CourseCompletion.objects.filter(student=self.student, course=self.course).exists())

        # Complete 2nd lesson via AJAX -> Hits 100%
        res2 = self.client.post(reverse("mark_material_complete", kwargs={"pk": self.material2.id}), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res2.json()["percentage"], 100)
        self.assertTrue(res2.json()["quiz_unlocked"])
        
        # Verify CourseCompletion created
        completions = CourseCompletion.objects.filter(student=self.student, course=self.course)
        self.assertEqual(completions.count(), 1)

        # Mark complete again -> CourseCompletion count remains 1 and is not recreated
        res3 = self.client.post(reverse("mark_material_complete", kwargs={"pk": self.material2.id}), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(CourseCompletion.objects.filter(student=self.student, course=self.course).count(), 1)

    def test_full_guided_learning_journey_integration(self):
        # 1. Log in student
        self.client.force_login(self.student)

        # 2. Verify progress starts at 0%
        prog = calculate_course_progress(self.student, self.course)
        self.assertEqual(prog["percentage"], 0)

        # 3. Access quiz detail -> verify redirected (locked)
        quiz_url = reverse("quiz_detail", kwargs={"pk": self.quiz.id})
        res_quiz = self.client.get(quiz_url)
        self.assertRedirects(res_quiz, reverse("course_detail", kwargs={"pk": self.course.id}))

        # 4. Complete Lesson 1 via AJAX
        res_ajax1 = self.client.post(
            reverse("mark_material_complete", kwargs={"pk": self.material.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(res_ajax1.json()["percentage"], 50)
        self.assertFalse(res_ajax1.json()["quiz_unlocked"])

        # 5. Complete Lesson 2 via AJAX -> 100%
        res_ajax2 = self.client.post(
            reverse("mark_material_complete", kwargs={"pk": self.material2.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(res_ajax2.json()["percentage"], 100)
        self.assertTrue(res_ajax2.json()["quiz_unlocked"])
        self.assertTrue(CourseCompletion.objects.filter(student=self.student, course=self.course).exists())

        # 6. Verify quiz details is now unlocked (returns 200 OK)
        res_quiz_unlocked = self.client.get(quiz_url)
        self.assertEqual(res_quiz_unlocked.status_code, 200)

        # 7. Submit Quiz answers (correctly) -> pass
        res_submit = self.client.post(quiz_url, {
            f"question_{self.question.id}": "A"
        })
        
        # 8. Verify redirected to success page
        from certificates.models import Certificate
        cert = Certificate.objects.get(student=self.student, course=self.course)
        self.assertRedirects(res_submit, reverse("certificate_success", kwargs={"certificate_id": cert.certificate_id}))

        # 9. Verify success page loads successfully
        res_success = self.client.get(reverse("certificate_success", kwargs={"certificate_id": cert.certificate_id}))
        self.assertEqual(res_success.status_code, 200)

        # 10. Verify student learning report loads successfully
        report_url = reverse("student_learning_report", kwargs={"course_id": self.course.id})
        res_report = self.client.get(report_url)
        self.assertEqual(res_report.status_code, 200)
        self.assertContains(res_report, "Course Started 🚀")
        self.assertContains(res_report, "Lesson Completed")
        self.assertContains(res_report, "Certificate Earned 🏆")



