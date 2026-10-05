from django.db import models
from django.contrib.auth.models import User


class ResumeAnalysis(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="resume_analyses"
    )

    resume_text = models.TextField()
    job_role = models.CharField(max_length=200, blank=True, default="General Profile")

    overall_score = models.PositiveIntegerField(default=0)
    ats_score = models.PositiveIntegerField(default=0)
    seniority_level = models.CharField(max_length=50, blank=True, default="Mid-Level")

    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    missing_skills = models.TextField(blank=True)
    suggestions = models.TextField(blank=True)

    details = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job_role} - {self.overall_score}/100"