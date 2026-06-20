from django.contrib.admin.views.decorators import staff_member_required
from monitoring.utils import log_audit, AuditActions, get_client_ip
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Avg
from django.core.cache import cache
from courses.models import (
    Course,
    Category,
    Tag,
)
from materials.models import Material
from quizzes.models import Quiz, Question, QuizAttempt
from certificates.models import Certificate
from discussions.models import DiscussionThread, DiscussionReply
from announcements.models import Announcement
from enrollments.models import Enrollment
from .forms import (
    CourseCreateForm,
    MaterialCreateForm,
    QuizCreateForm,
    QuestionCreateForm,
    CategoryForm,
    TagForm,
)


@staff_member_required
def instructor_dashboard(request):
    total_courses = Course.objects.count()
    total_students = Enrollment.objects.values(
        "student"
    ).distinct().count()

    total_lessons = Material.objects.count()
    total_quizzes = Quiz.objects.count()
    total_questions = Question.objects.count()
    total_threads = DiscussionThread.objects.count()
    total_replies = DiscussionReply.objects.count()

    total_announcements = Announcement.objects.count()
    published_announcements = Announcement.objects.filter(is_published=True).count()

    recent_courses = Course.objects.order_by(
        "-created_at"
    )[:5]

    recent_enrollments = Enrollment.objects.select_related(
        "student",
        "course"
    ).order_by(
        "-enrolled_at"
    )[:5]

    return render(
        request,
        "instructor/dashboard.html",
        {
            "total_courses": total_courses,
            "total_students": total_students,
            "total_lessons": total_lessons,
            "total_quizzes": total_quizzes,
            "total_questions": total_questions,
            "total_threads": total_threads,
            "total_replies": total_replies,
            "recent_courses": recent_courses,
            "recent_enrollments": recent_enrollments,
            "total_announcements": total_announcements,
            "published_announcements": published_announcements,
        }
    )


@staff_member_required
def create_course(request):

    if request.method == "POST":

        form = CourseCreateForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            course = form.save()
            log_audit(
                user=request.user,
                action=AuditActions.CREATE_COURSE,
                object_type="Course",
                object_id=course.id,
                details=f"Created course: {course.title}",
                ip_address=get_client_ip(request)
            )

            return redirect(
                "instructor_dashboard"
            )

    else:

        form = CourseCreateForm()

    return render(
        request,
        "instructor/create_course.html",
        {
            "form": form
        }
    )


@staff_member_required
def manage_courses(request):
    courses = Course.objects.select_related("category").order_by("-created_at")
    return render(
        request,
        "instructor/manage_courses.html",
        {
            "courses": courses
        }
    )


@staff_member_required
def edit_course(request, pk):
    course = get_object_or_404(Course, pk=pk)

    if request.method == "POST":

        form = CourseCreateForm(
            request.POST,
            request.FILES,
            instance=course
        )

        if form.is_valid():

            course = form.save()
            log_audit(
                user=request.user,
                action=AuditActions.UPDATE_COURSE,
                object_type="Course",
                object_id=course.id,
                details=f"Updated course: {course.title}",
                ip_address=get_client_ip(request)
            )

            return redirect(
                "manage_courses"
            )

    else:

        form = CourseCreateForm(instance=course)

    return render(
        request,
        "instructor/edit_course.html",
        {
            "form": form,
            "course": course
        }
    )


@staff_member_required
def delete_course(request, pk):
    course = get_object_or_404(Course, pk=pk)

    if request.method == "POST":
        course_title = course.title
        course_id = course.id
        course.delete()
        log_audit(
            user=request.user,
            action=AuditActions.DELETE_COURSE,
            object_type="Course",
            object_id=course_id,
            details=f"Deleted course: {course_title}",
            ip_address=get_client_ip(request)
        )
        return redirect("manage_courses")

    return render(
        request,
        "instructor/delete_course.html",
        {
            "course": course
        }
    )


@staff_member_required
def manage_materials(request):
    materials = Material.objects.select_related(
        "course"
    ).order_by("-created_at")

    return render(
        request,
        "instructor/manage_materials.html",
        {
            "materials": materials
        }
    )


@staff_member_required
def create_material(request):
    if request.method == "POST":
        form = MaterialCreateForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            form.save()
            return redirect("manage_materials")
    else:
        form = MaterialCreateForm()

    return render(
        request,
        "instructor/create_material.html",
        {
            "form": form
        }
    )


@staff_member_required
def edit_material(request, pk):
    material = get_object_or_404(Material, pk=pk)

    if request.method == "POST":
        form = MaterialCreateForm(
            request.POST,
            request.FILES,
            instance=material
        )

        if form.is_valid():
            form.save()
            return redirect("manage_materials")
    else:
        form = MaterialCreateForm(instance=material)

    return render(
        request,
        "instructor/edit_material.html",
        {
            "form": form,
            "material": material
        }
    )


@staff_member_required
def delete_material(request, pk):
    material = get_object_or_404(Material, pk=pk)

    if request.method == "POST":
        material.delete()
        return redirect("manage_materials")

    return render(
        request,
        "instructor/delete_material.html",
        {
            "material": material
        }
    )


@staff_member_required
def manage_quizzes(request):
    quizzes = Quiz.objects.select_related("course").order_by("-created_at")
    return render(
        request,
        "instructor/manage_quizzes.html",
        {
            "quizzes": quizzes
        }
    )


@staff_member_required
def create_quiz(request):
    if request.method == "POST":
        form = QuizCreateForm(request.POST)
        if form.is_valid():
            quiz = form.save()
            log_audit(
                user=request.user,
                action=AuditActions.CREATE_QUIZ,
                object_type="Quiz",
                object_id=quiz.id,
                details=f"Created quiz: {quiz.title}",
                ip_address=get_client_ip(request)
            )
            return redirect("manage_quizzes")
    else:
        form = QuizCreateForm()

    return render(
        request,
        "instructor/create_quiz.html",
        {
            "form": form
        }
    )


@staff_member_required
def edit_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)

    if request.method == "POST":
        form = QuizCreateForm(request.POST, instance=quiz)
        if form.is_valid():
            quiz = form.save()
            log_audit(
                user=request.user,
                action=AuditActions.UPDATE_QUIZ,
                object_type="Quiz",
                object_id=quiz.id,
                details=f"Updated quiz: {quiz.title}",
                ip_address=get_client_ip(request)
            )
            return redirect("manage_quizzes")
    else:
        form = QuizCreateForm(instance=quiz)

    return render(
        request,
        "instructor/edit_quiz.html",
        {
            "form": form,
            "quiz": quiz
        }
    )


@staff_member_required
def delete_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)

    if request.method == "POST":
        quiz_title = quiz.title
        quiz_id = quiz.id
        quiz.delete()
        log_audit(
            user=request.user,
            action=AuditActions.DELETE_QUIZ,
            object_type="Quiz",
            object_id=quiz_id,
            details=f"Deleted quiz: {quiz_title}",
            ip_address=get_client_ip(request)
        )
        return redirect("manage_quizzes")

    return render(
        request,
        "instructor/delete_quiz.html",
        {
            "quiz": quiz
        }
    )


@staff_member_required
def manage_questions(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = Question.objects.filter(quiz=quiz).order_by("id")
    return render(
        request,
        "instructor/manage_questions.html",
        {
            "quiz": quiz,
            "questions": questions
        }
    )


@staff_member_required
def create_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == "POST":
        form = QuestionCreateForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            return redirect("manage_questions", quiz_id=quiz.id)
    else:
        form = QuestionCreateForm()

    return render(
        request,
        "instructor/create_question.html",
        {
            "form": form,
            "quiz": quiz
        }
    )


@staff_member_required
def edit_question(request, pk):
    question = get_object_or_404(Question, pk=pk)

    if request.method == "POST":
        form = QuestionCreateForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect("manage_questions", quiz_id=question.quiz.id)
    else:
        form = QuestionCreateForm(instance=question)

    return render(
        request,
        "instructor/edit_question.html",
        {
            "form": form,
            "question": question
        }
    )


@staff_member_required
def delete_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    quiz_id = question.quiz.id

    if request.method == "POST":
        question.delete()
        return redirect("manage_questions", quiz_id=quiz_id)

    return render(
        request,
        "instructor/delete_question.html",
        {
            "question": question
        }
    )


@staff_member_required
def manage_categories(request):
    categories = Category.objects.order_by("name")

    return render(
        request,
        "instructor/manage_categories.html",
        {
            "categories": categories
        }
    )


@staff_member_required
def create_category(request):

    if request.method == "POST":

        form = CategoryForm(request.POST)

        if form.is_valid():
            category = form.save()
            log_audit(
                user=request.user,
                action=AuditActions.CREATE_CATEGORY,
                object_type="Category",
                object_id=category.id,
                details=f"Created category: {category.name}",
                ip_address=get_client_ip(request)
            )

            return redirect(
                "manage_categories"
            )

    else:
        form = CategoryForm()

    return render(
        request,
        "instructor/create_category.html",
        {
            "form": form
        }
    )


@staff_member_required
def edit_category(request, pk):

    category = get_object_or_404(
        Category,
        pk=pk
    )

    if request.method == "POST":

        form = CategoryForm(
            request.POST,
            instance=category
        )

        if form.is_valid():

            category = form.save()
            log_audit(
                user=request.user,
                action=AuditActions.UPDATE_CATEGORY,
                object_type="Category",
                object_id=category.id,
                details=f"Updated category: {category.name}",
                ip_address=get_client_ip(request)
            )

            return redirect(
                "manage_categories"
            )

    else:

        form = CategoryForm(
            instance=category
        )

    return render(
        request,
        "instructor/edit_category.html",
        {
            "form": form,
            "category": category,
        }
    )


@staff_member_required
def delete_category(request, pk):

    category = get_object_or_404(
        Category,
        pk=pk
    )

    if request.method == "POST":

        category_name = category.name
        category_id = category.id
        category.delete()
        log_audit(
            user=request.user,
            action=AuditActions.DELETE_CATEGORY,
            object_type="Category",
            object_id=category_id,
            details=f"Deleted category: {category_name}",
            ip_address=get_client_ip(request)
        )

        return redirect(
            "manage_categories"
        )

    return render(
        request,
        "instructor/delete_category.html",
        {
            "category": category
        }
    )


@staff_member_required
def manage_tags(request):
    tags = Tag.objects.order_by("name")

    return render(
        request,
        "instructor/manage_tags.html",
        {
            "tags": tags
        }
    )


@staff_member_required
def create_tag(request):

    if request.method == "POST":

        form = TagForm(request.POST)

        if form.is_valid():
            tag = form.save()
            log_audit(
                user=request.user,
                action=AuditActions.CREATE_TAG,
                object_type="Tag",
                object_id=tag.id,
                details=f"Created tag: {tag.name}",
                ip_address=get_client_ip(request)
            )

            return redirect(
                "manage_tags"
            )

    else:
        form = TagForm()

    return render(
        request,
        "instructor/create_tag.html",
        {
            "form": form
        }
    )


@staff_member_required
def edit_tag(request, pk):

    tag = get_object_or_404(
        Tag,
        pk=pk
    )

    if request.method == "POST":

        form = TagForm(
            request.POST,
            instance=tag
        )

        if form.is_valid():
            tag = form.save()
            log_audit(
                user=request.user,
                action=AuditActions.UPDATE_TAG,
                object_type="Tag",
                object_id=tag.id,
                details=f"Updated tag: {tag.name}",
                ip_address=get_client_ip(request)
            )

            return redirect(
                "manage_tags"
            )

    else:

        form = TagForm(
            instance=tag
        )

    return render(
        request,
        "instructor/edit_tag.html",
        {
            "form": form,
            "tag": tag
        }
    )


@staff_member_required
def delete_tag(request, pk):

    tag = get_object_or_404(
        Tag,
        pk=pk
    )

    if request.method == "POST":

        tag_name = tag.name
        tag_id = tag.id
        tag.delete()
        log_audit(
            user=request.user,
            action=AuditActions.DELETE_TAG,
            object_type="Tag",
            object_id=tag_id,
            details=f"Deleted tag: {tag_name}",
            ip_address=get_client_ip(request)
        )

        return redirect(
            "manage_tags"
        )

    return render(
        request,
        "instructor/delete_tag.html",
        {
            "tag": tag
        }
    )


def get_course_analytics_data(course):
    cache_key = f"course_analytics:v1:{course.id}"
    data = cache.get(cache_key)
    if not data:
        # Get enrollments for the course
        enrollments = Enrollment.objects.filter(course=course)
        total_enrollments = enrollments.count()

        # Get completions (progress_percentage == 100)
        completed_enrollments = sum(1 for e in enrollments if e.get_progress_percentage() == 100)
        completion_rate = int((completed_enrollments / total_enrollments) * 100) if total_enrollments > 0 else 0

        # Average Quiz score
        avg_score = QuizAttempt.objects.filter(quiz__course=course).aggregate(Avg("score"))["score__avg"] or 0
        average_quiz_score = round(avg_score)

        # Certificates issued
        certificate_count = Certificate.objects.filter(course=course).count()

        # Discussion metrics
        discussion_threads = DiscussionThread.objects.filter(material__lesson__course=course).count()
        discussion_replies = DiscussionReply.objects.filter(thread__material__lesson__course=course).count()

        # Recent activity (evaluate as list for caching)
        recent_attempts = list(QuizAttempt.objects.filter(quiz__course=course).select_related("student", "quiz").order_by("-attempted_at")[:5])
        recent_enrollments = list(enrollments.select_related("student").order_by("-enrolled_at")[:5])

        data = {
            "total_enrollments": total_enrollments,
            "completion_rate": completion_rate,
            "average_quiz_score": average_quiz_score,
            "certificate_count": certificate_count,
            "discussion_threads": discussion_threads,
            "discussion_replies": discussion_replies,
            "recent_attempts": recent_attempts,
            "recent_enrollments": recent_enrollments,
        }
        cache.set(cache_key, data, timeout=60)
    return data


@staff_member_required
def course_analytics(request, pk):
    course = get_object_or_404(Course, pk=pk)

    log_audit(
        user=request.user,
        action=AuditActions.VIEW_COURSE_ANALYTICS,
        object_type="Course",
        object_id=course.id,
        details=f"Viewed analytics for course: {course.title}",
        ip_address=get_client_ip(request)
    )

    data = get_course_analytics_data(course)
    data["course"] = course

    return render(
        request,
        "instructor/course_analytics.html",
        data
    )

