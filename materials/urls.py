from django.urls import path

from .views import material_detail
from progress.views import mark_material_complete


urlpatterns = [
    path(
        "<int:pk>/",
        material_detail,
        name="material_detail"
    ),
    path(
        "<int:pk>/complete/",
        mark_material_complete,
        name="mark_material_complete"
    ),
]

