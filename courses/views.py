from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from .models import Course, Category, Tag, CourseReview
from .forms import ReviewForm
from enrollments.models import Enrollment
from materials.models import Material
from quizzes.models import Quiz, QuizAttempt
from progress.models import LessonProgress
from progress.services import calculate_course_progress
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, FloatField, Value
from django.db.models.functions import Coalesce



def get_popular_courses():
    cache_key = "popular_courses:v1"
    popular_courses = cache.get(cache_key)
    if not popular_courses:
        popular_courses = list(
            Course.objects
            .select_related("category")
            .prefetch_related("tags")
            .annotate(
                enrollment_count=Count(
                    "enrollment",
                    distinct=True
                ),
                review_count=Count(
                    "reviews",
                    distinct=True
                ),
                avg_rating=Coalesce(
                    Avg("reviews__rating"),
                    Value(0.0),
                    output_field=FloatField(),
                ),
            )
            .annotate(
                popularity_score=
                Count("enrollment", distinct=True)
                +
                Count("reviews", distinct=True)
                +
                Coalesce(
                    Avg("reviews__rating"),
                    Value(0.0),
                    output_field=FloatField(),
                )
            )
            .order_by("-popularity_score")[:6]
        )
        cache.set(cache_key, popular_courses, timeout=300)
    return popular_courses


def get_recommended_courses(user):
    cache_key = f"recommendations:v1:{user.id}"
    recommended = cache.get(cache_key)
    if not recommended:
        enrolled_courses = (
            Course.objects.filter(
                enrollment__student=user
            )
            .prefetch_related("tags")
        )

        enrolled_course_ids = list(
            enrolled_courses.values_list(
                "id",
                flat=True
            )
        )

        category_ids = list(
            enrolled_courses.values_list(
                "category_id",
                flat=True
            )
        )

        tag_ids = list(
            enrolled_courses.values_list(
                "tags__id",
                flat=True
            )
        )

        recommended = list(
            Course.objects
            .exclude(
                id__in=enrolled_course_ids
            )
            .filter(
                Q(category_id__in=category_ids)
                |
                Q(tags__id__in=tag_ids)
            )
            .distinct()
            .annotate(
                review_count=Count(
                    "reviews",
                    distinct=True
                ),
                enrollment_count=Count(
                    "enrollment",
                    distinct=True
                ),
                avg_rating=Coalesce(
                    Avg("reviews__rating"),
                    Value(0.0),
                    output_field=FloatField(),
                ),
            )
            .order_by(
                "-avg_rating",
                "-enrollment_count",
                "-review_count"
            )[:6]
        )
        cache.set(cache_key, recommended, timeout=300)
    return recommended


def course_list(request):
    courses = Course.objects.select_related("category").prefetch_related("tags").all()
    popular_courses = get_popular_courses()

    return render(
        request,
        "courses/course_list.html",
        {
            "courses": courses,
            "popular_courses": popular_courses,
        }
    )


def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)

    is_enrolled = (
        request.user.is_authenticated
        and Enrollment.objects.filter(student=request.user, course=course).exists()
    )

    materials = Material.objects.filter(course=course)
    total_lessons = materials.count()
    completed_lessons = 0
    progress_percentage = 0
    completed_material_ids = set()
    attempted_quiz_ids = set()

    if request.user.is_authenticated:
        progress = calculate_course_progress(request.user, course)
        completed_lessons = progress["completed_lessons"]
        progress_percentage = progress["percentage"]
        completed_material_ids = set(
            LessonProgress.objects.filter(
                student=request.user, material__course=course, completed=True
            ).values_list("material_id", flat=True)
        )
        attempted_quiz_ids = set(
            QuizAttempt.objects.filter(student=request.user, quiz__course=course)
            .values_list("quiz_id", flat=True)
        )

    quizzes = Quiz.objects.filter(course=course)
    reviews = CourseReview.objects.filter(course=course).select_related("student").order_by("-created_at")
    review_form = ReviewForm() if is_enrolled else None

    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "is_enrolled": is_enrolled,
            "materials": materials,
            "quizzes": quizzes,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "progress_percentage": progress_percentage,
            "completed_material_ids": completed_material_ids,
            "attempted_quiz_ids": attempted_quiz_ids,
            "reviews": reviews,
            "review_form": review_form,
        },
    )



@login_required
def post_course_review(request, pk):
    """Handle review form submission — separate from course_detail GET view."""
    course = get_object_or_404(Course, pk=pk)

    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        return redirect("course_detail", pk=pk)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            CourseReview.objects.update_or_create(
                course=course,
                student=request.user,
                defaults={
                    "rating": form.cleaned_data["rating"],
                    "comment": form.cleaned_data["comment"],
                },
            )
            messages.success(request, "Your review has been saved.")

    return redirect("course_detail", pk=pk)


def search_courses(request):
    query = request.GET.get("q", "")
    category = request.GET.get("category")
    tag = request.GET.get("tag")
    sort = request.GET.get("sort")

    courses = Course.objects.all().select_related(
        "category"
    ).prefetch_related(
        "tags"
    )

    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    if category:
        courses = courses.filter(
            category_id=category
        )

    if tag:
        courses = courses.filter(
            tags__id=tag
        )

    courses = courses.distinct()

    courses = courses.annotate(
        review_count=Count("reviews"),
        avg_rating=Avg("reviews__rating")
    )

    if sort == "rating":
        courses = courses.order_by("-avg_rating")

    elif sort == "reviews":
        courses = courses.order_by("-review_count")

    else:
        courses = courses.order_by("-created_at")

    paginator = Paginator(
        courses,
        6
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )

    categories = Category.objects.all().order_by("name")
    tags = Tag.objects.all().order_by("name")

    return render(
        request,
        "courses/search_results.html",
        {
            "query": query,
            "page_obj": page_obj,
            "categories": categories,
            "tags": tags,
            "category": category,
            "tag": tag,
            "sort": sort,
        }
    )

