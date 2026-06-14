"""
jd_scraper.py — Scrape job description text from a URL.

Supports LinkedIn and Indeed with targeted CSS selectors.
Falls back to generic paragraph extraction for any other page.

Security: all URLs are SSRF-validated before any outbound request.
Output is length-capped to prevent DoS via massive job postings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import security as _sec

_MAX_JD_TEXT = 50_000   # chars — same as security.MAX_JD_CHARS
_MAX_TITLE   = 200      # chars for job title / company name


@dataclass
class ScrapeResult:
    text: str = ""
    source: str = ""       # "linkedin" | "indeed" | "generic"
    job_title: Optional[str] = None
    company: Optional[str] = None
    error: Optional[str] = None


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_jd(url: str, timeout: int = 15) -> ScrapeResult:
    """
    Fetch and extract job description text from a URL.
    Returns ScrapeResult; check .error for failure.

    Security: URL is SSRF-validated before any request is made.
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # --- SSRF validation ---
    try:
        _sec.validate_url(url)
    except _sec.SecurityError as exc:
        return ScrapeResult(error=str(exc))

    try:
        import requests
    except ImportError:
        return ScrapeResult(error="requests is not installed. Run: pip install requests")

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return ScrapeResult(error="beautifulsoup4 is not installed. Run: pip install beautifulsoup4")

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code != 200:
            return ScrapeResult(
                error=f"Could not fetch page: HTTP {resp.status_code}. "
                      "Some sites block automated requests — try copying the JD manually."
            )
    except requests.exceptions.Timeout:
        return ScrapeResult(error="Request timed out. Check your internet connection.")
    except requests.exceptions.ConnectionError:
        return ScrapeResult(error="Could not connect to the URL. Check it and try again.")
    except Exception:
        return ScrapeResult(error="Request failed. Check the URL and try again.")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove noisy tags in all cases
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "iframe"]):
        tag.decompose()

    domain = _extract_domain(url)

    if "linkedin.com" in domain:
        return _parse_linkedin(soup, url)
    elif "indeed.com" in domain:
        return _parse_indeed(soup, url)
    elif "glassdoor.com" in domain:
        return _parse_glassdoor(soup, url)
    else:
        return _parse_generic(soup, url)


# ---------------------------------------------------------------------------
# Site-specific parsers
# ---------------------------------------------------------------------------

def _parse_linkedin(soup, url: str) -> ScrapeResult:
    """Extract JD from LinkedIn job page."""
    result = ScrapeResult(source="linkedin")

    # Job title
    title_el = soup.find(class_=re.compile(r"job-details-jobs-unified-top-card__job-title", re.I))
    if not title_el:
        title_el = soup.find("h1")
    result.job_title = _safe_title(title_el)

    # Company
    company_el = soup.find(class_=re.compile(r"job-details-jobs-unified-top-card__company-name", re.I))
    result.company = _safe_title(company_el)

    # Description body
    desc_el = soup.find(class_=re.compile(r"jobs-description|description__text|job-description", re.I))
    if desc_el:
        result.text = _clean_text(desc_el.get_text(separator="\n"))
    else:
        # LinkedIn often requires login — fall back to generic
        result = _parse_generic(soup, url)
        result.source = "linkedin"
        if not result.text:
            result.error = (
                "LinkedIn requires login to view full job descriptions. "
                "Copy the JD text manually and paste it below."
            )
    return result


def _parse_indeed(soup, url: str) -> ScrapeResult:
    """Extract JD from Indeed job page."""
    result = ScrapeResult(source="indeed")

    title_el = soup.find(class_=re.compile(r"jobsearch-JobInfoHeader-title", re.I))
    if not title_el:
        title_el = soup.find("h1")
    result.job_title = _safe_title(title_el)

    company_el = soup.find(class_=re.compile(r"jobsearch-InlineCompanyRating", re.I))
    result.company = _safe_title(company_el)

    desc_el = (
        soup.find(id="jobDescriptionText")
        or soup.find(class_=re.compile(r"jobDescription|job-description-text", re.I))
    )
    if desc_el:
        result.text = _clean_text(desc_el.get_text(separator="\n"))
    else:
        result = _parse_generic(soup, url)
        result.source = "indeed"

    return result


def _parse_glassdoor(soup, url: str) -> ScrapeResult:
    """Extract JD from Glassdoor job page."""
    result = ScrapeResult(source="glassdoor")

    title_el = soup.find(class_=re.compile(r"job-title|jobTitle", re.I))
    if not title_el:
        title_el = soup.find("h1")
    result.job_title = _safe_title(title_el)

    desc_el = soup.find(class_=re.compile(r"jobDescriptionContent|desc|description", re.I))
    if desc_el:
        result.text = _clean_text(desc_el.get_text(separator="\n"))
    else:
        result = _parse_generic(soup, url)
        result.source = "glassdoor"

    return result


def _parse_generic(soup, url: str) -> ScrapeResult:
    """
    Generic extractor: finds the largest block of paragraph/list text.
    Works on most careers pages and job boards.
    """
    result = ScrapeResult(source="generic")

    # Try common job-description containers
    selectors = [
        {"id": re.compile(r"job.?desc|description|posting", re.I)},
        {"class": re.compile(r"job.?desc|job.?detail|posting|description|content.?body", re.I)},
    ]
    for attrs in selectors:
        el = soup.find(True, attrs)
        if el:
            text = _clean_text(el.get_text(separator="\n"))
            if len(text.split()) > 50:
                result.text = text
                return result

    # Last resort: collect all <p> and <li> text
    blocks = []
    for tag in soup.find_all(["p", "li", "div"]):
        t = tag.get_text(strip=True)
        if len(t) > 40:
            blocks.append(t)

    if blocks:
        result.text = _clean_text("\n".join(blocks))
    else:
        result.error = (
            "Could not find job description text on this page. "
            "Try copying the text manually."
        )

    # Try to grab title from <h1>
    h1 = soup.find("h1")
    result.job_title = _safe_title(h1)

    return result


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _extract_domain(url: str) -> str:
    m = re.search(r"https?://([^/]+)", url)
    return m.group(1).lower() if m else ""


def _clean_text(text: str) -> str:
    """Collapse whitespace, remove blank-line runs > 2, and cap length."""
    lines = [line.strip() for line in text.splitlines()]
    # Collapse 3+ consecutive blank lines to 2
    cleaned: list[str] = []
    blank_streak = 0
    for line in lines:
        if not line:
            blank_streak += 1
            if blank_streak <= 2:
                cleaned.append("")
        else:
            blank_streak = 0
            cleaned.append(line)
    result = "\n".join(cleaned).strip()
    # Hard cap to prevent DoS via giant pages
    return result[:_MAX_JD_TEXT]


def _safe_title(el) -> str:
    """Extract text from a BS4 element and cap it at _MAX_TITLE chars."""
    if el is None:
        return ""
    return el.get_text(strip=True)[:_MAX_TITLE]
