from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache


def health_check(request):
    health = {
        "status": "healthy",
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "django": "healthy",
        },
    }

    # -------------------------
    # Database Health Check
    # -------------------------
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        health["status"] = "unhealthy"
        health["services"]["database"] = "unhealthy"

    # -------------------------
    # Redis Health Check
    # -------------------------
    try:
        cache.set("health_check", "ok", timeout=5)
        cache.get("health_check")
    except Exception:
        health["status"] = "unhealthy"
        health["services"]["redis"] = "unhealthy"

    # -------------------------
    # Return Status Code
    # -------------------------
    status_code = 200 if health["status"] == "healthy" else 503

    return JsonResponse(health, status=status_code)