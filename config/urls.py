"""
URL configuration for ResumeAI.
"""
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import path, include


def health_check(request):
    """Health check probe for load balancers and deployment platforms."""
    try:
        connection.cursor().execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "unavailable"

    status_code = 200 if db_status == "connected" else 503
    return JsonResponse({
        "status": "healthy" if status_code == 200 else "unhealthy",
        "database": db_status,
    }, status=status_code)


urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("", include("analyzer.urls")),
]
