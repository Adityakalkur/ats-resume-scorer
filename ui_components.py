"""
ui_components.py -- Reusable styled HTML/CSS components for ATS Scorer (v3).
Design system: Thermal Cartography -- warm darks, terracotta accent, monospaced status.
All functions return HTML strings for st.markdown(..., unsafe_allow_html=True).
"""

from __future__ import annotations
import html as html_lib


# ---------------------------------------------------------------------------
# CSS injection
# ---------------------------------------------------------------------------

def inject_css() -> str:
    return """
<style>
/* Non-blocking font load — swap ensures text shows immediately with system font */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700;9..40,800&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg-main:   #0d0d0b;
    --bg-card:   #141413;
    --bg-card2:  #1c1b19;
    --accent:    #d97757;
    --accent2:   #c9954a;
    --blue:      #6a9bcc;
    --green:     #788c5d;
    --red:       #ef4444;
    --text:      #faf9f5;
    --muted:     #7a7870;
    --dim:       #3a3830;
    --border:    #2a2824;
    --radius:    14px;
    --font:      'DM Sans', system-ui, sans-serif;
    --mono:      'DM Mono', 'Courier New', monospace;
}

/* Base */
html, body, [data-testid="stApp"], .main {
    background-color: var(--bg-main) !important;
    font-family: var(--font) !important;
    color: var(--text) !important;
}

/* Hide chrome — keep header visible so sidebar toggle works */
#MainMenu, footer { visibility: hidden; }
header { visibility: visible; background: transparent !important; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stHeader"] { background: transparent !important; }
.block-container {
    padding-top: 0.75rem !important;
    padding-bottom: 2rem !important;
    max-width: 900px !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0f0f0d !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] .stExpander {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    margin-bottom: 0.5rem !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    border: 1.5px dashed var(--accent) !important;
    border-radius: var(--radius) !important;
    background: rgba(217,119,87,0.04) !important;
    padding: 1.75rem !important;
    transition: all 0.25s ease;
}
[data-testid="stFileUploader"]:hover {
    background: rgba(217,119,87,0.08) !important;
    box-shadow: 0 0 28px rgba(217,119,87,0.15) !important;
}
[data-testid="stFileUploader"] label { display: none !important; }
[data-testid="stFileUploaderDropzoneInstructions"] {
    color: var(--muted) !important;
    font-family: var(--font) !important;
}

/* Textarea */
textarea {
    background-color: var(--bg-card2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: var(--font) !important;
    font-size: 0.9rem !important;
}
textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(217,119,87,0.15) !important;
    outline: none !important;
}

/* Primary button */
[data-testid="stBaseButton-primary"] {
    background: var(--accent) !important;
    color: #faf9f5 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.7rem 1.8rem !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    font-family: var(--font) !important;
    letter-spacing: 0.01em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 12px rgba(217,119,87,0.3) !important;
}
[data-testid="stBaseButton-primary"]:hover {
    background: #c86a44 !important;
    box-shadow: 0 4px 20px rgba(217,119,87,0.45) !important;
    transform: translateY(-1px) !important;
}

/* Secondary button */
[data-testid="stBaseButton-secondary"] {
    background: var(--bg-card2) !important;
    color: var(--muted) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: var(--font) !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
[data-testid="stBaseButton-secondary"]:hover {
    color: var(--text) !important;
    border-color: var(--accent) !important;
    background: var(--bg-card) !important;
}

/* Tabs */
[data-testid="stTabs"] [role="tablist"] {
    background: var(--bg-card) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 2px !important;
    border-bottom: none !important;
}
[data-testid="stTabs"] [role="tab"] {
    color: var(--muted) !important;
    font-family: var(--font) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    border-radius: 7px !important;
    border: none !important;
    padding: 0.45rem 0.9rem !important;
    transition: all 0.18s ease !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: var(--accent) !important;
    color: #faf9f5 !important;
    font-weight: 600 !important;
}
[data-testid="stTabs"] [role="tab"]:hover {
    background: rgba(217,119,87,0.1) !important;
    color: var(--text) !important;
}
[data-testid="stTabPanel"] { padding-top: 1.25rem !important; }

/* Expanders */
.stExpander {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    margin-bottom: 0.5rem !important;
}

/* Progress bar */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
    border-radius: 4px !important;
}
[data-testid="stProgress"] > div {
    background: var(--dim) !important;
    border-radius: 4px !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border-radius: 12px !important;
    padding: 0.75rem 1rem !important;
    border: 1px solid var(--border) !important;
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.78rem !important; font-family: var(--font) !important; }
[data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 700 !important; }

/* Status widget */
[data-testid="stStatusWidget"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}

/* Alert */
[data-testid="stAlert"] { border-radius: 10px !important; }

/* Divider */
hr { border-color: var(--border) !important; }

/* Resume preview */
.resume-preview-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    max-height: 480px;
    overflow-y: auto;
    font-size: 0.82rem;
    line-height: 1.8;
    color: var(--muted);
    white-space: pre-wrap;
    font-family: var(--mono);
}
.resume-preview-box .sh {
    color: var(--accent);
    font-weight: 600;
    font-size: 0.86rem;
    letter-spacing: 0.06em;
    display: block;
    margin-top: 0.75rem;
}

/* Criteria grid */
.cg-row { display:flex; gap:0.5rem; margin-bottom:0.5rem; }
.cg-cell {
    flex:1; background:var(--bg-card2); border:1px solid var(--border);
    border-radius:9px; padding:0.55rem 0.7rem;
    display:flex; align-items:center; gap:0.5rem; min-width:0;
}
.cg-cell.pass { border-left:3px solid var(--green); }
.cg-cell.warn { border-left:3px solid var(--accent2); }
.cg-cell.fail { border-left:3px solid var(--red); }
.cg-icon { font-size:0.9rem; flex-shrink:0; }
.cg-name { font-size:0.77rem; color:var(--muted); flex:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-family:var(--font); }
.cg-score { font-size:0.82rem; font-weight:700; font-family:var(--mono); flex-shrink:0; }
.cg-score.pass { color:var(--green); }
.cg-score.warn { color:var(--accent2); }
.cg-score.fail { color:var(--red); }

/* Score ring wrapper */
.score-ring-wrap { display:flex; flex-direction:column; align-items:center; padding:1rem 0; }

/* Stat cards */
.stat-cards { display:flex; gap:0.75rem; margin:1.25rem 0; }
.stat-card {
    flex:1; background:var(--bg-card2);
    border:1px solid var(--border); border-radius:12px;
    padding:1rem 1.25rem; position:relative; overflow:hidden;
}
.stat-card::before {
    content:''; position:absolute; left:0; top:0; bottom:0;
    width:3px;
}
.stat-card.pass::before { background:var(--green); }
.stat-card.warn::before { background:var(--accent2); }
.stat-card.fail::before { background:var(--red); }
.stat-val { font-size:2rem; font-weight:800; font-family:var(--mono); line-height:1; }
.stat-card.pass .stat-val { color:var(--green); }
.stat-card.warn .stat-val { color:var(--accent2); }
.stat-card.fail .stat-val { color:var(--red); }
.stat-label { font-size:0.76rem; color:var(--muted); margin-top:0.3rem; font-family:var(--font); }

/* Section label */
.section-label {
    font-size:0.7rem; font-weight:700; letter-spacing:0.12em;
    color:var(--accent); text-transform:uppercase; font-family:var(--mono);
    margin:1.25rem 0 0.6rem; padding-bottom:0.4rem;
    border-bottom:1px solid var(--border);
}

/* Status badge */
.badge {
    display:inline-block; font-size:0.68rem; font-weight:600;
    padding:0.2rem 0.55rem; border-radius:4px; font-family:var(--mono);
    letter-spacing:0.06em; text-transform:uppercase;
}
.badge.pass { background:rgba(120,140,93,0.18); color:var(--green); }
.badge.warn { background:rgba(201,149,74,0.18); color:var(--accent2); }
.badge.fail { background:rgba(239,68,68,0.18); color:var(--red); }

/* Score bar */
.score-bar-wrap { height:5px; background:var(--dim); border-radius:3px; overflow:hidden; margin:0.35rem 0; }
.score-bar-fill { height:100%; border-radius:3px; transition:width 0.6s ease; }

/* Fix card */
.fix-card {
    background:var(--bg-card2); border:1px solid var(--border);
    border-radius:10px; padding:0.85rem 1rem; margin-bottom:0.5rem;
    display:flex; flex-direction:column; gap:0.25rem; position:relative;
}
.fix-card.fail { border-left:3px solid var(--red); }
.fix-card.warn { border-left:3px solid var(--accent2); }
.fix-card.pass { border-left:3px solid var(--green); }
.fix-card-header { display:flex; align-items:center; gap:0.5rem; }
.fix-card-icon { font-size:1rem; }
.fix-card-name { font-weight:600; font-size:0.88rem; color:var(--text); font-family:var(--font); flex:1; }
.fix-card-priority {
    font-size:0.65rem; font-weight:700; letter-spacing:0.08em;
    font-family:var(--mono); text-transform:uppercase;
    padding:0.15rem 0.4rem; border-radius:3px;
}
.fix-card-priority.fail { color:var(--red); background:rgba(239,68,68,0.1); }
.fix-card-priority.warn { color:var(--accent2); background:rgba(201,149,74,0.1); }
.fix-card-priority.pass { color:var(--green); background:rgba(120,140,93,0.1); }
.fix-card-text { font-size:0.82rem; color:var(--muted); line-height:1.5; padding-left:1.5rem; }

/* Keyword pills */
.kw-pills { display:flex; flex-wrap:wrap; gap:0.4rem; }
.kw-pill {
    font-size:0.75rem; padding:0.2rem 0.6rem; border-radius:5px;
    font-family:var(--mono); border:1px solid;
}
.kw-pill.match { background:rgba(120,140,93,0.14); color:var(--green); border-color:rgba(120,140,93,0.35); }
.kw-pill.miss  { background:rgba(239,68,68,0.1); color:var(--red); border-color:rgba(239,68,68,0.3); }

/* Step indicators */
.steps-wrap {
    display:flex; align-items:center; justify-content:center;
    gap:0; margin:0.75rem 0 1.5rem; padding:0.85rem 1.5rem;
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:12px;
}
.step { display:flex; align-items:center; gap:0.6rem; font-size:0.82rem; font-family:var(--font); }
.step-num {
    width:26px; height:26px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:0.72rem; font-weight:700; font-family:var(--mono); flex-shrink:0;
}
.step-num.done   { background:var(--accent); color:#faf9f5; }
.step-num.active { background:rgba(217,119,87,0.2); color:var(--accent); border:1.5px solid var(--accent); }
.step-num.idle   { background:var(--dim); color:var(--muted); }
.step-label      { font-weight:500; }
.step-label.done   { color:var(--accent); }
.step-label.active { color:var(--text); }
.step-label.idle   { color:var(--muted); }
.step-line { flex:1; height:1px; background:var(--dim); min-width:40px; margin:0 0.75rem; }

/* Upload card */
.upload-card {
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:var(--radius); padding:1.5rem 1.75rem; margin-bottom:1rem;
}
.upload-card-title {
    font-size:0.7rem; font-weight:700; letter-spacing:0.1em;
    color:var(--muted); text-transform:uppercase; font-family:var(--mono);
    margin-bottom:0.75rem;
}

/* Results header */
.results-header {
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:var(--radius); padding:1rem 1.5rem;
    display:flex; align-items:center; gap:1.5rem; margin-bottom:1.25rem;
}
.rh-info { flex:1; }
.rh-filename { font-size:1rem; font-weight:600; color:var(--text); font-family:var(--font); }
.rh-meta { font-size:0.75rem; color:var(--muted); margin-top:0.2rem; font-family:var(--font); }
.rh-score { text-align:right; }
.rh-score-num { font-size:3rem; font-weight:800; font-family:var(--mono); line-height:1; }
.rh-score-num.great { color:var(--green); }
.rh-score-num.ok    { color:var(--accent2); }
.rh-score-num.poor  { color:var(--red); }
.rh-score-denom { font-size:0.8rem; color:var(--muted); font-family:var(--mono); }
.rh-verdict { font-size:0.73rem; color:var(--muted); font-family:var(--font); margin-top:0.15rem; }

/* No JD prompt */
.no-jd-wrap {
    text-align:center; padding:2.5rem 1rem; color:var(--muted); font-family:var(--font);
}
.no-jd-icon { font-size:2rem; margin-bottom:0.5rem; }
.no-jd-text { font-size:0.88rem; line-height:1.6; }

/* Inline alert */
.tc-alert {
    border-radius:9px; padding:0.75rem 1rem; font-size:0.85rem;
    margin:0.5rem 0; font-family:var(--font); border:1px solid;
}
.tc-alert.info    { background:rgba(106,155,204,0.1); color:var(--blue); border-color:rgba(106,155,204,0.25); }
.tc-alert.success { background:rgba(120,140,93,0.12); color:var(--green); border-color:rgba(120,140,93,0.3); }
.tc-alert.warning { background:rgba(201,149,74,0.1); color:var(--accent2); border-color:rgba(201,149,74,0.25); }
.tc-alert.error   { background:rgba(239,68,68,0.1); color:var(--red); border-color:rgba(239,68,68,0.25); }

/* Footer */
.tc-footer {
    text-align:center; padding:1.5rem 0 0.5rem;
    font-size:0.72rem; color:var(--dim); font-family:var(--mono);
    letter-spacing:0.04em; border-top:1px solid var(--border); margin-top:2rem;
}

/* ── Cross-platform / browser compatibility ─────────────────────────── */

/* Prevent iOS Safari from auto-zooming text on focus */
html {
    -webkit-text-size-adjust: 100%;
    text-size-adjust: 100%;
}

/* iOS smooth momentum scrolling in overflow containers */
.resume-preview-box {
    -webkit-overflow-scrolling: touch;
}

/* Fix Safari border-radius clipping with overflow:hidden on cards */
.fix-card, .stat-card, .tc-alert, .results-header,
.upload-card, .cg-cell, .kw-pill {
    -webkit-transform: translateZ(0);
    transform: translateZ(0);
}

/* Prevent double-tap zoom on buttons and tabs (iOS) */
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-secondary"],
[data-testid="stTabs"] [role="tab"],
[data-testid="stRadio"] label {
    touch-action: manipulation;
}

/* ── Responsive: tablet (≤ 768 px) ─────────────────────────────────── */
@media (max-width: 768px) {
    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }
    /* Steps: hide connector lines, let steps wrap */
    .step-line { display: none !important; }
    .steps-wrap {
        flex-wrap: wrap;
        gap: 0.4rem !important;
        padding: 0.6rem 0.75rem !important;
        justify-content: flex-start;
    }
    .step { gap: 0.4rem; }
    .step-label { font-size: 0.75rem; }

    /* Stat cards: 2 columns on tablet */
    .stat-cards { flex-wrap: wrap; }
    .stat-card { flex: 1 1 calc(50% - 0.75rem); min-width: 120px; }
}

/* ── Responsive: mobile (≤ 480 px) ─────────────────────────────────── */
@media (max-width: 480px) {
    /* Results header stacks vertically */
    .results-header {
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: 0.75rem !important;
    }
    .rh-score { text-align: left !important; }
    .rh-score-num { font-size: 2.2rem !important; }

    /* Criteria grid: single column */
    .cg-row { flex-direction: column !important; }

    /* Stat cards: single column */
    .stat-cards { flex-direction: column !important; }
    .stat-card { flex: 1 1 100% !important; }
    .stat-val { font-size: 1.6rem !important; }

    /* Minimum 44 px tap targets (Apple HIG) */
    [data-testid="stBaseButton-primary"],
    [data-testid="stBaseButton-secondary"] {
        min-height: 44px !important;
    }
    [data-testid="stTabs"] [role="tab"] {
        min-height: 40px !important;
        padding: 0.55rem 0.6rem !important;
        font-size: 0.76rem !important;
    }
    /* Radio buttons easier to tap */
    [data-testid="stRadio"] label {
        min-height: 40px;
        display: flex;
        align-items: center;
    }

    /* Keyword pills wrap tighter */
    .kw-pill { font-size: 0.7rem !important; padding: 0.18rem 0.5rem !important; }

    /* Resume preview smaller on mobile */
    .resume-preview-box {
        max-height: 320px !important;
        font-size: 0.76rem !important;
    }

    /* Fix card text slightly smaller */
    .fix-card-text { font-size: 0.79rem !important; }

    /* Feedback bullets */
    .fb-list { font-size: 0.8rem !important; }
}

/* ── Scrollbar styling (Chrome/Edge/Safari) ──────────────────────────── */
.resume-preview-box::-webkit-scrollbar { width: 4px; }
.resume-preview-box::-webkit-scrollbar-track { background: var(--dim); border-radius: 2px; }
.resume-preview-box::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 2px; }

/* Firefox scrollbar */
.resume-preview-box { scrollbar-width: thin; scrollbar-color: var(--accent) var(--dim); }

/* ── Print / PDF export styles ──────────────────────────────────────── */
@media print {
    #MainMenu, header, footer, .tc-footer,
    [data-testid="stSidebar"] { display: none !important; }
    body { background: white !important; color: black !important; }
    .block-container { max-width: 100% !important; }
}
</style>
"""


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

def hero_header() -> str:
    return """
<div style="text-align:center;padding:1.25rem 0 0.5rem;">
  <div style="font-size:0.7rem;font-weight:700;letter-spacing:0.14em;
              color:var(--accent);text-transform:uppercase;font-family:var(--mono);
              margin-bottom:0.5rem;">ATS Resume Scorer</div>
  <div style="font-size:1.9rem;font-weight:800;color:var(--text);
              font-family:var(--font);letter-spacing:-0.02em;line-height:1.2;">
    Beat the bots.<br>
    <span style="color:var(--accent);">Land the interview.</span>
  </div>
  <div style="font-size:0.88rem;color:var(--muted);margin-top:0.6rem;
              font-family:var(--font);max-width:480px;margin-inline:auto;">
    Upload your resume and get a detailed ATS compatibility score in seconds.
  </div>
</div>
"""


def step_indicators(active: int) -> str:
    """active: 1=upload, 2=analyzing, 3=results"""
    def state(n):
        if n < active: return "done"
        if n == active: return "active"
        return "idle"

    def num_html(n):
        s = state(n)
        if s == "done":
            return '<div class="step-num done">&#10003;</div>'
        return f'<div class="step-num {s}">{n:02d}</div>'

    steps = [(1, "Upload"), (2, "Analyze"), (3, "Review")]
    parts = []
    for i, (n, lbl) in enumerate(steps):
        s = state(n)
        parts.append(f"""
<div class="step">
  {num_html(n)}
  <span class="step-label {s}">{lbl}</span>
</div>""")
        if i < len(steps) - 1:
            parts.append('<div class="step-line"></div>')

    return f'<div class="steps-wrap">{"".join(parts)}</div>'


def card_start(title: str, subtitle: str = "") -> str:
    sub = (f'<div style="font-size:0.8rem;color:var(--muted);margin-top:0.2rem;'
           f'font-family:var(--font);">{subtitle}</div>') if subtitle else ""
    return f"""
<div class="upload-card">
  <div class="upload-card-title">{title}</div>
  {sub}
"""


def card_end() -> str:
    return "</div>"


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def sidebar_logo() -> str:
    return """
<div style="padding:0.5rem 0 1rem;">
  <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.16em;
              color:var(--accent);text-transform:uppercase;font-family:var(--mono);">
    ATS SCORER
  </div>
  <div style="font-size:0.75rem;color:var(--muted);margin-top:0.25rem;font-family:var(--font);">
    Beat the bots. Land the interview.
  </div>
  <div style="height:1px;background:var(--border);margin:0.75rem 0;"></div>
</div>
"""


def sidebar_score_mini(score: int) -> str:
    if score >= 80:
        col = "var(--green)"
    elif score >= 60:
        col = "var(--accent2)"
    else:
        col = "var(--red)"
    return f"""
<div style="background:var(--bg-card2);border:1px solid var(--border);
            border-radius:10px;padding:0.85rem 1rem;margin-bottom:0.75rem;">
  <div style="font-size:0.65rem;color:var(--muted);font-family:var(--mono);
              text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">
    ATS Score
  </div>
  <div style="font-size:1.8rem;font-weight:800;font-family:var(--mono);
              color:{col};line-height:1;">
    {score}
    <span style="font-size:0.85rem;color:var(--muted);font-weight:400;">/ 100</span>
  </div>
  <div style="height:5px;background:var(--dim);border-radius:3px;margin-top:0.5rem;overflow:hidden;">
    <div style="height:100%;width:{score}%;background:{col};border-radius:3px;"></div>
  </div>
</div>
"""


# ---------------------------------------------------------------------------
# Results view
# ---------------------------------------------------------------------------

def results_header(filename: str, score: int) -> str:
    if score >= 80:
        sc_class = "great"
        verdict = "Strong resume &mdash; minor fixes needed"
    elif score >= 60:
        sc_class = "ok"
        verdict = "Decent resume &mdash; room for improvement"
    else:
        sc_class = "poor"
        verdict = "Significant gaps found &mdash; needs work"

    safe_fn = html_lib.escape(filename)
    return f"""
<div class="results-header">
  <div class="rh-info">
    <div class="rh-filename">{safe_fn}</div>
    <div class="rh-meta">Analysis complete</div>
  </div>
  <div class="rh-score">
    <div class="rh-score-num {sc_class}">{score}</div>
    <div class="rh-score-denom">/ 100</div>
    <div class="rh-verdict">{verdict}</div>
  </div>
</div>
"""


def score_ring(score: int, size: int = 160) -> str:
    """Animated SVG circular score ring."""
    if score >= 80:
        color = "var(--green)"
    elif score >= 60:
        color = "var(--accent2)"
    else:
        color = "var(--red)"

    r = (size - 20) // 2
    cx = cy = size // 2
    circumference = 2 * 3.14159 * r
    dash = circumference * score / 100
    gap = circumference - dash

    return f"""
<div class="score-ring-wrap">
  <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
    <circle cx="{cx}" cy="{cy}" r="{r}"
      fill="none" stroke="var(--dim)" stroke-width="10"/>
    <circle cx="{cx}" cy="{cy}" r="{r}"
      fill="none" stroke="{color}" stroke-width="10"
      stroke-linecap="round"
      stroke-dasharray="{dash:.1f} {gap:.1f}"
      transform="rotate(-90 {cx} {cy})"
      style="transition:stroke-dasharray 0.8s ease;"/>
    <text x="{cx}" y="{cy - 6}" text-anchor="middle"
      font-size="{size // 4}" font-weight="800"
      fill="var(--text)" font-family="var(--mono)">{score}</text>
    <text x="{cx}" y="{cy + size // 8}" text-anchor="middle"
      font-size="{size // 10}" fill="var(--muted)"
      font-family="var(--font)">/ 100</text>
  </svg>
</div>
"""


def summary_cards(passed: int, warned: int, failed: int) -> str:
    return f"""
<div class="stat-cards">
  <div class="stat-card pass">
    <div class="stat-val">{passed}</div>
    <div class="stat-label">Passed</div>
  </div>
  <div class="stat-card warn">
    <div class="stat-val">{warned}</div>
    <div class="stat-label">Warnings</div>
  </div>
  <div class="stat-card fail">
    <div class="stat-val">{failed}</div>
    <div class="stat-label">Failed</div>
  </div>
</div>
"""


def criteria_grid(criteria: list) -> str:
    rows_html = []
    pairs = [criteria[i:i+2] for i in range(0, len(criteria), 2)]
    for pair in pairs:
        cells = ""
        for c in pair:
            cells += f"""
<div class="cg-cell {c.status}">
  <span class="cg-icon">{c.icon}</span>
  <span class="cg-name">{html_lib.escape(c.name)}</span>
  <span class="cg-score {c.status}">{c.score}/10</span>
</div>"""
        rows_html.append(f'<div class="cg-row">{cells}</div>')
    return "\n".join(rows_html)


def section_label(title: str) -> str:
    return f'<div class="section-label">{html_lib.escape(title)}</div>'


def status_badge(status: str) -> str:
    labels = {"pass": "Pass", "warn": "Warn", "fail": "Fail"}
    lbl = labels.get(status, status)
    return f'<span class="badge {status}">{lbl}</span>'


def score_bar(score: int) -> str:
    if score >= 8:
        color = "var(--green)"
    elif score >= 5:
        color = "var(--accent2)"
    else:
        color = "var(--red)"
    pct = score * 10
    return f"""
<div class="score-bar-wrap">
  <div class="score-bar-fill" style="width:{pct}%;background:{color};"></div>
</div>
"""


def fix_card(icon: str, name: str, fix_text: str, status: str) -> str:
    priority_map = {"fail": "Fix Now", "warn": "Improve", "pass": "Good"}
    priority = priority_map.get(status, "")
    safe_name = html_lib.escape(name)
    safe_fix = html_lib.escape(fix_text)
    return f"""
<div class="fix-card {status}">
  <div class="fix-card-header">
    <span class="fix-card-icon">{icon}</span>
    <span class="fix-card-name">{safe_name}</span>
    <span class="fix-card-priority {status}">{priority}</span>
  </div>
  <div class="fix-card-text">{safe_fix}</div>
</div>
"""


def keyword_pills_block(words: list, matched=None) -> str:
    """
    matched: bool → all pills get that class (True=match, False=miss)
             set/list → each word compared against the collection
    """
    pills = ""
    if isinstance(matched, bool):
        cls = "match" if matched else "miss"
        for w in words:
            pills += f'<span class="kw-pill {cls}">{html_lib.escape(w)}</span>'
    else:
        matched_lower = {m.lower() for m in (matched or set())}
        for w in words:
            cls = "match" if w.lower() in matched_lower else "miss"
            pills += f'<span class="kw-pill {cls}">{html_lib.escape(w)}</span>'
    return f'<div class="kw-pills">{pills}</div>'


def feedback_bullets(feedback: str, fix: str, status: str) -> str:
    """
    Render scorer feedback as structured bullet points, followed by a styled fix box.
    Splits on '. ' to turn multi-sentence feedback into scannable bullets.
    """
    if status == "pass":
        border_color = "var(--green)"
    elif status == "warn":
        border_color = "var(--accent2)"
    else:
        border_color = "var(--red)"

    # Split feedback into bullet points on '. ' boundaries
    sentences = [s.strip() for s in feedback.replace("  ", " ").split(". ") if s.strip()]
    # Re-add periods stripped by split (except last if it already ends with one)
    bullets_html = ""
    for s in sentences:
        if not s.endswith("."):
            s = s + "."
        safe = html_lib.escape(s)
        bullets_html += f"""
<li style="margin-bottom:0.35rem;color:var(--muted);font-size:0.86rem;line-height:1.55;">
  {safe}
</li>"""

    fix_box = ""
    if status != "pass" and fix:
        safe_fix = html_lib.escape(fix)
        fix_box = f"""
<div style="background:var(--bg-main);border-left:3px solid {border_color};
            border-radius:0 8px 8px 0;padding:0.65rem 1rem;margin-top:0.75rem;
            font-size:0.84rem;color:var(--text);">
  <span style="color:{border_color};font-weight:600;font-family:var(--mono);
               font-size:0.75rem;letter-spacing:0.06em;text-transform:uppercase;">
    How to fix&nbsp;
  </span>{safe_fix}
</div>"""

    return f"""
<ul style="margin:0.5rem 0 0 0.25rem;padding-left:1.25rem;list-style:disc;">
  {bullets_html}
</ul>
{fix_box}
"""


def no_jd_prompt() -> str:
    return """
<div class="no-jd-wrap">
  <div class="no-jd-icon">&#128269;</div>
  <div class="no-jd-text">
    No job description provided.<br>
    Go back to the upload view and paste a job listing<br>
    to enable keyword gap analysis.
  </div>
</div>
"""


def alert(msg: str, kind: str = "info") -> str:
    icons = {"info": "&#8505;", "success": "&#10003;", "warning": "&#9888;", "error": "&#10007;"}
    icon = icons.get(kind, "&#8505;")
    safe_msg = html_lib.escape(msg)
    return f'<div class="tc-alert {kind}">{icon}&nbsp; {safe_msg}</div>'


def app_footer() -> str:
    return """
<div class="tc-footer">
  ATS Resume Scorer &nbsp;&middot;&nbsp; No data stored &nbsp;&middot;&nbsp;
  100% rule-based &nbsp;&middot;&nbsp; Built for job seekers
</div>
"""


def resume_preview_html(full_text: str, sections: dict) -> str:
    """Scrollable resume text preview with section headers highlighted."""
    import html as _h
    safe = _h.escape(full_text)
    for canonical, content in sections.items():
        first_line = content.split("\n")[0] if content else ""
        if first_line:
            safe_heading = _h.escape(first_line.upper())
            safe = safe.replace(
                _h.escape(first_line),
                f'<span class="sh">{safe_heading}</span>',
                1,
            )
    return f'<div class="resume-preview-box">{safe}</div>'


def cloud_source_hint(provider: str, instruction: str) -> str:
    """Styled hint block for Dropbox / Google Drive import."""
    icons = {
        "dropbox": "&#128451;",   # folder icon
        "gdrive":  "&#128196;",   # page icon
    }
    colors = {
        "dropbox": "#0061fe",
        "gdrive":  "#4285f4",
    }
    icon  = icons.get(provider, "&#128279;")
    color = colors.get(provider, "var(--accent)")
    safe_instruction = html_lib.escape(instruction)
    return f"""
<div style="background:var(--bg-card2);border:1px solid var(--border);
            border-left:3px solid {color};border-radius:9px;
            padding:0.65rem 0.9rem;margin-bottom:0.5rem;font-size:0.82rem;">
  <span style="font-size:1rem;margin-right:0.4rem;">{icon}</span>
  <span style="color:var(--muted);">{safe_instruction}</span>
</div>
"""


# ---------------------------------------------------------------------------
# AI suggestion card
# ---------------------------------------------------------------------------

def ai_suggestion_card(suggestion) -> str:
    """
    Render one AI rewrite suggestion.
    `suggestion` is an ai_rewriter.RewriteSuggestion dataclass.
    """
    import html as _h

    if suggestion.error:
        return f"""
<div style="background:var(--bg-card);border:1px solid var(--border);
            border-left:3px solid var(--red);border-radius:12px;
            padding:1rem 1.1rem;margin-bottom:1rem;">
  <div style="color:var(--red);font-size:0.85rem;font-weight:600;margin-bottom:0.3rem;">
    {_h.escape(suggestion.icon)}  {_h.escape(suggestion.criterion_name)}  —  Error
  </div>
  <div style="color:var(--muted);font-size:0.82rem;">{_h.escape(suggestion.error)}</div>
</div>
"""

    score_color = (
        "var(--green)" if suggestion.current_score >= 7
        else "var(--accent2)" if suggestion.current_score >= 4
        else "var(--red)"
    )

    bullets_html = "".join(
        f'<li style="margin-bottom:0.4rem;color:var(--fg);font-size:0.83rem;">'
        f'{_h.escape(b)}</li>'
        for b in suggestion.improved_bullets
    )

    return f"""
<div style="background:var(--bg-card);border:1px solid var(--border);
            border-left:3px solid var(--accent);border-radius:12px;
            padding:1.1rem 1.2rem;margin-bottom:1.1rem;">
  <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.6rem;">
    <span style="font-size:1.15rem;">{_h.escape(suggestion.icon)}</span>
    <span style="font-weight:700;color:var(--fg);font-size:0.95rem;">
      {_h.escape(suggestion.criterion_name)}
    </span>
    <span style="margin-left:auto;font-family:var(--mono);font-size:0.8rem;
                 color:{score_color};background:var(--bg-card2);
                 border:1px solid var(--border);border-radius:6px;
                 padding:0.1rem 0.5rem;">{suggestion.current_score}/10</span>
  </div>
  <div style="font-weight:600;color:var(--accent);font-size:0.85rem;margin-bottom:0.7rem;">
    {_h.escape(suggestion.suggestion_title)}
  </div>
  <ul style="margin:0 0 0.75rem 1.1rem;padding:0;list-style:disc;">
    {bullets_html}
  </ul>
  <div style="border-top:1px solid var(--border);padding-top:0.6rem;
              color:var(--dim);font-size:0.78rem;font-style:italic;">
    {_h.escape(suggestion.explanation)}
  </div>
</div>
"""


# ---------------------------------------------------------------------------
# Side-by-side comparison table
# ---------------------------------------------------------------------------

def comparison_table(criteria_a: list, criteria_b: list,
                     score_a: float, score_b: float,
                     label_a: str = "Resume A", label_b: str = "Resume B") -> str:
    """
    Render a full side-by-side comparison of two scored resumes.
    """
    import html as _h

    def _score_cell(score: int, other: int) -> str:
        if score > other:
            bg = "var(--green)"
            col = "#fff"
        elif score < other:
            bg = "var(--red)"
            col = "#fff"
        else:
            bg = "var(--bg-card2)"
            col = "var(--muted)"
        return (
            f'<td style="text-align:center;padding:0.5rem 0.6rem;'
            f'background:{bg};color:{col};font-family:var(--mono);'
            f'font-weight:700;font-size:0.9rem;">{score}/10</td>'
        )

    def _winner_badge(score_a: int, score_b: int) -> str:
        if score_a > score_b:
            return '<td style="text-align:center;padding:0.5rem;"><span style="color:var(--green);font-size:0.75rem;font-weight:700;">▲ A</span></td>'
        elif score_b > score_a:
            return '<td style="text-align:center;padding:0.5rem;"><span style="color:var(--green);font-size:0.75rem;font-weight:700;">▲ B</span></td>'
        else:
            return '<td style="text-align:center;padding:0.5rem;color:var(--dim);font-size:0.75rem;">TIE</td>'

    rows = ""
    for ca, cb in zip(criteria_a, criteria_b):
        sa, sb = ca.score, cb.score
        rows += f"""
<tr style="border-bottom:1px solid var(--border);">
  <td style="padding:0.5rem 0.75rem;color:var(--muted);font-size:0.82rem;">
    {_h.escape(ca.icon)} {_h.escape(ca.name)}
  </td>
  {_score_cell(sa, sb)}
  {_score_cell(sb, sa)}
  {_winner_badge(sa, sb)}
</tr>"""

    total_a_int = int(round(score_a * 10))
    total_b_int = int(round(score_b * 10))
    winner_label = label_a if score_a > score_b else (label_b if score_b > score_a else "Tie")
    winner_color = "var(--green)"

    return f"""
<div style="overflow-x:auto;border-radius:12px;border:1px solid var(--border);margin-bottom:1rem;">
<table style="width:100%;border-collapse:collapse;background:var(--bg-card);">
  <thead>
    <tr style="background:var(--bg-card2);border-bottom:1px solid var(--border);">
      <th style="text-align:left;padding:0.65rem 0.75rem;color:var(--dim);
                 font-size:0.72rem;letter-spacing:0.07em;text-transform:uppercase;
                 font-family:var(--mono);">Criterion</th>
      <th style="text-align:center;padding:0.65rem;color:var(--accent);
                 font-size:0.78rem;">{_h.escape(label_a)}</th>
      <th style="text-align:center;padding:0.65rem;color:var(--accent2);
                 font-size:0.78rem;">{_h.escape(label_b)}</th>
      <th style="text-align:center;padding:0.65rem;color:var(--dim);
                 font-size:0.72rem;text-transform:uppercase;
                 font-family:var(--mono);">Winner</th>
    </tr>
  </thead>
  <tbody>
    {rows}
    <tr style="background:var(--bg-card2);">
      <td style="padding:0.65rem 0.75rem;font-weight:700;color:var(--fg);
                 font-size:0.85rem;font-family:var(--mono);">TOTAL</td>
      <td style="text-align:center;padding:0.65rem;font-weight:800;
                 font-size:1rem;font-family:var(--mono);
                 color:{'var(--green)' if score_a >= score_b else 'var(--muted)'};">
        {total_a_int}/100
      </td>
      <td style="text-align:center;padding:0.65rem;font-weight:800;
                 font-size:1rem;font-family:var(--mono);
                 color:{'var(--green)' if score_b >= score_a else 'var(--muted)'};">
        {total_b_int}/100
      </td>
      <td style="text-align:center;padding:0.65rem;font-weight:700;
                 color:{winner_color};font-size:0.85rem;">{_h.escape(winner_label)}</td>
    </tr>
  </tbody>
</table>
</div>
"""


def comparison_header(label_a: str, label_b: str,
                      score_a: float, score_b: float) -> str:
    """Two-column score ring summary for comparison mode."""
    import html as _h

    def _ring(score: float, label: str, color: str) -> str:
        pct = int(round(score * 100))
        if pct >= 80:
            grade, grade_color = "Excellent", "var(--green)"
        elif pct >= 65:
            grade, grade_color = "Good", "var(--accent2)"
        elif pct >= 50:
            grade, grade_color = "Fair", "var(--accent)"
        else:
            grade, grade_color = "Needs Work", "var(--red)"

        circ = 2 * 3.14159 * 54
        offset = circ * (1 - score)
        return f"""
<div style="text-align:center;padding:0.5rem;">
  <svg viewBox="0 0 120 120" width="130" style="display:block;margin:0 auto;">
    <circle cx="60" cy="60" r="54" fill="none" stroke="var(--border)" stroke-width="8"/>
    <circle cx="60" cy="60" r="54" fill="none" stroke="{color}" stroke-width="8"
            stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}"
            stroke-linecap="round" transform="rotate(-90 60 60)"/>
    <text x="60" y="58" text-anchor="middle" dominant-baseline="middle"
          font-family="DM Mono,monospace" font-weight="800" font-size="20" fill="{color}">
      {pct}
    </text>
    <text x="60" y="76" text-anchor="middle" dominant-baseline="middle"
          font-family="DM Sans,sans-serif" font-size="9" fill="var(--dim)">/ 100</text>
  </svg>
  <div style="font-weight:700;color:var(--fg);font-size:0.9rem;margin-top:0.4rem;">
    {_h.escape(label)}
  </div>
  <div style="color:{grade_color};font-size:0.78rem;font-weight:600;margin-top:0.1rem;">
    {grade}
  </div>
</div>"""

    left_color = "var(--accent)" if score_a >= score_b else "var(--muted)"
    right_color = "var(--accent2)" if score_b >= score_a else "var(--muted)"

    return f"""
<div style="display:flex;gap:1.5rem;justify-content:center;
            background:var(--bg-card);border:1px solid var(--border);
            border-radius:14px;padding:1.2rem;margin-bottom:1.2rem;">
  {_ring(score_a, label_a, left_color)}
  <div style="display:flex;align-items:center;color:var(--border);font-size:1.5rem;font-weight:300;">vs</div>
  {_ring(score_b, label_b, right_color)}
</div>
"""
