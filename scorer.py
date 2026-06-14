"""
scorer.py - ATS scoring engine with 10 independent scoring functions.

Each function receives the ParseResult (and optionally a job description string)
and returns a CriterionResult dataclass:
    score   : int  (0-10)
    status  : str  "pass" | "warn" | "fail"
    feedback: str  human-readable explanation
    details : dict (extra structured data for the UI)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from keywords import (
    ACTION_VERBS,
    GERUND_VERBS,
    WEAK_PHRASES,
    SECTION_HEADINGS,
    REQUIRED_SECTIONS,
    RECOMMENDED_SECTIONS,
    HARD_SKILLS_KEYWORDS,
    SOFT_SKILLS_ONLY_INDICATORS,
    DATE_PATTERNS,
    QUANTIFICATION_PATTERNS,
    UNICODE_BULLETS,
    SHORT_TECH_TERMS,
    KEYWORD_SYNONYMS,
)

if TYPE_CHECKING:
    from parser import ParseResult


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class CriterionResult:
    name: str
    icon: str
    score: int
    status: str
    feedback: str
    fix: str
    details: dict = field(default_factory=dict)


def _status(score: int) -> str:
    if score >= 8:
        return "pass"
    if score >= 5:
        return "warn"
    return "fail"


# ---------------------------------------------------------------------------
# 1. Contact Information
# ---------------------------------------------------------------------------

def score_contact_info(result):
    text = result.full_text
    fields_found = {}

    email_re = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    fields_found["email"] = bool(email_re.search(text))

    phone_re = re.compile(r"(\+?\d[\d\s\-\.\(\)]{7,}\d)")
    fields_found["phone"] = bool(phone_re.search(text))

    linkedin_re = re.compile(r"linkedin\.com/in/", re.IGNORECASE)
    fields_found["linkedin"] = bool(linkedin_re.search(text))

    location_re = re.compile(
        r"\b([A-Z][a-z]+,?\s+[A-Z]{2})\b|"
        r"\b(New York|Los Angeles|San Francisco|Chicago|London|Remote|Hybrid)\b",
        re.IGNORECASE,
    )
    fields_found["location"] = bool(location_re.search(text))

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    name_found = False
    if lines:
        first = lines[0]
        if 2 <= len(first.split()) <= 5 and re.match(r"^[A-Za-z\s\.\-]+$", first):
            name_found = True
    fields_found["name"] = name_found

    missing = [k for k, v in fields_found.items() if not v]
    score = max(0, 10 - len(missing) * 2)

    if not missing:
        feedback = "All key contact fields detected: name, email, phone, location, and LinkedIn."
        fix = "Nothing to fix - contact section looks complete."
    else:
        feedback = (
            f"Missing contact fields: {', '.join(missing)}. "
            "ATS systems rely on structured contact data to auto-populate applicant profiles."
        )
        fix = (
            f"Add the following to the top of your resume: {', '.join(missing)}. "
            "Place each on its own line. For LinkedIn, use the format: "
            "linkedin.com/in/your-profile-name"
        )

    return CriterionResult(
        name="Contact Information",
        icon="\U0001f464",
        score=score,
        status=_status(score),
        feedback=feedback,
        fix=fix,
        details={"fields": fields_found, "missing": missing},
    )


# ---------------------------------------------------------------------------
# 2. Standard Section Headings
# ---------------------------------------------------------------------------

def score_section_headings(result):
    sections_found = set(result.sections.keys())
    missing_required = [s for s in REQUIRED_SECTIONS if s not in sections_found]
    missing_recommended = [s for s in RECOMMENDED_SECTIONS if s not in sections_found]

    score = 10 - len(missing_required) * 3 - len(missing_recommended) * 1
    score = max(0, min(10, score))

    extra_sections = [
        s for s in sections_found
        if s not in REQUIRED_SECTIONS + RECOMMENDED_SECTIONS + ["header", "certifications", "projects"]
    ]

    if not missing_required and not missing_recommended:
        feedback = f"All standard sections detected: {', '.join(sorted(sections_found - {'header'}))}."
        fix = "Nothing to fix - all expected sections are present."
    else:
        parts = []
        if missing_required:
            parts.append(f"Missing required sections: {', '.join(missing_required)}")
        if missing_recommended:
            parts.append(f"Missing recommended sections: {', '.join(missing_recommended)}")
        feedback = ". ".join(parts) + ". ATS systems scan for these exact headings."
        fix = (
            "Add the missing sections with standard headings. Use: "
            "'Work Experience', 'Education', 'Skills', 'Professional Summary'. "
            "Avoid creative names like 'My Journey' - they confuse ATS parsers."
        )

    return CriterionResult(
        name="Standard Section Headings",
        icon="\U0001f4cb",
        score=score,
        status=_status(score),
        feedback=feedback,
        fix=fix,
        details={
            "found": list(sections_found - {"header"}),
            "missing_required": missing_required,
            "missing_recommended": missing_recommended,
            "unrecognized": extra_sections,
        },
    )


# ---------------------------------------------------------------------------
# 3. Tense Consistency
# ---------------------------------------------------------------------------

_PAST_TENSE_RE = re.compile(
    r"^(led|managed|built|developed|designed|created|improved|increased|"
    r"reduced|delivered|launched|implemented|deployed|achieved|completed|"
    r"analyzed|executed|drove|generated|saved|resolved|coordinated|"
    r"trained|wrote|coded|authored|architected|optimized|streamlined|"
    r"established|founded|engineered|secured|won|maintained|supervised|"
    r"oversaw|directed|headed|spearheaded|championed|orchestrated|"
    r"facilitated|administered|mentored|coached|guided|partnered|"
    r"presented|communicated|negotiated|liaised|consulted|advised|"
    r"onboarded|validated|reviewed|benchmarked|researched|evaluated|"
    r"assessed|audited|identified|diagnosed|measured|tracked|monitored|"
    r"tested|automated|modernized|refactored|restructured|transformed|"
    r"upgraded|revamped|scaled|accelerated|enhanced|collaborated)$",
    re.IGNORECASE,
)

_PRESENT_TENSE_RE = re.compile(
    r"^(lead|manage|build|develop|design|create|improve|increase|"
    r"reduce|deliver|launch|implement|deploy|achieve|complete|"
    r"analyze|execute|drive|generate|save|resolve|coordinate|"
    r"train|write|code|author|architect|optimize|streamline|"
    r"establish|engineer|secure|maintain|supervise|"
    r"oversee|direct|spearhead|champion|orchestrate|"
    r"facilitate|administer|mentor|coach|guide|partner|"
    r"communicate|negotiate|liaise|consult|advise|"
    r"onboard|validate|benchmark|research|evaluate|"
    r"assess|audit|identify|diagnose|measure|track|monitor|"
    r"automate|modernize|refactor|restructure|transform|"
    r"upgrade|revamp|accelerate|enhance|collaborate)$",
    re.IGNORECASE,
)

_BULLET_STRIP_RE = re.compile(r"^[•\-\*▪▸➤✔–—]\s*")


def score_tense_consistency(result):
    experience_text = result.sections.get("experience", "")
    if not experience_text:
        return CriterionResult(
            name="Tense Consistency",
            icon="⏱️",
            score=5,
            status="warn",
            feedback="No experience section detected - tense check skipped.",
            fix="Add a Work Experience section with bullet-pointed achievements.",
            details={},
        )

    past_count = 0
    present_count = 0

    for line in experience_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        cleaned = _BULLET_STRIP_RE.sub("", stripped).strip()
        if not cleaned:
            continue
        first_word = cleaned.split()[0].rstrip(".,;:") if cleaned.split() else ""
        if _PAST_TENSE_RE.match(first_word):
            past_count += 1
        elif _PRESENT_TENSE_RE.match(first_word):
            present_count += 1

    total = past_count + present_count

    if total == 0:
        score = 5
        feedback = "Could not detect clear action verbs in experience section to evaluate tense."
        fix = "Start each bullet with a strong past-tense action verb (e.g. 'Built', 'Managed', 'Designed')."
    elif present_count == 0 or (present_count / total) <= 0.15:
        score = 10
        feedback = f"Good tense consistency - {past_count} past-tense bullets detected."
        fix = "Tense is consistent. No action needed."
    elif (present_count / total) <= 0.30:
        score = 7
        feedback = (
            f"{present_count} present-tense verbs found alongside {past_count} past-tense verbs. "
            "Minor inconsistency - acceptable only if these are current-role bullets."
        )
        fix = (
            "Review bullets using present tense. If describing a past role, convert to past tense "
            "(e.g. 'Manage -> Managed', 'Lead -> Led')."
        )
    else:
        score = 4
        feedback = (
            f"Significant tense mixing: {present_count} present-tense vs {past_count} past-tense verbs. "
            "ATS systems and recruiters expect consistent past tense for completed roles."
        )
        fix = (
            f"Convert {present_count} present-tense verbs to past tense. "
            "Only your current role's bullets may use present tense. "
            "Example: 'Develop -> Developed', 'Lead -> Led', 'Build -> Built'."
        )

    return CriterionResult(
        name="Tense Consistency",
        icon="⏱️",
        score=score,
        status=_status(score),
        feedback=feedback,
        fix=fix,
        details={"past_count": past_count, "present_count": present_count, "total": total},
    )


# ---------------------------------------------------------------------------
# 4. Bullet Point Structure
# ---------------------------------------------------------------------------

def score_bullet_structure(result):
    from parser import extract_all_bullets

    bullets = extract_all_bullets(result.sections)
    if not bullets:
        return CriterionResult(
            name="Bullet Point Structure",
            icon="\U0001f539",
            score=5,
            status="warn",
            feedback="No bullet points detected in experience/projects sections.",
            fix="Use bullet points starting with strong action verbs for every job achievement.",
            details={},
        )

    weak_re = re.compile("|".join(WEAK_PHRASES), re.IGNORECASE)
    strong = []    # past-tense action verb — best
    gerund = []    # present-participle (-ing) — acceptable
    no_verb = []   # no recognized opening — neutral
    weak = []      # explicit weak phrase — red flag

    for b in bullets:
        words = b.split()
        if not words:
            continue
        first = words[0].lower().rstrip(".,;:")
        if weak_re.match(b.lower()):
            weak.append(b)
        elif first in ACTION_VERBS:
            strong.append(b)
        elif first in GERUND_VERBS or (first.endswith("ing") and len(first) > 5):
            gerund.append(b)
        else:
            no_verb.append(b)

    total = len(bullets)
    # Weighted score: strong=full credit, gerund=70%, no_verb=30%, weak=0%
    weighted = len(strong) * 1.0 + len(gerund) * 0.7 + len(no_verb) * 0.3
    score = round((weighted / total) * 10) if total else 0
    score = max(0, min(10, score))

    bad_count = len(weak) + len(no_verb)
    problem_bullets = (weak + no_verb)[:3]  # up to 3 examples for the UI

    if score >= 9:
        feedback = f"All {total} bullets use strong action verb openings. Excellent structure."
        fix = "Bullet structure is excellent. Keep using past-tense action verbs."
    elif score >= 7:
        feedback = (
            f"{len(strong)} of {total} bullets start with strong action verbs; "
            f"{len(gerund)} use present-participle (-ing) form."
        )
        fix = (
            "Convert -ing openings to past tense for stronger ATS impact. "
            "Example: 'Leading a team' → 'Led a team of 8 engineers'."
        )
    elif score >= 5:
        feedback = (
            f"{bad_count} of {total} bullets have weak or unrecognized openings "
            f"({len(weak)} weak phrases, {len(no_verb)} without a recognized verb)."
        )
        fix = (
            f"Rewrite {bad_count} bullets to open with action verbs like "
            "'Built', 'Led', 'Reduced', 'Automated'. "
            "Avoid 'Responsible for', 'Worked on', 'Helped with'."
        )
    else:
        feedback = (
            f"Most bullets ({bad_count}/{total}) lack strong action verb openings. "
            f"{len(weak)} use weak phrases; {len(no_verb)} have no recognizable verb."
        )
        fix = (
            "Rewrite bullets to start with a past-tense action verb and include a result. "
            "Pattern: [Verb] + [What] + [Impact]. "
            "Example: 'Reduced API latency by 40% by caching hot queries in Redis.'"
        )

    return CriterionResult(
        name="Bullet Point Structure",
        icon="\U0001f539",
        score=score,
        status=_status(score),
        feedback=feedback,
        fix=fix,
        details={
            "total_bullets": total,
            "strong_verb": len(strong),
            "gerund_verb": len(gerund),
            "no_verb": len(no_verb),
            "weak_phrases": len(weak),
            "problem_examples": problem_bullets,
        },
    )


# ---------------------------------------------------------------------------
# 5. Quantified Achievements
# ---------------------------------------------------------------------------

def score_quantified_results(result):
    from parser import extract_all_bullets

    bullets = extract_all_bullets(result.sections)
    if not bullets:
        return CriterionResult(
            name="Quantified Achievements",
            icon="\U0001f4c8",
            score=3,
            status="fail",
            feedback="No bullets found in experience/projects to evaluate quantification.",
            fix="Add bullet points with measurable achievements (%, $, numbers, timeframes).",
            details={},
        )

    quant_re = re.compile("|".join(QUANTIFICATION_PATTERNS), re.IGNORECASE)
    quantified = [b for b in bullets if quant_re.search(b)]
    ratio = len(quantified) / len(bullets)

    if ratio >= 0.5:
        score = 10
    elif ratio >= 0.3:
        score = 8
    elif ratio >= 0.15:
        score = 5
    else:
        score = 3

    pct = round(ratio * 100)

    if score >= 8:
        feedback = f"{pct}% of your bullets are quantified ({len(quantified)}/{len(bullets)}). Strong use of metrics."
        fix = "Great quantification. Aim to keep at least 40% of bullets metric-driven."
    elif score >= 5:
        feedback = f"Only {pct}% of bullets include measurable results ({len(quantified)}/{len(bullets)})."
        fix = (
            f"Add numbers to {len(bullets) - len(quantified)} more bullets. "
            "Examples: 'Reduced load time by 40%', 'Managed team of 8', 'Grew revenue $200K'."
        )
    else:
        feedback = (
            f"Very few quantified bullets ({pct}% - {len(quantified)}/{len(bullets)}). "
            "ATS systems and recruiters prioritize measurable impact."
        )
        fix = (
            "Quantify at least 30-50% of your experience bullets. Add: percentages (%), "
            "dollar amounts ($), headcount numbers, time savings, or ranking (top 10%). "
            "Even estimates help: 'Processed ~200 tickets/week'."
        )

    return CriterionResult(
        name="Quantified Achievements",
        icon="\U0001f4c8",
        score=score,
        status=_status(score),
        feedback=feedback,
        fix=fix,
        details={
            "total_bullets": len(bullets),
            "quantified": len(quantified),
            "ratio": ratio,
            "examples": quantified[:3],
        },
    )


# ---------------------------------------------------------------------------
# 6. Keyword Match (JD)
# ---------------------------------------------------------------------------

_JD_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "must", "shall",
    "that", "this", "these", "those", "it", "its", "we", "you", "they",
    "our", "your", "their", "us", "them", "he", "she", "who", "what",
    "when", "where", "how", "why", "which", "can", "not", "no", "if",
    "all", "also", "than", "then", "so", "up", "out", "about", "into",
    "through", "during", "before", "after", "above", "below", "between",
    "each", "both", "few", "more", "most", "other", "some", "such",
    "only", "own", "same", "too", "very", "just", "because",
    "while", "although", "however", "therefore", "thus", "hence",
    "including", "etc", "eg", "ie", "work", "team", "role",
    "position", "job", "opportunity", "experience", "candidate", "ability",
    "strong", "good", "great", "excellent", "bonus", "plus", "nice",
    "required", "preferred", "desired", "looking", "seeking", "need",
}


def _extract_jd_keywords(jd_text: str) -> set[str]:
    """
    Extract meaningful keywords from a job description.

    Strategy:
    - Single tokens: keep if not a stopword and either in SHORT_TECH_TERMS
      or length > 3 and not purely numeric.
    - Bigrams: only keep if BOTH words are non-stopwords and at least one
      is longer than 4 chars (reduces noise dramatically).
    - Expand synonyms: if a known abbreviation/expansion is in the JD,
      add its counterpart to the keyword set.
    """
    jd_lower = jd_text.lower()
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9\+\#\-\.\/]*", jd_lower)

    keywords: set[str] = set()
    for t in tokens:
        if t in SHORT_TECH_TERMS:
            keywords.add(t)
        elif t not in _JD_STOPWORDS and len(t) > 3 and not t.isdigit():
            keywords.add(t)

    # Quality bigrams only
    words = jd_lower.split()
    for i in range(len(words) - 1):
        w1 = re.sub(r"[^a-z0-9\+\#\-]", "", words[i])
        w2 = re.sub(r"[^a-z0-9\+\#\-]", "", words[i + 1])
        if (w1 not in _JD_STOPWORDS and w2 not in _JD_STOPWORDS
                and (len(w1) > 4 or w1 in SHORT_TECH_TERMS)
                and (len(w2) > 4 or w2 in SHORT_TECH_TERMS)):
            keywords.add(f"{w1} {w2}")

    # Expand synonyms
    for kw, synonym in KEYWORD_SYNONYMS.items():
        if kw in keywords or kw in jd_lower:
            keywords.add(synonym)

    return keywords


def _keyword_in_resume(keyword: str, resume_lower: str) -> bool:
    """
    Check whether a keyword appears in the resume text.
    - Short tech terms (≤ 4 chars): word-boundary regex to avoid false positives.
    - Longer terms: substring match (fast, and false positives unlikely).
    """
    if keyword in SHORT_TECH_TERMS or len(keyword) <= 4:
        return bool(re.search(r"\b" + re.escape(keyword) + r"\b", resume_lower))
    return keyword in resume_lower


def score_keyword_match(result, jd_text=""):
    if not jd_text or not jd_text.strip():
        return CriterionResult(
            name="Keyword Match (JD)",
            icon="\U0001f3af",
            score=5,
            status="warn",
            feedback="No job description provided. Baseline score of 5/10 applied.",
            fix="Paste the job description to get a detailed keyword gap analysis.",
            details={"no_jd": True},
        )

    resume_lower = result.full_text.lower()
    jd_keywords = _extract_jd_keywords(jd_text)

    # Separate single-word keywords from bigrams for cleaner UI display
    single_kws = {k for k in jd_keywords if " " not in k}
    bigram_kws = {k for k in jd_keywords if " " in k}

    matched_single = {k for k in single_kws if _keyword_in_resume(k, resume_lower)}
    matched_bigram = {k for k in bigram_kws if _keyword_in_resume(k, resume_lower)}
    matched = matched_single | matched_bigram
    missing = jd_keywords - matched

    # Weight: single keywords 1pt each, bigrams 1.5pts each (more specific = more valuable)
    matched_weight = len(matched_single) + len(matched_bigram) * 1.5
    total_weight = len(single_kws) + len(bigram_kws) * 1.5
    match_rate = matched_weight / total_weight if total_weight else 0
    score = min(10, max(0, round(match_rate * 10)))
    pct = round(match_rate * 100)

    # For display: prioritize missing single-word tech terms (most actionable)
    missing_priority = sorted(
        missing,
        key=lambda k: (0 if k in SHORT_TECH_TERMS else 1 if " " not in k else 2, len(k)),
    )

    if match_rate >= 0.7:
        feedback = (
            f"Strong keyword alignment: {pct}% of JD terms found in your resume "
            f"({len(matched)}/{len(jd_keywords)} keywords matched)."
        )
        fix = "Good match. Scan the remaining missing keywords — add any that genuinely apply."
    elif match_rate >= 0.4:
        feedback = (
            f"Moderate keyword match: {pct}% "
            f"({len(matched)}/{len(jd_keywords)} JD terms found)."
        )
        fix = (
            f"Work in {min(len(missing), 10)} missing keywords into your skills section "
            "and bullet points. Prioritise technical terms and tools listed in the JD."
        )
    else:
        feedback = (
            f"Low keyword match: only {pct}% of JD terms appear in your resume "
            f"({len(matched)}/{len(jd_keywords)})."
        )
        fix = (
            f"Your resume is missing {len(missing)} keywords from the job description. "
            "Tailor your skills section to mirror the JD's exact tool and technology names. "
            "Integrate them naturally — don't just list them."
        )

    return CriterionResult(
        name="Keyword Match (JD)",
        icon="\U0001f3af",
        score=score,
        status=_status(score),
        feedback=feedback,
        fix=fix,
        details={
            "matched": sorted(matched),
            "missing": missing_priority,
            "total_jd_keywords": len(jd_keywords),
            "match_rate": match_rate,
        },
    )


# ---------------------------------------------------------------------------
# 7. Skills Section
# ---------------------------------------------------------------------------

def score_skills_section(result):
    skills_text = result.sections.get("skills", "")

    if not skills_text:
        return CriterionResult(
            name="Skills Section",
            icon="\U0001f6e0️",
            score=0,
            status="fail",
            feedback="No skills section detected. This is a critical ATS filter field.",
            fix=(
                "Add a dedicated 'Skills' or 'Technical Skills' section. "
                "List skills in comma-separated or pipe-separated format: "
                "Python | SQL | AWS | Docker | React"
            ),
            details={},
        )

    skills_lower = skills_text.lower()
    has_commas = "," in skills_text
    has_pipes = "|" in skills_text
    good_format = has_commas or has_pipes

    hard_found = [s for s in HARD_SKILLS_KEYWORDS if s in skills_lower]
    soft_only = not hard_found and any(s in skills_lower for s in SOFT_SKILLS_ONLY_INDICATORS)

    score = 10
    issues = []

    if not good_format:
        score -= 3
        issues.append("Skills are not comma or pipe separated - ATS may not parse individual skills correctly.")

    if soft_only:
        score -= 4
        issues.append("Only soft skills detected (communication, leadership, etc.). Add technical/hard skills.")
    elif not hard_found:
        score -= 2
        issues.append("No recognizable hard skills (tools, languages, platforms) found.")

    score = max(0, score)

    if not issues:
        feedback = (
            f"Skills section looks good. {len(hard_found)} hard skills detected "
            f"({'comma' if has_commas else 'pipe'}-separated format)."
        )
        fix = "Skills section is well-structured. Keep it updated with job-relevant tools."
    else:
        feedback = "Skills section found but has issues: " + " | ".join(issues)
        fix = (
            "Structure skills as: 'Languages: Python, Java, SQL | "
            "Frameworks: React, Django | Cloud: AWS, GCP | Tools: Git, Docker'. "
            "Include concrete technical tools, not just traits like 'teamwork'."
        )

    return CriterionResult(
        name="Skills Section",
        icon="\U0001f6e0️",
        score=score,
        status=_status(score),
        feedback=feedback,
        fix=fix,
        details={
            "hard_skills_found": hard_found[:10],
            "has_commas": has_commas,
            "has_pipes": has_pipes,
            "soft_only": soft_only,
        },
    )


# ---------------------------------------------------------------------------
# 8. Date Formatting
# ---------------------------------------------------------------------------

def score_date_formatting(result):
    text = result.full_text
    formats_found = {}
    for fmt_name, pattern in DATE_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            formats_found[fmt_name] = len(matches)

    distinct_date_formats = [k for k in formats_found if k not in ("present", "yyyy_only")]
    has_present = "present" in formats_found

    if not formats_found:
        return CriterionResult(
            name="Date Formatting",
            icon="\U0001f4c5",
            score=5,
            status="warn",
            feedback="No dates detected in the resume. Ensure employment dates are included.",
            fix="Add start and end dates (e.g. 'Jan 2021 - Present') to each role.",
            details={},
        )

    score = 10
    issues = []

    if len(distinct_date_formats) > 1:
        score -= 4
        issues.append(
            f"Inconsistent date formats detected: {', '.join(distinct_date_formats)}. "
            "Use one format throughout (e.g. 'Jan 2022 - Mar 2024')."
        )

    score = max(0, score)

    if not issues:
        feedback = (
            f"Date formatting looks consistent. "
            f"Formats detected: {', '.join(distinct_date_formats or ['year-only'])}."
            + (" 'Present' used for current role." if has_present else "")
        )
        fix = "Dates are consistent. No action needed."
    else:
        feedback = " | ".join(issues)
        fix = (
            "Standardize all dates to one format: 'Jan 2022' or '01/2022'. "
            "Use 'Present' for your current role's end date. "
            "Avoid mixing abbreviated months with numeric formats."
        )

    return CriterionResult(
        name="Date Formatting",
        icon="\U0001f4c5",
        score=score,
        status=_status(score),
        feedback=feedback,
        fix=fix,
        details={"formats_found": formats_found, "inconsistent": len(distinct_date_formats) > 1},
    )


# ---------------------------------------------------------------------------
# 9. Length & Density
# ---------------------------------------------------------------------------

def score_length_density(result):
    word_count = result.word_count
    page_count = result.page_count or 1

    score = 10
    issues = []

    if word_count < 200:
        score -= 6
        issues.append(f"Too short: only {word_count} words. Likely a sparse or incomplete resume.")
    elif word_count < 300:
        score -= 3
        issues.append(f"Slightly thin: {word_count} words. Consider adding more detail to roles.")
    elif word_count > 900:
        score -= 4
        issues.append(f"Too long: {word_count} words. ATS and recruiters prefer concise resumes.")
    elif word_count > 700:
        score -= 2
        issues.append(f"A bit lengthy: {word_count} words. Aim to trim to under 700.")

    if page_count > 2:
        score -= 2
        issues.append(f"{page_count} pages detected. Ideal is 1-2 pages for most roles.")

    score = max(0, score)

    if not issues:
        feedback = f"Good length: {word_count} words across {page_count} page(s). Well-balanced density."
        fix = "Resume length is optimal. Maintain 300-700 words for most roles."
    else:
        feedback = " | ".join(issues)
        if word_count < 300:
            fix = (
                f"Expand your resume to 300-600 words. Add 2-4 bullet points per role, "
                "a skills section, and a professional summary."
            )
        else:
            fix = (
                f"Trim your resume to under 700 words ({word_count - 700}+ words over limit). "
                "Remove outdated roles (10+ years old), generic phrases, and redundant bullets."
            )

    return CriterionResult(
        name="Length & Density",
        icon="\U0001f4cf",
        score=score,
        status=_status(score),
        feedback=feedback,
        fix=fix,
        details={"word_count": word_count, "page_count": page_count},
    )


# ---------------------------------------------------------------------------
# 10. Formatting Red Flags
# ---------------------------------------------------------------------------

def score_formatting_flags(result):
    text = result.full_text
    warnings = result.warnings
    issues = []

    table_warnings = [w for w in warnings if "table" in w.lower()]
    if table_warnings:
        issues.append("Tables detected. ATS systems often scramble table layouts.")

    skills_text = result.sections.get("skills", "")
    first_lines = set(text.splitlines()[:5])
    pipe_lines = sum(
        1 for line in text.splitlines()
        if ("|" in line or "\t\t" in line)
        and line.strip() not in first_lines
        and line.strip() not in skills_text
    )
    if pipe_lines > 8:
        issues.append(
            f"{pipe_lines} lines with column separators ('|') outside skills/contact - "
            "may indicate a multi-column layout that confuses ATS parsers."
        )

    unicode_found = [c for c in UNICODE_BULLETS if c in text]
    if unicode_found:
        issues.append(
            f"Non-standard bullet characters detected: {', '.join(unicode_found)}. "
            "Use plain hyphens (-) or asterisks (*) instead."
        )

    image_warnings = [w for w in warnings if "image" in w.lower() or "scanned" in w.lower()]
    if image_warnings:
        issues.append("Resume appears to be a scanned image - ATS cannot read image-based text.")

    header_footer_warnings = [w for w in warnings if "header" in w.lower() or "footer" in w.lower()]
    if header_footer_warnings:
        issues.append(
            "Contact info may be in a DOCX header/footer zone - some ATS systems ignore these. "
            "Move contact details into the main document body."
        )

    score = max(0, 10 - len(issues) * 3)

    if not issues:
        feedback = "No major formatting red flags detected. Document structure looks ATS-friendly."
        fix = "Formatting is clean. Continue using simple, single-column layout with plain text."
    else:
        feedback = f"{len(issues)} formatting issue(s) detected: " + " | ".join(issues)
        fix = (
            "Fix formatting issues: (1) Remove tables - use plain bullet lists instead. "
            "(2) Switch to single-column layout. "
            "(3) Replace special bullets with standard hyphens. "
            "(4) If scanned, re-export as a text-based PDF from Word/Google Docs."
        )

    return CriterionResult(
        name="Formatting Red Flags",
        icon="\U0001f6a9",
        score=score,
        status=_status(score),
        feedback=feedback,
        fix=fix,
        details={"issues": issues},
    )


# ---------------------------------------------------------------------------
# Master scorer
# ---------------------------------------------------------------------------

def run_all_scores(result, jd_text=""):
    """Run all 10 scoring functions and return a list of CriterionResult objects."""
    return [
        score_contact_info(result),
        score_section_headings(result),
        score_tense_consistency(result),
        score_bullet_structure(result),
        score_quantified_results(result),
        score_keyword_match(result, jd_text),
        score_skills_section(result),
        score_date_formatting(result),
        score_length_density(result),
        score_formatting_flags(result),
    ]


def compute_total_score(criteria):
    """Sum all criterion scores into a total out of 100."""
    return sum(c.score for c in criteria)
