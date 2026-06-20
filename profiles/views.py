from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserUpdateForm, ProfileUpdateForm
from .models import Profile, NotificationLog, UserAchievement
from progress.models import LessonProgress
from quizzes.models import QuizAttempt
from certificates.models import Certificate
from paths.models import CareerTrack


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=profile
        )
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your profile has been successfully updated!")
            return redirect("profile")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    # Fetch recent notification logs for this user
    notification_logs = NotificationLog.objects.filter(
        recipient=request.user
    ).order_by("-sent_at")[:10]

    # Gather timeline events
    events = []
    
    for lp in LessonProgress.objects.filter(student=request.user, completed=True).select_related('material').order_by('-completed_at')[:10]:
        events.append({
            'date': lp.completed_at,
            'title': f"Completed Lesson: {lp.material.title}",
            'icon': 'check-circle',
            'color': 'var(--success)'
        })
        
    for qa in QuizAttempt.objects.filter(student=request.user, passed=True).select_related('quiz').order_by('-attempted_at')[:10]:
        events.append({
            'date': qa.attempted_at,
            'title': f"Passed Quiz: {qa.quiz.title}",
            'icon': 'check-square',
            'color': 'var(--success)'
        })
        
    for ua in UserAchievement.objects.filter(user=request.user).select_related('achievement').order_by('-earned_at')[:10]:
        events.append({
            'date': ua.earned_at,
            'title': f"Earned Achievement: {ua.achievement.name}",
            'icon': ua.achievement.icon or 'award',
            'color': 'var(--accent-gold)' if ua.achievement.is_gold else 'var(--accent-primary)',
            'is_achievement': True
        })
        
    events.sort(key=lambda x: x['date'], reverse=True)
    timeline_events = events[:15]
    
    achievements = UserAchievement.objects.filter(user=request.user).select_related('achievement').order_by('-earned_at')
    
    certificates = Certificate.objects.filter(student=request.user).select_related('course').order_by('-issued_at')

    context = {
        "profile": profile,
        "u_form": u_form,
        "p_form": p_form,
        "notification_logs": notification_logs,
        "timeline_events": timeline_events,
        "achievements": achievements,
        "certificates": certificates,
    }

    return render(request, "profiles/profile.html", context)


@login_required
def onboarding_view(request):
    if request.method == 'POST':
        goal = request.POST.get('career_goal')
        exp = request.POST.get('experience_level')
        time = request.POST.get('time_commitment')
        deadline = request.POST.get('target_deadline')
        
        if goal:
            profile = request.user.profile
            profile.career_goal = goal
            profile.experience_level = exp
            profile.time_commitment = time
            profile.target_deadline = deadline
            profile.save()
            return redirect('dashboard')
            
    tracks = CareerTrack.objects.all()
    # Mock some defaults if DB is empty
    if not tracks.exists():
        tracks = [
            {"title": "Full Stack Developer"},
            {"title": "AI Engineer"},
            {"title": "Data Scientist"},
            {"title": "Cybersecurity Engineer"},
        ]
        
    return render(request, 'profiles/onboarding.html', {
        'tracks': tracks
    })

def public_portfolio(request, username):
    from accounts.models import User
    from projects.models import ProjectSubmission
    from certificates.models import Certificate
    from paths.models import UserPathProgress

    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)

    projects = ProjectSubmission.objects.filter(user=user, status__in=['SUBMITTED', 'FEATURED']).order_by('-featured', '-created_at')
    certificates = Certificate.objects.filter(student=user).select_related('course')
    path_progresses = UserPathProgress.objects.filter(user=user).select_related('learning_path')

    context = {
        'portfolio_user': user,
        'profile': profile,
        'projects': projects,
        'certificates': certificates,
        'path_progresses': path_progresses,
    }

    return render(request, 'profiles/portfolio.html', context)
