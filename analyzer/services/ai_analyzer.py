"""
AI Resume Analysis Service using Groq LLM.
Evaluates resumes on ATS parsability, impact metrics, domain detection, and generates
Google XYZ formula bullet point rewrites.
"""
import json
import logging
import os
import re
from typing import Dict, Any
from groq import Groq, NotFoundError

logger = logging.getLogger(__name__)


def parse_json_safely(ai_text: str) -> Dict[str, Any]:
    """Resilient JSON parser handling markdown wrappers, trailing commas, and unclosed tokens."""
    cleaned = ai_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    # 1. Direct standard parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 2. Extract outermost JSON structure
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        extracted = match.group(1)
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            # Strip illegal trailing commas before brackets or braces
            sanitized = re.sub(r",\s*([\]}])", r"\1", extracted)
            try:
                return json.loads(sanitized)
            except json.JSONDecodeError:
                pass

    # 3. Handle potential mid-token truncation
    candidate = cleaned
    if candidate.endswith(","):
        candidate = candidate[:-1].strip()

    # Close unclosed quote if odd count
    quote_count = candidate.count('"') - candidate.count(r'\"')
    if quote_count % 2 != 0:
        candidate += '"'

    open_braces = max(0, candidate.count("{") - candidate.count("}"))
    open_brackets = max(0, candidate.count("[") - candidate.count("]"))
    candidate += ("]" * open_brackets) + ("}" * open_braces)
    candidate = re.sub(r",\s*([\]}])", r"\1", candidate)

    return json.loads(candidate)


def analyze_resume_with_ai(resume_text: str) -> Dict[str, Any]:
    """Calls Groq API to analyze resume and returns a structured dictionary."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Resume analysis is temporarily unavailable. GROQ_API_KEY is not configured.")

    client = Groq(api_key=api_key)
    configured_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    # Fallback list for maximum resilience across different Groq accounts and regions
    candidate_models = [
        configured_model,
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "llama-3.3-70b-versatile",
    ]
    seen = set()
    models_to_try = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

    prompt = f"""
You are an elite Fortune 500 tech recruiter and certified ATS resume specialist.

Analyze the following resume thoroughly based on modern hiring standards, ATS parsability, impact metrics, domain depth, and formatting.

RESUME CONTENT:
{resume_text}

Evaluate and return ONLY a valid JSON object matching this exact schema:
{{
    "detected_role": "Primary role or specialization identified (e.g. Full Stack Developer, Data Engineer, Product Manager)",
    "seniority_level": "Entry-Level, Mid-Level, Senior, or Lead",
    "overall_score": 75,
    "ats_score": 70,
    "category_scores": {{
        "impact_metrics": 65,
        "ats_parsability": 75,
        "skills_depth": 70,
        "structure_brevity": 70
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
- Extract actual bullets from the resume to rewrite into Google's XYZ formula ("Accomplished [X], measured by [Y], by doing [Z]").
- Keep each description concise and avoid inner double quotes inside string values.
- Ensure the JSON is completely formed and closed.
"""

    response = None
    last_error = None

    for model in models_to_try:
        try:
            logger.info("Attempting resume analysis with Groq model: %s", model)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional ATS resume analyzer that outputs raw, valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=4096,
            )
            break
        except NotFoundError as err:
            logger.warning("Groq model %s not found on this account/region. Falling back to next model.", model)
            last_error = err
            continue
        except Exception as err:
            # If response_format is not supported by a specific model, retry without it
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional ATS resume analyzer that outputs raw, valid JSON only.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=4096,
                )
                break
            except Exception as inner_err:
                logger.warning("Error calling Groq model %s: %s", model, inner_err)
                last_error = inner_err
                continue

    if response is None:
        raise ValueError(f"Failed to analyze resume with Groq. Last error: {last_error}")

    ai_text = response.choices[0].message.content.strip()

    try:
        data = parse_json_safely(ai_text)
    except Exception as exc:
        logger.error("JSON parsing error on AI output: %s\nRaw output: %s", exc, ai_text)
        raise ValueError("We encountered a formatting issue with the AI response. Please try again.") from exc

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
