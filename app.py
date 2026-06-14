"""
app.py -- Streamlit UI for ATS Resume Scorer (v4).
New in v4:
  - AI rewrite suggestions tab (user's own Anthropic API key)
  - Job description URL scraper (LinkedIn, Indeed, generic)
  - Side-by-side resume comparison mode
"""

import html as _html_mod
import io
import re
import streamlit as st

from parser import parse_resume
from scorer import run_all_scores, compute_total_score
from report import generate_pdf_report
import ui_components as ui
import security


# ---------------------------------------------------------------------------
# Cloud import helpers
# ---------------------------------------------------------------------------

def _dropbox_direct_url(url: str) -> str:
    """Convert a Dropbox share URL to a direct-download URL.
    Validates domain via security module before returning.
    """
    url = security.validate_dropbox_url(url.strip())
    if "dl=0" in url:
        return url.replace("dl=0", "dl=1")
    if "dl=1" in url:
        return url
    sep = "&" if "?" in url else "?"
    return url + sep + "dl=1"


def _gdrive_direct_url(url: str) -> tuple[str, str]:
    """Convert a Google Drive share URL to a direct-download URL.
    Validates domain via security module before returning.
    """
    url = security.validate_gdrive_url(url.strip())
    patterns = [
        r"/file/d/([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)",
        r"/open\?id=([a-zA-Z0-9_-]+)",
    ]
    file_id = None
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            file_id = m.group(1)
            break
    if not file_id:
        return url, "resume_from_drive"
    direct = f"https://drive.google.com/uc?export=download&id={file_id}"
    return direct, f"resume_{file_id[:8]}.pdf"


def _fetch_url(url: str) -> tuple[bytes, str]:
    """Download a resume file safely.
    Uses security.safe_download which enforces SSRF protection,
    streaming size cap, and timeout.
    """
    return security.safe_download(url)


# ---------------------------------------------------------------------------
# Helpers: parse + score a file
# ---------------------------------------------------------------------------

def _analyze_file(file_bytes: bytes, filename: str, jd_text: str) -> dict:
    """Parse and score a resume. Returns a dict of result state."""
    parse_result = parse_resume(file_bytes, filename)
    criteria = run_all_scores(parse_result, jd_text)
    total_score = compute_total_score(criteria)
    return {
        "parse_result": parse_result,
        "criteria": criteria,
        "total_score": total_score,
    }


def _validate_resume_bytes(file_bytes: bytes, filename: str) -> None:
    """Run size and magic-byte checks on resolved file bytes. Stops on failure."""
    try:
        security.validate_file_size(file_bytes)
        security.validate_file_magic(file_bytes, filename)
    except security.SecurityError as exc:
        st.markdown(ui.alert(str(exc), "error"), unsafe_allow_html=True)
        st.stop()


def _resolve_upload(source: str, uploaded_file, db_url: str, gd_url: str):
    """
    Resolve (file_bytes, filename) from whichever source is active.
    Enforces SSRF protection, file-size limits, and magic-byte checks.
    Raises RuntimeError or calls st.stop() on bad input.
    """
    if source == "Upload file":
        if not uploaded_file:
            st.markdown(
                ui.alert(
                    "No file received — the upload may have failed. "
                    "On mobile, try switching to **Google Drive link** for a more reliable upload.",
                    "error",
                ),
                unsafe_allow_html=True,
            )
            st.stop()
        file_bytes = uploaded_file.read()
        filename = security.validate_filename(uploaded_file.name)
        _validate_resume_bytes(file_bytes, filename)
        return file_bytes, filename

    elif source == "Dropbox link":
        url_val = (db_url or "").strip()
        if not url_val:
            st.markdown(ui.alert("Please enter a Dropbox share link.", "error"), unsafe_allow_html=True)
            st.stop()
        with st.spinner("Downloading from Dropbox..."):
            try:
                direct = _dropbox_direct_url(url_val)
                file_bytes, filename = _fetch_url(direct)
            except security.SecurityError as exc:
                st.markdown(ui.alert(str(exc), "error"), unsafe_allow_html=True)
                st.stop()
            except Exception:
                st.markdown(ui.alert(
                    "Dropbox download failed. Check the link is a valid public share URL.",
                    "error",
                ), unsafe_allow_html=True)
                st.stop()
        _validate_resume_bytes(file_bytes, filename)
        return file_bytes, filename

    else:  # Google Drive
        url_val = (gd_url or "").strip()
        if not url_val:
            st.markdown(ui.alert("Please enter a Google Drive share link.", "error"), unsafe_allow_html=True)
            st.stop()
        with st.spinner("Downloading from Google Drive..."):
            try:
                direct, hint = _gdrive_direct_url(url_val)
                file_bytes, fn = _fetch_url(direct)
                filename = fn or hint
            except security.SecurityError as exc:
                st.markdown(ui.alert(str(exc), "error"), unsafe_allow_html=True)
                st.stop()
            except Exception:
                st.markdown(ui.alert(
                    "Google Drive download failed. Ensure the file is shared "
                    "as 'Anyone with the link' and the URL is correct.",
                    "error",
                ), unsafe_allow_html=True)
                st.stop()
        _validate_resume_bytes(file_bytes, filename)
        return file_bytes, filename


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ATS Resume Scorer",
    page_icon="bolt",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(ui.inject_css(), unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
_DEFAULTS = {
    "mode": "single",           # "single" | "compare"
    "results": None,
    "parse_result": None,
    "total_score": None,
    "jd_used": "",
    "filename": "",
    # compare mode
    "results_b": None,
    "parse_result_b": None,
    "total_score_b": None,
    "filename_b": "",
    # AI suggestions
    "ai_suggestions": None,
    "anthropic_key": "",
}
for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ============================================================
# JD INPUT WIDGET  (shared between single + compare views)
# ============================================================
def _jd_input_widget(col) -> str:
    """
    Render the Job Description column (paste or URL scrape).
    Returns the JD text.
    """
    from jd_scraper import scrape_jd

    with col:
        st.markdown(
            '<div style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;'
            'color:var(--muted);text-transform:uppercase;font-family:var(--mono);">'
            'Job Description <span style="font-weight:400;text-transform:none;'
            'letter-spacing:0;color:var(--dim);">— optional</span></div>',
            unsafe_allow_html=True,
        )

        jd_mode = st.radio(
            "Job description input mode",
            ["Paste text", "Scrape from URL"],
            horizontal=True,
            label_visibility="collapsed",
        )

        jd_text = ""

        if jd_mode == "Paste text":
            jd_text = st.text_area(
                "Job Description",
                height=155,
                placeholder=(
                    "Paste the job listing here to enable keyword gap analysis.\n\n"
                    "Example: We need a Python developer with Django, REST APIs, AWS..."
                ),
                label_visibility="collapsed",
            )
            if jd_text.strip():
                wc = len(jd_text.split())
                st.markdown(
                    f'<div style="color:var(--accent);font-size:0.78rem;margin-top:0.2rem;">'
                    f'{wc} words — keyword analysis enabled</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div style="color:var(--dim);font-size:0.78rem;margin-top:0.2rem;">'
                    'Skip for a baseline 5/10 keyword score</div>',
                    unsafe_allow_html=True,
                )

        else:  # Scrape from URL
            jd_url = st.text_input(
                "Job listing URL",
                placeholder="https://www.linkedin.com/jobs/view/... or Indeed/Glassdoor URL",
                label_visibility="collapsed",
            )
            scrape_btn = st.button("Fetch JD", use_container_width=False, type="secondary")
            if scrape_btn and jd_url.strip():
                try:
                    security.validate_url(jd_url.strip())
                except security.SecurityError as _sec_exc:
                    st.markdown(ui.alert(str(_sec_exc), "error"), unsafe_allow_html=True)
                    scrape_btn = False
            if scrape_btn and jd_url.strip():
                with st.spinner("Fetching job description..."):
                    result = scrape_jd(jd_url.strip())
                if result.error:
                    st.markdown(ui.alert(result.error, "error"), unsafe_allow_html=True)
                else:
                    st.session_state["_scraped_jd"] = result.text
                    if result.job_title:
                        st.markdown(
                            ui.alert(f"Fetched: **{result.job_title}**"
                                     + (f" @ {result.company}" if result.company else ""),
                                     "success"),
                            unsafe_allow_html=True,
                        )

            # Show scraped text in a text_area for editing
            scraped = st.session_state.get("_scraped_jd", "")
            jd_text = st.text_area(
                "Fetched Job Description (editable)",
                value=scraped,
                height=115,
                label_visibility="collapsed",
                placeholder="Fetched text will appear here — you can edit it before analyzing.",
            )
            if jd_text.strip():
                wc = len(jd_text.split())
                st.markdown(
                    f'<div style="color:var(--accent);font-size:0.78rem;margin-top:0.2rem;">'
                    f'{wc} words — keyword analysis enabled</div>',
                    unsafe_allow_html=True,
                )

    return jd_text


# ============================================================
# RESUME UPLOAD COLUMN WIDGET
# ============================================================
def _resume_upload_widget(col, label: str = "Resume") -> tuple:
    """
    Render a resume source selector in `col`.
    Returns (uploaded_file, db_url, gd_url, source).
    """
    with col:
        st.markdown(
            f'<div style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;'
            f'color:var(--muted);text-transform:uppercase;font-family:var(--mono);'
            f'margin-bottom:0.5rem;">{label}</div>',
            unsafe_allow_html=True,
        )
        src_key = f"src_{label.lower().replace(' ', '_')}"
        source = st.radio(
            f"{label} source",
            ["Upload file", "Dropbox link", "Google Drive link"],
            horizontal=True,
            label_visibility="collapsed",
            key=src_key,
        )

        uploaded_file = None
        db_url = ""
        gd_url = ""

        if source == "Upload file":
            uploaded_file = st.file_uploader(
                f"Drop {label} here",
                type=["pdf", "docx", "doc", "txt", "rtf", "html", "htm"],
                label_visibility="collapsed",
                help="Supported: PDF, DOCX, TXT, RTF, HTML. Max 200 MB.",
                key=f"uploader_{label}",
            )
            if uploaded_file:
                safe_name = _html_mod.escape(uploaded_file.name)
                st.markdown(
                    f'<div style="color:var(--green);font-size:0.82rem;margin-top:0.3rem;">'
                    f'Ready: <b>{safe_name}</b></div>',
                    unsafe_allow_html=True,
                )
        elif source == "Dropbox link":
            st.markdown(
                ui.cloud_source_hint("dropbox", "Share publicly in Dropbox, paste the link."),
                unsafe_allow_html=True,
            )
            db_url = st.text_input(
                "Dropbox URL", placeholder="https://www.dropbox.com/s/xxxx/resume.pdf?dl=0",
                label_visibility="collapsed", key=f"db_{label}",
            )
            if db_url.strip():
                tag = "success" if "dropbox.com" in db_url else "error"
                msg = "Dropbox link ready." if tag == "success" else "Doesn't look like a Dropbox URL."
                st.markdown(ui.alert(msg, tag), unsafe_allow_html=True)
        else:
            st.markdown(
                ui.cloud_source_hint("gdrive", 'Set sharing to "Anyone with the link", paste below.'),
                unsafe_allow_html=True,
            )
            gd_url = st.text_input(
                "Google Drive URL",
                placeholder="https://drive.google.com/file/d/xxxx/view?usp=sharing",
                label_visibility="collapsed", key=f"gd_{label}",
            )
            if gd_url.strip():
                tag = "success" if "drive.google.com" in gd_url else "error"
                msg = "Drive link ready." if tag == "success" else "Doesn't look like a Drive URL."
                st.markdown(ui.alert(msg, tag), unsafe_allow_html=True)

    return uploaded_file, db_url, gd_url, source


# ============================================================
# VIEW A: UPLOAD  (single mode)
# ============================================================
def _render_upload_single():
    st.markdown(ui.hero_header(), unsafe_allow_html=True)

    # Mode switcher
    mode_col, _ = st.columns([2, 3])
    with mode_col:
        mode = st.radio(
            "Analysis mode",
            ["Single Resume", "Compare Two Resumes"],
            horizontal=True,
            label_visibility="collapsed",
        )
    if mode == "Compare Two Resumes":
        st.session_state["mode"] = "compare"
        st.rerun()

    st.markdown(ui.step_indicators(active=1), unsafe_allow_html=True)

    col_upload, col_jd = st.columns([1, 1], gap="medium")
    uploaded_file, db_url, gd_url, source = _resume_upload_widget(col_upload, "Resume")
    jd_text = _jd_input_widget(col_jd)

    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
    analyze_clicked = st.button("Analyze My Resume", use_container_width=True, type="primary")

    if analyze_clicked:
        file_bytes, resume_filename = _resolve_upload(source, uploaded_file, db_url, gd_url)
        jd_text = security.cap_jd_text(jd_text)
        with st.status("Analyzing your resume...", expanded=True) as status:
            st.write("Parsing document...")
            parse_result = parse_resume(file_bytes, resume_filename)
            if not parse_result.full_text.strip():
                status.update(label="Parse failed", state="error")
                st.error("Could not extract text. Ensure the file is text-based and in a supported format.")
                for w in parse_result.warnings:
                    st.warning(w)
                st.stop()
            st.write("Running ATS scoring engine...")
            criteria = run_all_scores(parse_result, jd_text)
            total_score = compute_total_score(criteria)
            st.write("Building your report...")
            status.update(label="Analysis complete!", state="complete")

        st.session_state.parse_result = parse_result
        st.session_state.results = criteria
        st.session_state.total_score = total_score
        st.session_state.jd_used = jd_text
        st.session_state.filename = resume_filename
        st.session_state.ai_suggestions = None  # reset
        st.rerun()

    # Info accordions
    st.markdown("<div style='height:1.25rem;'></div>", unsafe_allow_html=True)
    st.markdown('<div style="height:1px;background:var(--border);margin-bottom:0.75rem;"></div>', unsafe_allow_html=True)
    info_col1, info_col2, info_col3 = st.columns(3)
    with info_col1:
        with st.expander("What is ATS?"):
            st.markdown(
                "An **Applicant Tracking System** automatically scans resumes before "
                "a human sees them. ~99% of Fortune 500 companies use one. "
                "Resumes that aren't ATS-optimised get filtered out even if you're qualified."
            )
    with info_col2:
        with st.expander("How scoring works"):
            st.markdown(
                "10 criteria, 10 points each = **100 total**:\n\n"
                "Contact Info · Section Headings · Tense Consistency · Bullet Structure · "
                "Quantified Results · Keyword Match · Skills Section · Date Formatting · "
                "Length & Density · Formatting Flags"
            )
    with info_col3:
        with st.expander("Common mistakes"):
            st.markdown(
                "- Tables or multi-column layouts\n"
                "- Starting bullets with 'Responsible for'\n"
                "- Missing a dedicated Skills section\n"
                "- Inconsistent date formats\n"
                "- No quantified results (%, $, numbers)"
            )
    st.markdown(ui.app_footer(), unsafe_allow_html=True)


# ============================================================
# VIEW A2: UPLOAD  (compare mode)
# ============================================================
def _render_upload_compare():
    st.markdown(ui.hero_header(), unsafe_allow_html=True)

    mode_col, _ = st.columns([2, 3])
    with mode_col:
        mode = st.radio(
            "Analysis mode",
            ["Single Resume", "Compare Two Resumes"],
            index=1,
            horizontal=True,
            label_visibility="collapsed",
            key="mode_cmp",
        )
    if mode == "Single Resume":
        st.session_state["mode"] = "single"
        st.rerun()

    st.markdown(
        '<div style="color:var(--accent);font-size:0.83rem;font-weight:600;margin:0.25rem 0 0.75rem;">'
        '&#9878; Upload two resume versions against the same job description to see which performs better.</div>',
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2, gap="medium")
    uf_a, db_a, gd_a, src_a = _resume_upload_widget(col_a, "Resume A")
    uf_b, db_b, gd_b, src_b = _resume_upload_widget(col_b, "Resume B")

    jd_col_full = st.container()
    jd_text = _jd_input_widget(jd_col_full)

    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
    compare_clicked = st.button("Compare Resumes", use_container_width=True, type="primary")

    if compare_clicked:
        fb_a, fn_a = _resolve_upload(src_a, uf_a, db_a, gd_a)
        fb_b, fn_b = _resolve_upload(src_b, uf_b, db_b, gd_b)
        jd_text = security.cap_jd_text(jd_text)

        with st.status("Analyzing both resumes...", expanded=True) as status:
            st.write("Parsing Resume A...")
            pr_a = parse_resume(fb_a, fn_a)
            st.write("Scoring Resume A...")
            cr_a = run_all_scores(pr_a, jd_text)
            ts_a = compute_total_score(cr_a)

            st.write("Parsing Resume B...")
            pr_b = parse_resume(fb_b, fn_b)
            st.write("Scoring Resume B...")
            cr_b = run_all_scores(pr_b, jd_text)
            ts_b = compute_total_score(cr_b)

            status.update(label="Comparison ready!", state="complete")

        st.session_state.results = cr_a
        st.session_state.parse_result = pr_a
        st.session_state.total_score = ts_a
        st.session_state.filename = fn_a
        st.session_state.jd_used = jd_text

        st.session_state.results_b = cr_b
        st.session_state.parse_result_b = pr_b
        st.session_state.total_score_b = ts_b
        st.session_state.filename_b = fn_b
        st.rerun()

    st.markdown(ui.app_footer(), unsafe_allow_html=True)


# ============================================================
# VIEW B: RESULTS (single mode)
# ============================================================
def _render_results_single():
    criteria = st.session_state.results
    parse_result = st.session_state.parse_result
    total_score = st.session_state.total_score
    jd_text = st.session_state.jd_used

    passed = [c for c in criteria if c.status == "pass"]
    warned = [c for c in criteria if c.status == "warn"]
    failed = [c for c in criteria if c.status == "fail"]

    hdr_col, btn_col = st.columns([4, 1], gap="small")
    with hdr_col:
        st.markdown(ui.results_header(st.session_state.filename, total_score), unsafe_allow_html=True)
    with btn_col:
        st.markdown("<div style='height:0.9rem;'></div>", unsafe_allow_html=True)
        if st.button("+ New Resume", use_container_width=True, type="secondary"):
            for key in _DEFAULTS:
                st.session_state[key] = _DEFAULTS[key]
            if "_scraped_jd" in st.session_state:
                del st.session_state["_scraped_jd"]
            st.rerun()

    st.markdown(ui.step_indicators(active=3), unsafe_allow_html=True)

    if parse_result.warnings:
        with st.expander(f"Parser notices ({len(parse_result.warnings)})"):
            for w in parse_result.warnings:
                st.info(w)

    # ── Tabs ─────────────────────────────────────────────────
    tab_overview, tab_breakdown, tab_fixes, tab_keywords, tab_ai, tab_preview = st.tabs([
        "Overview", "Full Breakdown", "Fix List", "Keywords", "AI Suggestions", "Resume Text",
    ])

    # ── Overview ──────────────────────────────────────────────
    with tab_overview:
        ring_col, cards_col = st.columns([1, 2], gap="medium")
        with ring_col:
            st.markdown(ui.score_ring(total_score, size=200), unsafe_allow_html=True)
        with cards_col:
            st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
            st.markdown(ui.summary_cards(len(passed), len(warned), len(failed)), unsafe_allow_html=True)
            pdf_bytes = generate_pdf_report(criteria, total_score)
            if pdf_bytes:
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_bytes,
                    file_name="ats_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )
        st.markdown(ui.section_label("All 10 Criteria at a Glance"), unsafe_allow_html=True)
        st.markdown(ui.criteria_grid(criteria), unsafe_allow_html=True)

    # ── Full Breakdown ─────────────────────────────────────────
    with tab_breakdown:
        st.markdown(ui.section_label("Per-Category Breakdown"), unsafe_allow_html=True)
        for c in criteria:
            with st.expander(f"{c.icon}  {c.name}  —  {c.score}/10", expanded=(c.status == "fail")):
                col_bar, col_badge = st.columns([3, 1])
                with col_bar:
                    st.markdown(ui.score_bar(c.score), unsafe_allow_html=True)
                with col_badge:
                    st.markdown(
                        f'<div style="text-align:right;padding-top:4px;">{ui.status_badge(c.status)}</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(ui.feedback_bullets(c.feedback, c.fix, c.status), unsafe_allow_html=True)
                if c.details and c.status != "pass":
                    detail_items = [
                        (k.replace("_", " ").title(), v)
                        for k, v in c.details.items()
                        if not k.startswith("no_") and v not in (None, "", [], {})
                    ]
                    if detail_items:
                        rows = "".join(
                            f'<tr><td style="color:var(--dim);font-size:0.76rem;padding:0.2rem 0.75rem 0.2rem 0;'
                            f'white-space:nowrap;font-family:var(--mono);">{k}</td>'
                            f'<td style="color:var(--muted);font-size:0.8rem;">{v}</td></tr>'
                            for k, v in detail_items[:6]
                        )
                        st.markdown(
                            f'<table style="border-collapse:collapse;margin-top:0.6rem;width:100%;">'
                            f'{rows}</table>',
                            unsafe_allow_html=True,
                        )

    # ── Fix List ───────────────────────────────────────────────
    with tab_fixes:
        if not failed and not warned:
            st.markdown(ui.alert("No critical issues found. Your resume is in great shape!", "success"), unsafe_allow_html=True)
        if failed:
            st.markdown(ui.section_label("Fix Now  (High Priority)"), unsafe_allow_html=True)
            for c in failed:
                st.markdown(ui.fix_card(c.icon, c.name, c.fix, "fail"), unsafe_allow_html=True)
        if warned:
            st.markdown(ui.section_label("Improve  (Medium Priority)"), unsafe_allow_html=True)
            for c in warned:
                st.markdown(ui.fix_card(c.icon, c.name, c.fix, "warn"), unsafe_allow_html=True)
        if passed:
            st.markdown(ui.section_label("Looking Good"), unsafe_allow_html=True)
            for c in passed:
                st.markdown(ui.fix_card(c.icon, c.name, c.fix, "pass"), unsafe_allow_html=True)

    # ── Keywords ───────────────────────────────────────────────
    with tab_keywords:
        kw_c = next((c for c in criteria if "Keyword" in c.name), None)
        if not jd_text.strip() or (kw_c and kw_c.details.get("no_jd")):
            st.markdown(ui.no_jd_prompt(), unsafe_allow_html=True)
        elif kw_c:
            details = kw_c.details
            match_rate = details.get("match_rate", 0)
            matched_kw = details.get("matched", [])
            missing_kw = details.get("missing", [])
            total_kw = details.get("total_jd_keywords", 1)
            pct = round(match_rate * 100)
            rate_col, prog_col = st.columns([1, 3], gap="medium")
            with rate_col:
                st.markdown(
                    f'<div style="text-align:center;padding:0.75rem 0;">'
                    f'<div style="font-size:2.75rem;font-weight:800;color:var(--accent);'
                    f'font-family:var(--mono);">{pct}%</div>'
                    f'<div style="color:var(--muted);font-size:0.78rem;margin-top:0.2rem;">match rate</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with prog_col:
                st.markdown("<div style='height:1.1rem;'></div>", unsafe_allow_html=True)
                st.progress(match_rate)
                st.markdown(
                    f'<div style="color:var(--muted);font-size:0.78rem;margin-top:0.3rem;">'
                    f'{len(matched_kw)} of {total_kw} job description terms found in your resume</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
            col_m, col_miss = st.columns(2)
            with col_m:
                st.markdown(ui.section_label(f"Matched  ({len(matched_kw)})"), unsafe_allow_html=True)
                st.markdown(ui.keyword_pills_block(sorted(matched_kw)[:40], matched=True), unsafe_allow_html=True)
            with col_miss:
                st.markdown(ui.section_label(f"Missing  ({len(missing_kw)})"), unsafe_allow_html=True)
                st.markdown(
                    '<p style="font-size:0.77rem;color:var(--dim);margin-bottom:0.4rem;">'
                    'Add these naturally to your resume</p>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    ui.keyword_pills_block(sorted(missing_kw, key=len, reverse=True)[:40], matched=False),
                    unsafe_allow_html=True,
                )

    # ── AI Suggestions ─────────────────────────────────────────
    with tab_ai:
        st.markdown(
            '<div style="color:var(--muted);font-size:0.83rem;margin-bottom:0.8rem;">'
            'Enter your Anthropic API key to get Claude-generated rewrites for your weakest sections. '
            'Your key is never stored — it stays in your browser session only.</div>',
            unsafe_allow_html=True,
        )
        key_col, btn_col_ai = st.columns([3, 1], gap="small")
        with key_col:
            api_key = st.text_input(
                "Anthropic API Key",
                type="password",
                placeholder="sk-ant-api03-...",
                value=st.session_state.anthropic_key,
                label_visibility="collapsed",
            )
        with btn_col_ai:
            generate_btn = st.button("Generate Suggestions", use_container_width=True, type="primary")
        if api_key:
            st.session_state.anthropic_key = api_key
        if generate_btn:
            _key_err = None
            try:
                security.validate_api_key_format(api_key)
            except security.SecurityError as _ke:
                _key_err = str(_ke)
            if _key_err:
                st.markdown(ui.alert(_key_err, "error"), unsafe_allow_html=True)
            elif not api_key.strip():
                st.markdown(ui.alert("Please enter your Anthropic API key.", "error"), unsafe_allow_html=True)
            else:
                from ai_rewriter import get_all_suggestions
                weak_count = sum(1 for c in criteria if c.score < 7)
                with st.status(f"Generating suggestions for {weak_count} weak criteria...", expanded=True) as ai_status:
                    suggestions = get_all_suggestions(
                        api_key=api_key.strip(),
                        criteria=criteria,
                        resume_text=parse_result.full_text,
                        jd_text=jd_text,
                    )
                    ai_status.update(label="Suggestions ready!", state="complete")
                st.session_state.ai_suggestions = suggestions
        if st.session_state.ai_suggestions:
            suggestions = st.session_state.ai_suggestions
            if not suggestions:
                st.markdown(
                    ui.alert("All criteria score 7+. No major rewrites needed!", "success"),
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    ui.section_label(f"AI Rewrite Suggestions  ({len(suggestions)} criteria)"),
                    unsafe_allow_html=True,
                )
                for s in suggestions:
                    st.markdown(ui.ai_suggestion_card(s), unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="color:var(--dim);font-size:0.82rem;margin-top:0.5rem;">'
                'Get your API key at <a href="https://console.anthropic.com" target="_blank" '
                'style="color:var(--accent);">console.anthropic.com</a> — '
                'claude-haiku-4-5 is used (fast &amp; affordable).</div>',
                unsafe_allow_html=True,
            )

    # ── Resume Text ────────────────────────────────────────────
    with tab_preview:
        m1, m2, m3 = st.columns(3)
        m1.metric("Word Count", parse_result.word_count)
        m2.metric("Pages", parse_result.page_count)
        m3.metric("Format", parse_result.file_type.upper())
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        st.markdown(
            ui.resume_preview_html(parse_result.full_text, parse_result.sections),
            unsafe_allow_html=True,
        )

    st.markdown(ui.app_footer(), unsafe_allow_html=True)


# ============================================================
# VIEW B2: RESULTS (compare mode)
# ============================================================
def _render_results_compare():
    cr_a = st.session_state.results
    cr_b = st.session_state.results_b
    ts_a = st.session_state.total_score
    ts_b = st.session_state.total_score_b
    fn_a = st.session_state.filename
    fn_b = st.session_state.filename_b

    label_a = fn_a or "Resume A"
    label_b = fn_b or "Resume B"

    hdr_col, btn_col = st.columns([4, 1], gap="small")
    with hdr_col:
        st.markdown(
            '<div style="font-size:1.5rem;font-weight:800;color:var(--fg);margin:0.5rem 0 0.25rem;">'
            '&#9878; Resume Comparison</div>',
            unsafe_allow_html=True,
        )
    with btn_col:
        st.markdown("<div style='height:0.9rem;'></div>", unsafe_allow_html=True)
        if st.button("+ New", use_container_width=True, type="secondary"):
            for key in _DEFAULTS:
                st.session_state[key] = _DEFAULTS[key]
            if "_scraped_jd" in st.session_state:
                del st.session_state["_scraped_jd"]
            st.rerun()

    st.markdown(ui.comparison_header(label_a, label_b, ts_a, ts_b), unsafe_allow_html=True)

    tab_cmp, tab_a, tab_b = st.tabs([
        "Score Comparison",
        f"Resume A — {int(round(ts_a * 100))}/100",
        f"Resume B — {int(round(ts_b * 100))}/100",
    ])

    with tab_cmp:
        st.markdown(ui.section_label("Criterion-by-Criterion"), unsafe_allow_html=True)
        st.markdown(ui.comparison_table(cr_a, cr_b, ts_a, ts_b, label_a, label_b), unsafe_allow_html=True)
        winner = label_a if ts_a > ts_b else (label_b if ts_b > ts_a else None)
        if winner:
            diff = abs(int(round(ts_a * 100)) - int(round(ts_b * 100)))
            st.markdown(
                ui.alert(
                    f"**{winner}** wins by **{diff} points**. "
                    "Use the tabs above to explore each resume's full breakdown.",
                    "success",
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(ui.alert("It's a tie! Both resumes scored equally.", "success"), unsafe_allow_html=True)

    def _render_single_tab(criteria, parse_result, total_score, jd_text):
        passed = [c for c in criteria if c.status == "pass"]
        warned = [c for c in criteria if c.status == "warn"]
        failed = [c for c in criteria if c.status == "fail"]
        st.markdown(ui.score_ring(total_score, size=180), unsafe_allow_html=True)
        st.markdown(ui.summary_cards(len(passed), len(warned), len(failed)), unsafe_allow_html=True)
        st.markdown(ui.section_label("Criteria"), unsafe_allow_html=True)
        st.markdown(ui.criteria_grid(criteria), unsafe_allow_html=True)
        if failed or warned:
            st.markdown(ui.section_label("Priority Fixes"), unsafe_allow_html=True)
            for c in (failed + warned):
                st.markdown(ui.fix_card(c.icon, c.name, c.fix, c.status), unsafe_allow_html=True)

    with tab_a:
        _render_single_tab(cr_a, st.session_state.parse_result, ts_a, st.session_state.jd_used)

    with tab_b:
        _render_single_tab(cr_b, st.session_state.parse_result_b, ts_b, st.session_state.jd_used)

    st.markdown(ui.app_footer(), unsafe_allow_html=True)


# ============================================================
# ROUTER
# ============================================================
mode = st.session_state.get("mode", "single")
has_single = st.session_state.results is not None
has_compare = st.session_state.results_b is not None

if mode == "compare":
    if has_compare:
        _render_results_compare()
    else:
        _render_upload_compare()
else:
    if has_single:
        _render_results_single()
    else:
        _render_upload_single()
