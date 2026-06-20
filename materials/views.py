from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Material
from django.db.models import Count
from discussions.models import DiscussionThread
from discussions.forms import DiscussionThreadForm
from utils.security import user_is_enrolled
from monitoring.utils import log_audit, AuditActions, get_client_ip


@login_required
def material_detail(request, pk):
    material = get_object_or_404(
        Material,
        pk=pk
    )

    if not request.user.is_staff and not user_is_enrolled(request.user, material.course):
        log_audit(
            user=request.user,
            action=AuditActions.UNAUTHORIZED_ACCESS_ATTEMPT,
            object_type="Material",
            object_id=material.id,
            details=f"Unenrolled user attempted to access material: {material.title}",
            ip_address=get_client_ip(request)
        )
        return redirect("course_detail", pk=material.course.id)

    previous_material = (
        Material.objects.filter(
            course=material.course,
            order__lt=material.order
        )
        .order_by("-order")
        .first()
    )

    next_material = (
        Material.objects.filter(
            course=material.course,
            order__gt=material.order
        )
        .order_by("order")
        .first()
    )

    # Discussions
    threads = (
        DiscussionThread.objects
        .filter(material=material)
        .select_related("author", "material")
        .annotate(replies_count=Count("replies"))
    )

    if request.method == "POST" and "title" in request.POST:
        # Discussion submission
        form = DiscussionThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user
            thread.material = material
            thread.save()
            return redirect("material_detail", pk=material.id)
    else:
        form = DiscussionThreadForm()

    return render(
        request,
        "materials/material_detail.html",
        {
            "material": material,
            "previous_material": previous_material,
            "next_material": next_material,
            "threads": threads,
            "discussion_form": form,
        }
    )
