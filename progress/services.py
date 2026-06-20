from materials.models import Material
from .models import LessonProgress


def calculate_course_progress(student, course):
    """
    Calculate the progress of a student in a course.
    Returns a dict with:
        completed_lessons: int
        total_lessons: int
        percentage: int (0 to 100)
        quiz_unlocked: bool
    """
    total_lessons = Material.objects.filter(course=course).count()
    if total_lessons == 0:
        return {
            "completed_lessons": 0,
            "total_lessons": 0,
            "percentage": 0,
            "quiz_unlocked": False
        }

    completed_lessons = LessonProgress.objects.filter(
        student=student,
        material__course=course,
        completed=True
    ).count()

    percentage = int((completed_lessons / total_lessons) * 100)
    percentage = max(0, min(100, percentage))

    return {
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "percentage": percentage,
        "quiz_unlocked": percentage == 100
    }
