from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"

STANDARDS_FILE = DATA_DIR / "standards_indicators.xlsx"
EVIDENCE_FILE = DATA_DIR / "evidence_repository.xlsx"
PROJECTS_FILE = DATA_DIR / "projects.xlsx"
ASSESSMENTS_FILE = DATA_DIR / "assessment_scores.csv"
RECOMMENDATIONS_FILE = DATA_DIR / "recommendations.csv"
LOGO_FILE = ASSETS_DIR / "logo.png"

APP_TITLE = "Smart City Standards Intelligence Platform"

NAVIGATION_ITEMS = [
    "Executive Overview",
    "Standards Library",
    "Domain Maturity View",
    "Project Comparison",
    "Gap Analysis",
    "Evidence Repository",
    "Project Checker",
]

DOMAIN_DISPLAY = {
    "Smart Mobility": "Mobility",
    "Smart Environment": "Environment",
    "Smart Governance": "Governance",
}

DOMAIN_COLORS = {
    "Smart Mobility": "#8FB4E8",
    "Smart Environment": "#61D7C4",
    "Smart Governance": "#AD8CEB",
}

CARD_BACKGROUNDS = {
    "blue": "#EAF2FF",
    "gray": "#F7F7F7",
    "purple": "#E5E1FC",
    "green": "#EAFFF9",
    "orange": "#FFF1E2",
    "red": "#FFE8E8",
}


PAGE_CARD_BACKGROUNDS = {
    "library_catalogue_card": "#F4FFFC",
    "library_information_card": "#FFFFFF",
    "library_specification_card": "#F7F3FF",
    "gap_largest_card": "#EAFFF6",
    "gap_missing_card": "#FFFFFF",
    "gap_low_evidence_card": "#FFFFFF",
    "gap_high_impact_card": "#F5F1FF",
    "gap_priority_card": "#FFFAEC",
    "evidence_records_card": "#FFF4F5",
    "evidence_details_card": "#F7F5FF",
}

MATURITY_RUBRIC = {
    0: "Indicator not implemented",
    1: "General planning exists, but implementation has not started",
    2: (
        "Partially implemented on a limited scale. Basic functionality exists, "
        "but coverage is limited."
    ),
    3: (
        "Implemented and operational, but gaps remain in coverage or integration "
        "and further improvement is needed."
    ),
    4: "Indicator is implemented with good performance",
    5: "Fully implemented, optimized, and continuously improved",
}

EVIDENCE_RUBRIC = {
    0: ("No evidence", "No source or supporting material is available."),
    1: (
        "Weak evidence",
        "General description, announcement, or unsupported claim.",
    ),
    2: (
        "Moderate evidence",
        "Public document, project page, report, or dataset reference.",
    ),
    3: (
        "Strong evidence",
        "Measured data, dashboard, API, evaluation report, or official document.",
    ),
    4: (
        "Verified evidence",
        "Evidence reviewed by an expert, stakeholder, or project owner.",
    ),
}

DATA_READINESS_RUBRIC = {
    0: ("No data", "There is no source at all, including a manual source."),
    1: (
        "Unstructured data",
        "Data exists in an unstructured format and requires manual extraction or "
        "cleaning before use, such as PDFs, paper records, or manual documents.",
    ),
    2: (
        "Structured but static",
        "Data exists in a usable structured format, but it is not updated frequently "
        "or refreshed automatically, such as database snapshots or spreadsheets.",
    ),
    3: (
        "Structured and live",
        "Data exists in a usable format and is updated frequently, such as through "
        "APIs or automatically updated systems.",
    ),
}

HIGH_PRIORITY_MIN = 3
WEAK_MATURITY_MAX = 2
LOW_EVIDENCE_MAX = 1
MISSING_DATA_LEVEL = 0

PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
    "scrollZoom": False,
}
