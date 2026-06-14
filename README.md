# ⚡ ATS Resume Scorer

A fully rule-based ATS resume analyzer built with Streamlit. Upload a resume (PDF or DOCX), optionally paste a job description, and get an instant score out of 100 with detailed fix recommendations.

## Features

- **10-criteria scoring engine** — contact info, section headings, tense consistency, bullet structure, quantified results, keyword match, skills section, date formatting, length/density, formatting flags
- **Dark-theme UI** — custom CSS, animated SVG score ring, tabbed results
- **JD keyword analysis** — match rate + gap analysis when job description is provided
- **PDF export** — download a full report via reportlab
- **No LLM calls** — 100% deterministic, fast, private

## Quick Start

```bash
# 1. Clone / navigate to project
cd ats_scorer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

App opens at **http://localhost:8501**

## File Structure

```
ats_scorer/
├── app.py              # Streamlit UI — layout only
├── parser.py           # PDF + DOCX text extraction
├── scorer.py           # 10 ATS scoring functions
├── keywords.py         # Action verbs, section headings, skill lists
├── ui_components.py    # HTML/CSS rendering components
├── report.py           # PDF export (reportlab)
├── requirements.txt
├── CLAUDE.md           # Developer context
└── README.md
```

## Score Interpretation

| Score | Status | Meaning |
|-------|--------|---------|
| 80–100 | 🟢 Strong | Likely to pass ATS filters |
| 60–79 | 🟡 Decent | Some gaps — tailor to JD |
| 0–59 | 🔴 Needs Work | High risk of ATS rejection |

## Requirements

- Python 3.10+
- streamlit, pdfplumber, python-docx, reportlab, pandas
- No API keys or external services needed
