"""
ai_rewriter.py — AI-powered resume rewrite suggestions via Anthropic API.

Uses the user's own Anthropic API key (entered in the app).
Calls claude-haiku-4-5 for fast, affordable suggestions.

Security:
  - API key format is validated before any network call.
  - API key is never echoed in error messages or logs.
  - Resume and JD text are hard-truncated before being sent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import security as _sec


@dataclass
class RewriteSuggestion:
    criterion_name: str
    icon: str
    current_score: int
    suggestion_title: str
    improved_bullets: list[str]       # 2-4 rewritten bullet point examples
    explanation: str                   # short "why this works" note
    error: Optional[str] = None       # set if API call failed


_SYSTEM_PROMPT = """You are an expert resume writer and ATS optimization specialist.
You give concise, specific, actionable suggestions to improve a resume for ATS systems.
Your rewrites are professional, quantified where possible, and use strong action verbs.
Always respond in valid JSON — no markdown fences, no extra commentary."""


def _criterion_prompt(
    criterion_name: str,
    criterion_feedback: str,
    criterion_fix: str,
    resume_text: str,
    jd_text: str,
) -> str:
    jd_section = (
        f"\n\nJOB DESCRIPTION:\n{jd_text[:2000]}"
        if jd_text and jd_text.strip()
        else "\n\n(No job description provided — give general ATS advice.)"
    )
    return f"""CRITERION: {criterion_name}
CURRENT FEEDBACK: {criterion_feedback}
SUGGESTED FIX: {criterion_fix}

RESUME TEXT (first 3000 chars):
{resume_text[:3000]}{jd_section}

Return a JSON object with exactly these keys:
{{
  "suggestion_title": "<8-12 word headline for what needs to change>",
  "improved_bullets": [
    "<rewritten bullet 1 — starts with action verb, ideally quantified>",
    "<rewritten bullet 2>",
    "<rewritten bullet 3>"
  ],
  "explanation": "<2-3 sentences on why these changes improve ATS score>"
}}"""


def get_rewrite_suggestion(
    api_key: str,
    criterion_name: str,
    criterion_icon: str,
    criterion_score: int,
    criterion_feedback: str,
    criterion_fix: str,
    resume_text: str,
    jd_text: str,
) -> RewriteSuggestion:
    """
    Call Claude Haiku to get rewrite suggestions for one weak criterion.
    Returns a RewriteSuggestion (with error set if API call fails).
    API key is validated before any network call; never logged.
    """
    # --- API key format check (never echo the key in errors) ---
    try:
        _sec.validate_api_key_format(api_key)
    except _sec.SecurityError as exc:
        return RewriteSuggestion(
            criterion_name=criterion_name,
            icon=criterion_icon,
            current_score=criterion_score,
            suggestion_title="Invalid API key",
            improved_bullets=[],
            explanation="",
            error=str(exc),
        )

    try:
        import anthropic
    except ImportError:
        return RewriteSuggestion(
            criterion_name=criterion_name,
            icon=criterion_icon,
            current_score=criterion_score,
            suggestion_title="Install anthropic SDK",
            improved_bullets=[],
            explanation="",
            error="The `anthropic` package is not installed. Run: pip install anthropic",
        )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=600,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": _criterion_prompt(
                        criterion_name,
                        criterion_feedback,
                        criterion_fix,
                        resume_text,
                        jd_text,
                    ),
                }
            ],
        )
        raw = message.content[0].text.strip()

        # Strip markdown fences if model wrapped it anyway
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        import json
        data = json.loads(raw)

        return RewriteSuggestion(
            criterion_name=criterion_name,
            icon=criterion_icon,
            current_score=criterion_score,
            suggestion_title=data.get("suggestion_title", "Suggested improvements"),
            improved_bullets=data.get("improved_bullets", [])[:4],
            explanation=data.get("explanation", ""),
        )

    except anthropic.AuthenticationError:
        return RewriteSuggestion(
            criterion_name=criterion_name,
            icon=criterion_icon,
            current_score=criterion_score,
            suggestion_title="Invalid API key",
            improved_bullets=[],
            explanation="",
            error="Invalid Anthropic API key. Check your key at console.anthropic.com.",
        )
    except anthropic.RateLimitError:
        return RewriteSuggestion(
            criterion_name=criterion_name,
            icon=criterion_icon,
            current_score=criterion_score,
            suggestion_title="Rate limit hit",
            improved_bullets=[],
            explanation="",
            error="Anthropic rate limit reached. Wait a moment and try again.",
        )
    except Exception as exc:
        # Sanitize error — never include the raw exception which may contain the API key
        err_type = type(exc).__name__
        return RewriteSuggestion(
            criterion_name=criterion_name,
            icon=criterion_icon,
            current_score=criterion_score,
            suggestion_title="API error",
            improved_bullets=[],
            explanation="",
            error=f"Unexpected error ({err_type}). Check your API key and try again.",
        )


def get_all_suggestions(
    api_key: str,
    criteria: list,
    resume_text: str,
    jd_text: str,
    min_score_threshold: int = 7,
) -> list[RewriteSuggestion]:
    """
    Get AI suggestions for all criteria scoring below min_score_threshold.
    Criteria are sorted worst-first.
    """
    weak = [c for c in criteria if c.score < min_score_threshold]
    weak.sort(key=lambda c: c.score)

    suggestions = []
    for c in weak:
        s = get_rewrite_suggestion(
            api_key=api_key,
            criterion_name=c.name,
            criterion_icon=c.icon,
            criterion_score=c.score,
            criterion_feedback=c.feedback,
            criterion_fix=c.fix,
            resume_text=resume_text,
            jd_text=jd_text,
        )
        suggestions.append(s)
        # Stop early if we hit an auth error (same key for all calls)
        if s.error and ("Invalid" in (s.error or "") or "not installed" in (s.error or "")):
            break

    return suggestions
