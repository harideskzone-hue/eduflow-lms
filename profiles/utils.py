from datetime import date, timedelta
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from .models import Achievement, UserAchievement

def award_xp(profile, amount):
    profile.xp += amount
    profile.level = (profile.xp // 100) + 1
    profile.save(update_fields=['xp', 'level'])

def record_activity(profile, minutes=0):
    today = date.today()
    
    if profile.last_activity_date != today:
        if profile.last_activity_date == today - timedelta(days=1):
            profile.streak_days += 1
        else:
            profile.streak_days = 1
            
        if profile.streak_days > profile.longest_streak:
            profile.longest_streak = profile.streak_days
            
        profile.last_activity_date = today

    if minutes > 0:
        profile.learning_minutes += minutes

    profile.save(update_fields=['streak_days', 'longest_streak', 'last_activity_date', 'learning_minutes'])

def award_achievement(user, achievement_name):
    try:
        achievement = Achievement.objects.get(name=achievement_name)
        UserAchievement.objects.get_or_create(user=user, achievement=achievement)
    except Achievement.DoesNotExist:
        pass

def send_lms_notification(user, subject, message):
    if user.email:
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@eduflow.com'),
            [user.email],
            fail_silently=True,
        )

from functools import wraps
from django.shortcuts import redirect

def onboarding_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_staff:
            if not getattr(request.user, 'profile', None) or not request.user.profile.career_goal:
                return redirect('onboarding')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
