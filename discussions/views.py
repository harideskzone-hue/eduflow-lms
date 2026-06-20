from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from courses.models import Course
from enrollments.models import Enrollment
from .models import DiscussionThread, DiscussionReply
from .forms import DiscussionThreadForm, DiscussionReplyForm
from notifications.utils import send_notification
from utils.logging_utils import log_event, log_error
from utils.security import user_is_enrolled
from monitoring.utils import log_audit, AuditActions, get_client_ip
from django_ratelimit.decorators import ratelimit


@login_required
@ratelimit(key="user", rate="10/m", method="POST", block=True)
def course_discussion(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Validate enrollment
    is_enrolled = user_is_enrolled(request.user, course)

    if not is_enrolled and not request.user.is_staff:
        log_audit(
            user=request.user,
            action=AuditActions.UNAUTHORIZED_ACCESS_ATTEMPT,
            object_type="Discussion",
            object_id=course.id,
            details=f"Unenrolled user attempted to access course discussion board: {course.title}",
            ip_address=get_client_ip(request)
        )
        return redirect("course_detail", pk=course.id)

    threads = (
        DiscussionThread.objects
        .filter(course=course)
        .select_related("author", "course")
        .annotate(_replies_count=Count("replies"))
    )

    if request.method == "POST":
        form = DiscussionThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user
            thread.course = course
            thread.save()
            return redirect("course_discussion", course_id=course.id)
    else:
        form = DiscussionThreadForm()

    return render(
        request,
        "discussions/course_discussion.html",
        {
            "course": course,
            "threads": threads,
            "form": form,
            "is_enrolled": is_enrolled or request.user.is_staff,
        }
    )


@login_required
@ratelimit(key="user", rate="10/m", method="POST", block=True)
def thread_detail(request, thread_id):
    thread = get_object_or_404(DiscussionThread, id=thread_id)
    material = thread.material
    course = material.course

    # Validate enrollment
    is_enrolled = user_is_enrolled(request.user, course)

    if not is_enrolled and not request.user.is_staff:
        log_audit(
            user=request.user,
            action=AuditActions.UNAUTHORIZED_ACCESS_ATTEMPT,
            object_type="Discussion",
            object_id=course.id,
            details=f"Unenrolled user attempted to access course thread details: {course.title}",
            ip_address=get_client_ip(request)
        )
        return redirect("course_detail", pk=course.id)

    replies = thread.replies.select_related("author")

    if request.method == "POST":
        form = DiscussionReplyForm(request.POST)

        if form.is_valid():

            reply = form.save(commit=False)
            reply.author = request.user
            reply.thread = thread
            try:
                reply.save()
            except Exception:
                log_error(
                    f"EVENT=DISCUSSION_REPLY_FAILED user={request.user.username} "
                    f'thread="{thread.title}"',
                    exc_info=True
                )
                raise

            log_event(
                f'EVENT=DISCUSSION_REPLY user={request.user.username} '
                f'thread="{thread.title}"'
            )

            if thread.author != request.user:

                send_notification(
                    thread.author,
                    "New Discussion Reply",
                    f"{request.user.username} replied to '{thread.title}'.",
                    "discussions"
                )

            return redirect(
                "thread_detail",
                thread_id=thread.id
            )
    else:
        form = DiscussionReplyForm()

    return render(
        request,
        "discussions/thread_detail.html",
        {
            "material": material,
            "course": course,
            "thread": thread,
            "replies": replies,
            "form": form,
            "is_enrolled": is_enrolled or request.user.is_staff,
        }
    )


@staff_member_required
def manage_discussions(request):
    threads = DiscussionThread.objects.select_related("material", "material__course", "author").all()
    return render(
        request,
        "instructor/manage_discussions.html",
        {
            "threads": threads
        }
    )


@staff_member_required
def delete_thread(request, thread_id):
    thread = get_object_or_404(DiscussionThread, id=thread_id)

    if request.method == "POST":
        thread.delete()
        return redirect("manage_discussions")

    return render(
        request,
        "instructor/delete_thread.html",
        {
            "thread": thread
        }
    )


@staff_member_required
def delete_reply(request, reply_id):
    reply = get_object_or_404(DiscussionReply, id=reply_id)
    thread = reply.thread

    if request.method == "POST":
        reply.delete()
        return redirect("thread_detail", thread_id=thread.id)

    return render(
        request,
        "instructor/delete_reply.html",
        {
            "reply": reply
        }
    )
