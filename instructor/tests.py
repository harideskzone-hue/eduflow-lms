from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from courses.models import Course, Category, Tag

User = get_user_model()

class CategoryTagCRUDTests(TestCase):
    def setUp(self):
        # Create a staff user and a non-staff user
        self.staff_user = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="password123",
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="password123",
            is_staff=False
        )
        
        # Create initial test category and tag
        self.category = Category.objects.create(name="Web Development")
        self.tag = Tag.objects.create(name="Python")

    def test_staff_member_required_redirection(self):
        # When not logged in, should redirect to login page (which by default might not exist or be admin login)
        response = self.client.get(reverse("manage_categories"))
        self.assertEqual(response.status_code, 302)
        
        # When logged in as non-staff, should also redirect or fail
        self.client.login(username="student", password="password123")
        response = self.client.get(reverse("manage_categories"))
        self.assertEqual(response.status_code, 302)
        
        # When logged in as staff, should load page successfully
        self.client.login(username="staff", password="password123")
        response = self.client.get(reverse("manage_categories"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "instructor/manage_categories.html")

    def test_category_crud_flows(self):
        self.client.login(username="staff", password="password123")
        
        # 1. Create Category
        # GET create
        response = self.client.get(reverse("create_category"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "instructor/create_category.html")
        
        # POST create
        response = self.client.post(reverse("create_category"), {"name": "Data Science"})
        self.assertEqual(response.status_code, 302) # redirects to manage_categories
        self.assertTrue(Category.objects.filter(name="Data Science").exists())
        
        # 2. Edit Category
        category_to_edit = Category.objects.get(name="Data Science")
        # GET edit
        response = self.client.get(reverse("edit_category", kwargs={"pk": category_to_edit.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "instructor/edit_category.html")
        
        # POST edit
        response = self.client.post(
            reverse("edit_category", kwargs={"pk": category_to_edit.pk}),
            {"name": "Advanced Data Science"}
        )
        self.assertEqual(response.status_code, 302)
        category_to_edit.refresh_from_db()
        self.assertEqual(category_to_edit.name, "Advanced Data Science")
        
        # 3. Delete Category
        # GET delete (should show confirmation page)
        response = self.client.get(reverse("delete_category", kwargs={"pk": category_to_edit.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "instructor/delete_category.html")
        
        # POST delete (should actually delete and redirect)
        response = self.client.post(reverse("delete_category", kwargs={"pk": category_to_edit.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(name="Advanced Data Science").exists())

    def test_tag_crud_flows(self):
        self.client.login(username="staff", password="password123")
        
        # 1. Create Tag
        # GET create
        response = self.client.get(reverse("create_tag"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "instructor/create_tag.html")
        
        # POST create
        response = self.client.post(reverse("create_tag"), {"name": "Django"})
        self.assertEqual(response.status_code, 302) # redirects to manage_tags
        self.assertTrue(Tag.objects.filter(name="Django").exists())
        
        # 2. Edit Tag
        tag_to_edit = Tag.objects.get(name="Django")
        # GET edit
        response = self.client.get(reverse("edit_tag", kwargs={"pk": tag_to_edit.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "instructor/edit_tag.html")
        
        # POST edit
        response = self.client.post(
            reverse("edit_tag", kwargs={"pk": tag_to_edit.pk}),
            {"name": "Django Framework"}
        )
        self.assertEqual(response.status_code, 302)
        tag_to_edit.refresh_from_db()
        self.assertEqual(tag_to_edit.name, "Django Framework")
        
        # 3. Delete Tag
        # GET delete (should show confirmation page)
        response = self.client.get(reverse("delete_tag", kwargs={"pk": tag_to_edit.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "instructor/delete_tag.html")
        
        # POST delete (should actually delete and redirect)
        response = self.client.post(reverse("delete_tag", kwargs={"pk": tag_to_edit.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Tag.objects.filter(name="Django Framework").exists())

    def test_course_creation_with_category_and_tags(self):
        self.client.login(username="staff", password="password123")
        
        # We need another tag to test multi-selection
        other_tag = Tag.objects.create(name="Web")
        
        # Test creation of course with category and tags
        response = self.client.post(reverse("create_course"), {
            "title": "Django Deep Dive",
            "description": "Learn Django in depth",
            "category": self.category.pk,
            "tags": [self.tag.pk, other_tag.pk],
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify course was created with the assigned category and tags
        course = Course.objects.get(title="Django Deep Dive")
        self.assertEqual(course.category, self.category)
        self.assertEqual(course.tags.count(), 2)
        self.assertIn(self.tag, course.tags.all())
        self.assertIn(other_tag, course.tags.all())
        
        # Test editing course category and tags
        new_category = Category.objects.create(name="Programming")
        response = self.client.post(reverse("edit_course", kwargs={"pk": course.pk}), {
            "title": "Django Deep Dive Advanced",
            "description": "Learn Django in depth",
            "category": new_category.pk,
            "tags": [other_tag.pk], # Keep only the 'Web' tag
        })
        self.assertEqual(response.status_code, 302)
        
        course.refresh_from_db()
        self.assertEqual(course.title, "Django Deep Dive Advanced")
        self.assertEqual(course.category, new_category)
        self.assertEqual(course.tags.count(), 1)
        self.assertIn(other_tag, course.tags.all())
        self.assertNotIn(self.tag, course.tags.all())


class CourseAnalyticsTests(TestCase):
    def setUp(self):
        # Create a staff user and a non-staff user
        self.staff_user = User.objects.create_user(
            username="staff_analytics",
            email="staff_analytics@example.com",
            password="password123",
            is_staff=True
        )
        self.student_a = User.objects.create_user(
            username="student_a",
            email="a@example.com",
            password="password123",
            is_staff=False
        )
        self.student_b = User.objects.create_user(
            username="student_b",
            email="b@example.com",
            password="password123",
            is_staff=False
        )

        self.course = Course.objects.create(
            title="Analytics Target Course",
            description="Testing course analytics page"
        )

    def test_course_analytics_access_restricted(self):
        # 1. Anonymous redirects
        response = self.client.get(reverse("course_analytics", kwargs={"pk": self.course.pk}))
        self.assertEqual(response.status_code, 302)

        # 2. Regular user (student) redirects
        self.client.login(username="student_a", password="password123")
        response = self.client.get(reverse("course_analytics", kwargs={"pk": self.course.pk}))
        self.assertEqual(response.status_code, 302)

    def test_course_analytics_metrics(self):
        from enrollments.models import Enrollment
        from quizzes.models import Quiz, QuizAttempt
        from certificates.models import Certificate
        from discussions.models import DiscussionThread, DiscussionReply
        from materials.models import Material
        from progress.models import LessonProgress

        # Create materials for progress tracking
        material_1 = Material.objects.create(course=self.course, title="Lesson 1", content="Intro", order=1)
        material_2 = Material.objects.create(course=self.course, title="Lesson 2", content="Deep", order=2)

        # Enrollments
        Enrollment.objects.create(student=self.student_a, course=self.course)
        Enrollment.objects.create(student=self.student_b, course=self.course)

        # Progress: student_a completes 100%, student_b completes 50%
        LessonProgress.objects.create(student=self.student_a, material=material_1, completed=True)
        LessonProgress.objects.create(student=self.student_a, material=material_2, completed=True)

        LessonProgress.objects.create(student=self.student_b, material=material_1, completed=True)
        LessonProgress.objects.create(student=self.student_b, material=material_2, completed=False)

        # Quiz
        quiz = Quiz.objects.create(course=self.course, title="Course Quiz", passing_score=60)
        QuizAttempt.objects.create(student=self.student_a, quiz=quiz, score=80, passed=True)
        QuizAttempt.objects.create(student=self.student_b, quiz=quiz, score=40, passed=False)

        # Certificate for student_a
        Certificate.objects.create(student=self.student_a, course=self.course)

        # Discussions
        thread = DiscussionThread.objects.create(course=self.course, author=self.student_a, title="Target Discussion", content="Hey")
        DiscussionReply.objects.create(thread=thread, author=self.student_b, content="Reply here")

        # Login as staff
        self.client.login(username="staff_analytics", password="password123")
        response = self.client.get(reverse("course_analytics", kwargs={"pk": self.course.pk}))
        self.assertEqual(response.status_code, 200)

        # Verify values in context
        self.assertEqual(response.context["total_enrollments"], 2)
        # student_a completed both lessons -> 100%. student_b completed 1 out of 2 -> 50%. So completion_rate should be (1/2)*100 = 50%
        self.assertEqual(response.context["completion_rate"], 50)
        # average quiz score: (80 + 40) / 2 = 60
        self.assertEqual(response.context["average_quiz_score"], 60)
        self.assertEqual(response.context["certificate_count"], 1)
        self.assertEqual(response.context["discussion_threads"], 1)
        self.assertEqual(response.context["discussion_replies"], 1)

        # Check template rendering has elements
        self.assertContains(response, "Analytics Target Course")
        self.assertContains(response, "50%") # Completion rate or score
        self.assertContains(response, "Student_a")
        self.assertContains(response, "Student_b")
