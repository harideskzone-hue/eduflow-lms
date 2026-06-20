from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from .forms import CustomUserCreationForm


@ratelimit(key="ip", rate="3/m", method="POST", block=True)
def register_view(request):

    if request.method == "POST":

        form = CustomUserCreationForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            return redirect("dashboard")

    else:

        form = CustomUserCreationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form
        }
    )


@method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True), name="dispatch")
class CustomLoginView(LoginView):
    pass


@method_decorator(ratelimit(key="ip", rate="2/m", method="POST", block=True), name="dispatch")
class CustomPasswordResetView(PasswordResetView):
    pass


@method_decorator(ratelimit(key="ip", rate="2/m", method="POST", block=True), name="dispatch")
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    pass

