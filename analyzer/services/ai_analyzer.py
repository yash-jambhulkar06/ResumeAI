"""
AI Resume Analysis Service using Groq LLM.
Evaluates resumes on ATS parsability, impact metrics, domain detection, and generates
Google XYZ formula bullet point rewrites.
"""
import json
import os
from typing import Dict, Any
from groq import Groq


def analyze_resume_with_ai(resume_text: str) -> Dict[str, Any]:
    """Calls Groq API to analyze resume and returns a structured dictionary."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Resume analysis is temporarily unavailable. GROQ_API_KEY is not configured.")

    client = Groq(api_key=api_key)
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    prompt = f"""
You are an elite Fortune 500 tech recruiter and certified ATS resume specialist.

Analyze the following resume thoroughly based on modern hiring standards, ATS parsability, impact metrics, domain depth, and formatting.

RESUME CONTENT:
{resume_text}

Evaluate and return ONLY valid JSON with this exact schema:
{{
    "detected_role": "Primary role or specialization identified (e.g. Full Stack Developer, Data Engineer, Product Manager)",
    "seniority_level": "Entry-Level, Mid-Level, Senior, or Lead",
    "overall_score": 0,
    "ats_score": 0,
    "category_scores": {{
        "impact_metrics": 0,
        "ats_parsability": 0,
        "skills_depth": 0,
        "structure_brevity": 0
    }},
    "strengths": [
        "Concise strength 1 with specific reasoning",
        "Concise strength 2 with specific reasoning",
        "Concise strength 3 with specific reasoning"
    ],
    "weaknesses": [
        "Concise weakness 1 with root cause",
        "Concise weakness 2 with root cause",
        "Concise weakness 3 with root cause"
    ],
    "missing_skills": [
        "In-demand skill or framework 1 for this profile",
        "In-demand skill or framework 2 for this profile",
        "In-demand skill or framework 3 for this profile"
    ],
    "suggestions": [
        "Actionable recommendation 1",
        "Actionable recommendation 2",
        "Actionable recommendation 3"
    ],
    "bullet_rewrites": [
        {{
            "original": "An actual weak or unquantified bullet point found in this resume",
            "improved": "Accomplished [X] as measured by [Y] by doing [Z] rewrite with strong action verb and quantified outcome",
            "reason": "Why this rewrite is more effective"
        }},
        {{
            "original": "Another actual weak bullet point found in this resume",
            "improved": "Accomplished [X] as measured by [Y] by doing [Z] rewrite with strong action verb and quantified outcome",
            "reason": "Why this rewrite is more effective"
        }}
    ]
}}

Rules:
- All scores must be integers between 0 and 100.
- Extract actual bullets from the resume to rewrite into Google's XYZ formula ("Accomplished [X], measured by [Y], by doing [Z]"). If the resume has very few bullets, rewrite the most impactful responsibilities.
- Be objective and realistic; do not invent fictional companies or dates.
- Return RAW JSON only, without any markdown formatting, backticks, or intro text.
"""

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "You are a specialized ATS resume analyzer that outputs raw, valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=2048,
    )

    ai_text = response.choices[0].message.content.strip()
    if ai_text.startswith("```"):
        ai_text = ai_text.replace("```json", "").replace("```", "").strip()

    data = json.loads(ai_text)

    # Normalize defaults in case of subtle LLM omission
    data.setdefault("detected_role", "General Software Engineering")
    data.setdefault("seniority_level", "Mid-Level")
    data.setdefault("overall_score", 70)
    data.setdefault("ats_score", 70)
    data.setdefault("category_scores", {
        "impact_metrics": 65,
        "ats_parsability": 75,
        "skills_depth": 70,
        "structure_brevity": 70,
    })
    data.setdefault("strengths", [])
    data.setdefault("weaknesses", [])
    data.setdefault("missing_skills", [])
    data.setdefault("suggestions", [])
    data.setdefault("bullet_rewrites", [])

    return data
