from django.contrib import admin
from .models import ResumeAnalysis


@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "job_role",
        "overall_score",
        "ats_score",
        "created_at",
    )

    list_filter = ("job_role", "created_at")
    search_fields = ("user__username", "job_role")