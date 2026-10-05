"""
Views for ResumeAI analyzer.
Orchestrates text extraction, deterministic ATS auditing, AI analysis, and rendering.
"""
import logging
from django.contrib.auth.models import User
from django.shortcuts import render

from .models import ResumeAnalysis
from .services.extractor import extract_resume_text
from .services.ats_auditor import run_ats_audit
from .services.ai_analyzer import analyze_resume_with_ai

logger = logging.getLogger(__name__)


def home(request):
    """Handles home page display and resume processing."""
    if request.method != "POST":
        return render(request, "analyzer/home.html")

    resume_text = request.POST.get("resume_text", "").strip()
    resume_file = request.FILES.get("resume_file")
    form_context = {"resume_text": resume_text}

    if resume_file:
        try:
            resume_text = extract_resume_text(resume_file)
            form_context["resume_text"] = resume_text
        except ValueError as exc:
            return render(request, "analyzer/home.html", {
                **form_context,
                "error": str(exc),
            })

    if not resume_text:
        return render(request, "analyzer/home.html", {
            **form_context,
            "error": "Please upload a readable resume or paste your resume text.",
        })

    try:
        # 1. Deterministic ATS audits (links, emails, headers, length, metrics)
        ats_checks = run_ats_audit(resume_text)

        # 2. Advanced LLM analysis (domain detection, category scoring, Google XYZ rewrites)
        analysis = analyze_resume_with_ai(resume_text)

        detected_role = analysis.get("detected_role", "General Software Engineering")
        seniority_level = analysis.get("seniority_level", "Mid-Level")
        category_scores = analysis.get("category_scores", {})
        bullet_rewrites = analysis.get("bullet_rewrites", [])

        # 3. Optional persistence
        user = User.objects.first()
        if user:
            ResumeAnalysis.objects.create(
                user=user,
                resume_text=resume_text,
                job_role=detected_role,
                seniority_level=seniority_level,
                overall_score=analysis.get("overall_score", 0),
                ats_score=analysis.get("ats_score", 0),
                strengths="\n".join(analysis.get("strengths", [])),
                weaknesses="\n".join(analysis.get("weaknesses", [])),
                missing_skills="\n".join(analysis.get("missing_skills", [])),
                suggestions="\n".join(analysis.get("suggestions", [])),
                details={
                    "category_scores": category_scores,
                    "bullet_rewrites": bullet_rewrites,
                    "ats_checks": ats_checks,
                },
            )

        return render(request, "analyzer/result.html", {
            "analysis": analysis,
            "detected_role": detected_role,
            "seniority_level": seniority_level,
            "job_role": detected_role,
            "category_scores": category_scores,
            "bullet_rewrites": bullet_rewrites,
            "ats_checks": ats_checks,
        })
    except ValueError as exc:
        logger.warning("Configuration or validation error during analysis: %s", exc)
        return render(request, "analyzer/home.html", {
            **form_context,
            "error": str(exc),
        })
    except Exception as exc:
        logger.exception("Unexpected error during resume analysis: %s", exc)
        return render(request, "analyzer/home.html", {
            **form_context,
            "error": "We encountered an issue analyzing your resume. Please try again in a moment.",
        })
