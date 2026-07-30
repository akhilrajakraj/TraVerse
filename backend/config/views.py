from django.http import JsonResponse
from django.core.cache import cache
from django.utils.timezone import now


def system_info(request):
    cached_data = cache.get("system_info")

    if cached_data:
        return JsonResponse({
            "source": "Redis Cache",
            "data": cached_data,
        })

    data = {
        "message": "DockForge Redis is working!",
        "generated_at": now().isoformat(),
    }

    cache.set("system_info", data, timeout=60)

    return JsonResponse({
        "source": "Fresh Response",
        "data": data,
    })