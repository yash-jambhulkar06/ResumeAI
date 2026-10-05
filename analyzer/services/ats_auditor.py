"""
Deterministic ATS parser and audit engine.
Inspects resume text for contact info, links, standard sections, metrics, and length.
"""
import re
from typing import List, Dict, Any


EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}")
LINKEDIN_PATTERN = re.compile(r"linkedin\.com/(?:in/)?[\w-]+", re.IGNORECASE)
GITHUB_PATTERN = re.compile(r"github\.com/[\w-]+", re.IGNORECASE)
METRIC_PATTERN = re.compile(r"\b\d+(?:\.\d+)?%|\$\d+(?:,\d+)*(?:\.\d+)?|\b\d+(?:\.\d+)?(?:k|m|x)\b|\b\d{2,}\b", re.IGNORECASE)

STANDARD_SECTIONS = [
    ("Experience / Work History", [r"\bexperience\b", r"\bwork history\b", r"\bemployment\b"]),
    ("Education", [r"\beducation\b", r"\bacademics\b", r"\bqualifications\b"]),
    ("Skills", [r"\bskills\b", r"\btechnologies\b", r"\bcompetencies\b", r"\btechnical skills\b"]),
    ("Projects", [r"\bprojects\b", r"\bkey projects\b", r"\bportfolio\b"]),
]


def run_ats_audit(text: str) -> List[Dict[str, Any]]:
    """Runs a series of deterministic checks against the resume text."""
    checks = []

    # 1. Contact Information
    has_email = bool(EMAIL_PATTERN.search(text))
    has_phone = bool(PHONE_PATTERN.search(text))

    if has_email and has_phone:
        checks.append({
            "label": "Contact Information",
            "status": "pass",
            "detail": "Email and phone number detected for recruiter outreach."
        })
    elif has_email or has_phone:
        checks.append({
            "label": "Contact Information",
            "status": "warn",
            "detail": "Only partial contact information detected (make sure both email and phone are present)."
        })
    else:
        checks.append({
            "label": "Contact Information",
            "status": "fail",
            "detail": "No direct email or phone number detected. ATS scanners may discard your resume."
        })

    # 2. Online Presence (LinkedIn / GitHub)
    has_linkedin = bool(LINKEDIN_PATTERN.search(text))
    has_github = bool(GITHUB_PATTERN.search(text))

    if has_linkedin or has_github:
        profiles = []
        if has_linkedin:
            profiles.append("LinkedIn")
        if has_github:
            profiles.append("GitHub")
        checks.append({
            "label": "Professional Links",
            "status": "pass",
            "detail": f"Detected active links: {', '.join(profiles)}."
        })
    else:
        checks.append({
            "label": "Professional Links",
            "status": "warn",
            "detail": "No LinkedIn or GitHub URL detected. Recruiters prefer verified profiles."
        })

    # 3. Standard ATS Section Headers
    found_sections = []
    missing_sections = []
    text_lower = text.lower()

    for section_name, patterns in STANDARD_SECTIONS:
        if any(re.search(pat, text_lower) for pat in patterns):
            found_sections.append(section_name)
        else:
            missing_sections.append(section_name)

    if not missing_sections:
        checks.append({
            "label": "Standard Section Headers",
            "status": "pass",
            "detail": "All key sections (Experience, Education, Skills, Projects) clearly labeled."
        })
    elif len(missing_sections) <= 1:
        checks.append({
            "label": "Standard Section Headers",
            "status": "warn",
            "detail": f"Consider adding standard header for: {', '.join(missing_sections)}."
        })
    else:
        checks.append({
            "label": "Standard Section Headers",
            "status": "fail",
            "detail": f"Missing critical ATS headers: {', '.join(missing_sections)}. Legacy ATS may misclassify your data."
        })

    # 4. Quantifiable Impact & Metrics
    metrics_count = len(METRIC_PATTERN.findall(text))
    if metrics_count >= 5:
        checks.append({
            "label": "Quantifiable Achievements",
            "status": "pass",
            "detail": f"Strong usage of numbers and measurable impact ({metrics_count}+ metrics found)."
        })
    elif metrics_count >= 2:
        checks.append({
            "label": "Quantifiable Achievements",
            "status": "warn",
            "detail": f"Only {metrics_count} metrics detected. Add more %, $, or team size statistics to showcase impact."
        })
    else:
        checks.append({
            "label": "Quantifiable Achievements",
            "status": "fail",
            "detail": "Few or no quantifiable metrics detected. Use numbers to prove your achievements."
        })

    # 5. Length & Word Count Check
    words = text.split()
    word_count = len(words)
    if 350 <= word_count <= 950:
        checks.append({
            "label": "Optimal Length",
            "status": "pass",
            "detail": f"Great resume length ({word_count} words), ideal for standard 1–2 page scans."
        })
    elif word_count < 350:
        checks.append({
            "label": "Optimal Length",
            "status": "warn",
            "detail": f"Resume is brief ({word_count} words). Expand on responsibilities, tooling, and projects."
        })
    else:
        checks.append({
            "label": "Optimal Length",
            "status": "warn",
            "detail": f"Resume is relatively lengthy ({word_count} words). Keep bullets concise to prevent recruiter fatigue."
        })

    return checks
