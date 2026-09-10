import json
import os
from pathlib import Path

from django.contrib.auth.models import User
from django.shortcuts import render
from docx import Document
from groq import Groq
from PIL import Image
from pypdf import PdfReader
import pytesseract

from .models import ResumeAnalysis

MAX_UPLOAD_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png"}
UPLOAD_ERROR = (
    "We couldn't read this resume. Please upload a valid PDF, DOCX, TXT, "
    "JPG or PNG file."
)


def extract_pdf_text(file):
    """Extract text from a PDF file."""
    reader = PdfReader(file)
    text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)
    return "\n".join(text).strip()


def extract_docx_text(file):
    """Extract text from a DOCX file."""
    document = Document(file)
    return "\n".join(
        paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()
    ).strip()


def extract_txt_text(file):
    """Extract text from a TXT file with tolerant UTF-8 decoding."""
    return file.read().decode("utf-8", errors="ignore").strip()


def extract_image_text(file):
    """Extract text from an image using Pillow and Tesseract OCR."""
    tesseract_cmd = os.getenv("TESSERACT_CMD")
    if not tesseract_cmd and os.name == "nt":
        default_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        if default_path.exists():
            tesseract_cmd = str(default_path)
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    try:
        with Image.open(file) as image:
            return pytesseract.image_to_string(image).strip()
    except Exception as exc:
        raise ValueError(UPLOAD_ERROR) from exc


def extract_resume_text(file):
    """Validate an uploaded resume and extract its text in memory."""
    extension = Path(file.name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Unsupported file type. Please upload PDF, DOCX, TXT, JPG or PNG."
        )
    if file.size > MAX_UPLOAD_SIZE:
        raise ValueError("File is too large. Please upload a file under 5 MB.")
    if file.size == 0:
        raise ValueError("This file is empty. Please upload a readable resume.")

    try:
        file.seek(0)
        if extension == ".pdf":
            text = extract_pdf_text(file)
        elif extension == ".docx":
            text = extract_docx_text(file)
        elif extension == ".txt":
            text = extract_txt_text(file)
        else:
            text = extract_image_text(file)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(UPLOAD_ERROR) from exc

    if not text:
        raise ValueError("We couldn't find any readable text in this resume.")
    return text


def home(request):
    if request.method != "POST":
        return render(request, "analyzer/home.html")

    job_role = request.POST.get("job_role", "").strip()
    resume_text = request.POST.get("resume_text", "").strip()
    resume_file = request.FILES.get("resume_file")
    form_context = {"job_role": job_role, "resume_text": resume_text}

    if not job_role:
        return render(request, "analyzer/home.html", {
            **form_context,
            "error": "Please enter your target job role.",
        })

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

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return render(request, "analyzer/home.html", {
            **form_context,
            "error": "Resume analysis is temporarily unavailable. Please try again later.",
        })

    try:
        client = Groq(api_key=api_key)
        prompt = f"""
You are an expert ATS resume reviewer and professional career coach.

Analyze the following resume for the target job role.

TARGET JOB ROLE:
{job_role}

RESUME:
{resume_text}

Evaluate:
1. Overall resume quality
2. ATS compatibility
3. Relevance to the target job
4. Technical skills
5. Projects and experience
6. Missing skills
7. Resume weaknesses
8. Practical improvements

Return ONLY valid JSON using exactly this structure:
{{
    "overall_score": 0,
    "ats_score": 0,
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "weaknesses": ["weakness 1", "weakness 2", "weakness 3"],
    "missing_skills": ["skill 1", "skill 2", "skill 3"],
    "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}}

Rules:
- Scores must be between 0 and 100.
- Be realistic and do not invent experience or skills.
- Suggestions should be practical and missing skills relevant to the target job.
- Keep each item concise and return JSON only.
"""
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional ATS resume analyzer. Return only valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1500,
        )
        ai_text = response.choices[0].message.content.strip()
        if ai_text.startswith("```"):
            ai_text = ai_text.replace("```json", "").replace("```", "").strip()
        analysis = json.loads(ai_text)

        required_fields = [
            "overall_score", "ats_score", "strengths", "weaknesses",
            "missing_skills", "suggestions",
        ]
        for field in required_fields:
            if field not in analysis:
                raise ValueError(f"AI response missing field: {field}")

        user = User.objects.first()
        if user:
            ResumeAnalysis.objects.create(
                user=user,
                resume_text=resume_text,
                job_role=job_role,
                overall_score=analysis["overall_score"],
                ats_score=analysis["ats_score"],
                strengths="\n".join(analysis["strengths"]),
                weaknesses="\n".join(analysis["weaknesses"]),
                missing_skills="\n".join(analysis["missing_skills"]),
                suggestions="\n".join(analysis["suggestions"]),
            )
        return render(request, "analyzer/result.html", {
            "job_role": job_role,
            "analysis": analysis,
        })
    except json.JSONDecodeError:
        return render(request, "analyzer/home.html", {
            **form_context,
            "error": "AI returned an invalid response. Please try again.",
        })
    except Exception as exc:
        print("\n========== ERROR ==========")
        print(type(exc).__name__)
        print(str(exc))
        print("============================\n")
        return render(request, "analyzer/home.html", {
            **form_context,
            "error": "We couldn't complete the analysis. Please try again.",
        })
