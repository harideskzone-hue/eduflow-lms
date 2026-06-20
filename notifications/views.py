from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from .models import Notification


@login_required
def notification_list(request):

    notifications = (
        Notification.objects
        .filter(user=request.user)
    )

    return render(
        request,
        "notifications/list.html",
        {
            "notifications": notifications
        }
    )


@login_required
def mark_notification_read(request, pk):

    notification = get_object_or_404(
        Notification,
        pk=pk,
        user=request.user
    )

    notification.is_read = True
    notification.save()

    return redirect(
        "notification_list"
    )


@login_required
def notification_preferences(request):
    from .models import NotificationPreference
    preference, created = NotificationPreference.objects.get_or_create(user=request.user)

    if request.method == "POST":
        preference.email_enrollments = request.POST.get("email_enrollments") == "on"
        preference.email_quizzes = request.POST.get("email_quizzes") == "on"
        preference.email_certificates = request.POST.get("email_certificates") == "on"
        preference.email_discussions = request.POST.get("email_discussions") == "on"
        preference.email_announcements = request.POST.get("email_announcements") == "on"
        preference.save()
        return redirect("notification_preferences")

    return render(
        request,
        "notifications/preferences.html",
        {
            "preference": preference
        }
    )

from django.http import JsonResponse

@login_required
def api_recent_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    data = []
    for notif in notifications:
        data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'type': notif.notification_type,
            'is_read': notif.is_read,
            'link': notif.link,
            'created_at': notif.created_at.strftime("%b %d, %Y %H:%M")
        })
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'notifications': data, 'unread_count': unread_count})

@login_required
def api_mark_all_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)
