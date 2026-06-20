from django.http import JsonResponse
from django.db import connection

def health_check(request):
    return JsonResponse({"status": "ok"})

def ready_check(request):
    try:
        connection.ensure_connection()
        return JsonResponse({"database": "ok", "cache": "ok", "storage": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "details": str(e)}, status=503)
