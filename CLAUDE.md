# ATS Resume Scorer — Project Context for Claude Code

## Project Purpose
A Streamlit web app that parses resumes (PDF/DOCX) and scores them against 10 ATS
criteria entirely through rule-based logic (no LLM calls).

---

## File Responsibilities

| File | Responsibility |
|------|---------------|
| `app.py` | Streamlit UI, layout wiring, tab structure. **Zero business logic.** |
| `parser.py` | PDF (pdfplumber) + DOCX (python-docx) text extraction. Returns `ParseResult`. |
| `scorer.py` | 10 independent scoring functions. Each returns `CriterionResult`. |
| `keywords.py` | Static vocabulary: action verbs, section heading variants, hard skills, patterns. |
| `ui_components.py` | Pure HTML/CSS rendering functions. No Streamlit state. |
| `report.py` | reportlab PDF export from scoring results. |
| `requirements.txt` | Python dependencies. |

---

## Data Flow

```
uploaded_file (bytes)
       ↓
parse_resume() → ParseResult
   .full_text: str
   .sections: dict[str, str]   # canonical_name → content
   .word_count: int
   .page_count: int
   .file_type: "pdf" | "docx"
   .warnings: list[str]
       ↓
run_all_scores(parse_result, jd_text) → list[CriterionResult]
   .name, .icon, .score (0–10), .status ("pass"|"warn"|"fail")
   .feedback: str, .fix: str, .details: dict
       ↓
compute_total_score() → int (0–100)
       ↓
UI renders tabs: Overview | Breakdown | Fixes | Keywords | Preview
```

---

## Scoring Criteria (scorer.py)

Each function signature: `score_*(result: ParseResult, ...) -> CriterionResult`

| # | Function | Key Logic |
|---|----------|-----------|
| 1 | `score_contact_info` | Regex for email, phone, LinkedIn, location. Deduct 2pt/missing field |
| 2 | `score_section_headings` | Check parsed sections against REQUIRED_SECTIONS in keywords.py |
| 3 | `score_tense_consistency` | Regex past/present verbs in experience section bullets |
| 4 | `score_bullet_structure` | First word of each bullet vs ACTION_VERBS set; detect WEAK_PHRASES |
| 5 | `score_quantified_results` | Count bullets matching QUANTIFICATION_PATTERNS; ratio × 10 |
| 6 | `score_keyword_match` | Extract JD terms, check intersection with resume text; baseline 5 if no JD |
| 7 | `score_skills_section` | Existence check, comma/pipe format, HARD_SKILLS_KEYWORDS presence |
| 8 | `score_date_formatting` | DATE_PATTERNS regex; penalize >1 distinct format |
| 9 | `score_length_density` | Word count 300–700 ideal; page count ≤2 |
| 10 | `score_formatting_flags` | Table warnings from parser, unicode bullets, multi-column hints |

**Status thresholds:** score ≥ 8 → "pass", ≥ 5 → "warn", < 5 → "fail"

---

## CSS Variables (ui_components.py → inject_css())

```css
--bg-main:      #0f1117   /* page background */
--bg-card:      #1a1d27   /* card / panel background */
--bg-card2:     #20243a   /* secondary card */
--accent:       #6c63ff   /* primary purple */
--accent-hover: #5a52e0   /* purple hover */
--text-primary: #f0f2f6   /* main text */
--text-muted:   #8b8fa8   /* secondary/gray text */
--green:        #22c55e   /* pass color */
--orange:       #f59e0b   /* warn color */
--red:          #ef4444   /* fail color */
--border:       #2d3148   /* card borders */
--radius:       16px      /* standard border-radius */
```

---

## Key Design Decisions

- **No LLM calls** — all scoring is deterministic regex + heuristic rules
- **Section segmentation** — heuristic (ALL-CAPS lines or Title-Case alone on line)
  mapped to canonical names via `keywords.SECTION_HEADINGS`
- **Keyword extraction (JD)** — simple tokenization + stopword removal + bigrams;
  no spaCy dependency at runtime (was considered but removed for simplicity)
- **Score ring** — pure SVG with CSS `@keyframes` animation injected via `st.markdown`
- **PDF export** — reportlab; gracefully skips if not installed

---

## Running Locally

```bash
cd ats_scorer
pip install -r requirements.txt
streamlit run app.py
```

App opens at http://localhost:8501
