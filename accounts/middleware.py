from django_ratelimit.exceptions import Ratelimited
from django.shortcuts import render
from monitoring.utils import log_audit, AuditActions, get_client_ip


class RatelimitMiddleware:
    """
    Middleware to catch django-ratelimit Ratelimited exceptions,
    log the rate limit event to the compliance audit logs, and
    render a custom glassmorphic 429.html error page.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, Ratelimited):
            client_ip = get_client_ip(request)
            user = request.user if request.user.is_authenticated else None
            log_audit(
                user=user,
                action=AuditActions.RATE_LIMIT_TRIGGERED,
                details=f"Rate limit triggered for IP={client_ip} on path={request.path}",
                ip_address=client_ip
            )
            return render(request, "errors/ratelimited.html", status=429)


class SecurityHeadersMiddleware:
    """
    Middleware to inject custom security headers like Permissions-Policy on all HTTP responses.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        return response
