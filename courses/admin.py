from django.contrib import admin
from .models import (
    Category,
    Tag,
    Course,
    CourseReview,
)

admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Course)
admin.site.register(CourseReview)
