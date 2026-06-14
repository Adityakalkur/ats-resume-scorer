"""
keywords.py -- Hardcoded vocabulary for the ATS scoring engine.
Contains: action verbs, gerund verbs, section heading variants,
common hard skills, weak phrase patterns, short tech terms,
keyword synonyms, and soft-skill-only indicators.
"""

# ---------------------------------------------------------------------------
# ACTION VERBS (150+) -- bullets should start with one of these
# ---------------------------------------------------------------------------
ACTION_VERBS = {
    # Leadership / Management
    "led", "managed", "directed", "supervised", "oversaw", "coordinated",
    "mentored", "coached", "guided", "headed", "spearheaded", "championed",
    "orchestrated", "delegated", "facilitated", "administered", "governed",
    "prioritized", "allocated", "hired", "recruited", "retained", "empowered",
    "unified", "aligned", "mobilized", "cultivated", "fostered", "inspired",
    # Building / Creating
    "built", "developed", "designed", "created", "engineered", "architected",
    "implemented", "deployed", "launched", "established", "founded",
    "constructed", "assembled", "crafted", "produced", "generated",
    "authored", "wrote", "coded", "programmed", "prototyped", "bootstrapped",
    "pioneered", "introduced", "initiated", "integrated", "migrated",
    "consolidated", "configured", "installed", "shipped", "released",
    "documented", "published", "proposed", "formulated", "devised",
    # Improving / Optimizing
    "improved", "optimized", "enhanced", "streamlined", "accelerated",
    "reduced", "increased", "grew", "scaled", "automated", "modernized",
    "refactored", "restructured", "transformed", "upgraded", "revamped",
    "simplified", "standardized", "eliminated", "minimized",
    "maximized", "amplified", "boosted", "doubled", "tripled", "cut",
    "lowered", "shortened", "sped", "expanded", "extended",
    # Analysis / Research
    "analyzed", "researched", "investigated", "evaluated", "assessed",
    "audited", "identified", "diagnosed", "measured", "tracked", "monitored",
    "tested", "validated", "reviewed", "benchmarked", "surveyed", "profiled",
    "forecasted", "modeled", "mapped", "quantified", "reported",
    "discovered", "uncovered", "recommended", "presented",
    # Collaboration / Communication
    "collaborated", "partnered", "communicated", "negotiated",
    "liaised", "consulted", "advised", "trained", "educated", "onboarded",
    "pitched", "influenced", "persuaded", "advocated",
    "demonstrated", "briefed", "interfaced",
    # Delivery / Achievement
    "delivered", "achieved", "completed", "exceeded", "secured", "won",
    "resolved", "solved", "executed", "drove", "saved",
    "recovered", "maintained", "ensured", "supported", "owned",
    "finalized", "closed", "surpassed",
    "outperformed", "earned", "obtained", "sourced", "acquired",
}

# Gerund (present participle) forms -- acceptable but weaker than past-tense.
GERUND_VERBS = {
    "leading", "managing", "directing", "supervising", "overseeing",
    "coordinating", "mentoring", "coaching", "guiding", "building",
    "developing", "designing", "creating", "engineering", "architecting",
    "implementing", "deploying", "launching", "establishing", "coding",
    "programming", "improving", "optimizing", "enhancing", "streamlining",
    "reducing", "increasing", "scaling", "automating", "refactoring",
    "analyzing", "researching", "evaluating", "assessing", "auditing",
    "tracking", "monitoring", "testing", "validating", "reviewing",
    "collaborating", "partnering", "presenting", "consulting", "advising",
    "training", "educating", "delivering", "executing", "driving",
    "maintaining", "supporting", "owning", "migrating", "integrating",
    "documenting", "pitching", "negotiating", "facilitating", "prioritizing",
}

# Short tech terms (<= 4 chars) matched with word boundaries to avoid false positives.
SHORT_TECH_TERMS = {
    "sql", "r", "go", "c", "aws", "gcp", "api", "sdk", "orm", "etl",
    "iac", "ml", "ai", "nlp", "cv", "bi", "ui", "ux", "qa", "ci",
    "cd", "git", "seo", "crm", "erp", "oop", "ios", "css", "html",
    "rest", "grpc", "saas", "paas", "iaas", "k8s",
}

# Abbreviation synonyms for keyword expansion in JD matching.
KEYWORD_SYNONYMS = {
    "machine learning": "ml",
    "ml": "machine learning",
    "artificial intelligence": "ai",
    "ai": "artificial intelligence",
    "natural language processing": "nlp",
    "nlp": "natural language processing",
    "continuous integration": "ci",
    "continuous deployment": "cd",
    "ci/cd": "continuous integration",
    "application programming interface": "api",
    "user experience": "ux",
    "user interface": "ui",
    "business intelligence": "bi",
    "kubernetes": "k8s",
    "k8s": "kubernetes",
    "amazon web services": "aws",
    "google cloud platform": "gcp",
    "large language model": "llm",
    "llm": "large language model",
}

# ---------------------------------------------------------------------------
# WEAK PHRASE PATTERNS -- red flags in bullet points
# ---------------------------------------------------------------------------
WEAK_PHRASES = [
    r"^responsible for",
    r"^duties included",
    r"^worked on",
    r"^helped (with|to)",
    r"^assisted (with|in)",
    r"^involved in",
    r"^participated in",
    r"^was part of",
    r"^tasked with",
    r"^i ",
    r"^the ",
    r"^a ",
]

# ---------------------------------------------------------------------------
# STANDARD SECTION HEADINGS -- accepted variants for each canonical section
# ---------------------------------------------------------------------------
SECTION_HEADINGS = {
    "summary": [
        "summary", "professional summary", "objective", "career objective",
        "profile", "professional profile", "about me", "overview",
        "executive summary", "career summary",
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "employment history", "work history", "career history",
        "relevant experience", "employment", "positions held",
    ],
    "education": [
        "education", "educational background", "academic background",
        "academics", "qualifications", "academic qualifications",
        "educational qualifications", "degrees",
    ],
    "skills": [
        "skills", "technical skills", "core competencies", "competencies",
        "key skills", "skill set", "technologies", "tools & technologies",
        "technical expertise", "areas of expertise", "proficiencies",
        "hard skills", "soft skills", "expertise",
    ],
    "certifications": [
        "certifications", "certificates", "certifications & licenses",
        "professional certifications", "licenses", "credentials",
        "accreditations",
    ],
    "projects": [
        "projects", "personal projects", "key projects", "notable projects",
        "side projects", "portfolio", "selected projects",
    ],
}

# Flat set of all accepted heading strings (lowercased)
ALL_VALID_HEADINGS: set[str] = {
    h for variants in SECTION_HEADINGS.values() for h in variants
}

# Required sections -- resume MUST contain at least one variant of each
REQUIRED_SECTIONS = ["experience", "education", "skills"]
RECOMMENDED_SECTIONS = ["summary"]

# ---------------------------------------------------------------------------
# HARD SKILLS -- indicators that a skills section contains technical content
# ---------------------------------------------------------------------------
HARD_SKILLS_KEYWORDS = {
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "bash",
    "sql", "nosql", "html", "css", "sass",
    # Frameworks / Libraries
    "react", "angular", "vue", "node", "django", "flask", "fastapi",
    "spring", "rails", "laravel", "express", "nextjs", "nuxtjs",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    # Cloud / DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "github actions", "ci/cd", "linux", "unix",
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
    "dynamodb", "snowflake", "bigquery", "oracle",
    # Tools / Platforms
    "git", "jira", "confluence", "slack", "figma", "photoshop", "tableau",
    "power bi", "excel", "salesforce", "hubspot", "sap",
    # Data / ML
    "machine learning", "deep learning", "nlp", "data analysis",
    "data science", "statistics", "a/b testing", "etl", "data pipelines",
}

SOFT_SKILLS_ONLY_INDICATORS = {
    "communication", "teamwork", "leadership", "problem-solving",
    "time management", "adaptability", "creativity", "attention to detail",
    "critical thinking", "interpersonal", "collaboration", "organization",
    "multitasking", "work ethic", "self-motivated", "proactive",
}

# ---------------------------------------------------------------------------
# DATE FORMAT PATTERNS (for regex matching in scorer.py)
# ---------------------------------------------------------------------------
DATE_PATTERNS = {
    "mon_yyyy": r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b",
    "mm_yyyy": r"\b(0?[1-9]|1[0-2])/\d{4}\b",
    "yyyy_only": r"\b(19|20)\d{2}\b",
    "present": r"\b(present|current|now|ongoing)\b",
    "full_month": r"\b(January|February|March|April|May|June|July|August|"
                  r"September|October|November|December)\s+\d{4}\b",
}

# Quantification signals -- bullets with these likely contain metrics
QUANTIFICATION_PATTERNS = [
    r"\d+\s*%",
    r"\$\s*\d+",
    r"£\s*\d+",
    r"€\s*\d+",
    r"\d+[kmb]\b",
    r"\d+\s*(million|billion|thousand|hundred)",
    r"\b\d+\+?\s*(users|customers|clients|employees|people|members)",
    r"\b\d+\s*(hours|days|weeks|months|years)",
    r"\b(increased|decreased|reduced|improved|grew|saved|generated)\b.*\d+",
    r"\b\d+x\b",
    r"\bx\d+\b",
    r"\btop\s+\d+",
    r"\#\s*\d+",
]

# Formatting red-flag unicode bullet replacements to detect
UNICODE_BULLETS = ["•", "◦", "▪", "▸", "▶", "➤", "➔", "✓", "✔", "★", "☆"]

# Common table/column separator characters that hint at multi-column layouts
TABLE_INDICATORS = ["|", "║", "│", "\t\t"]
