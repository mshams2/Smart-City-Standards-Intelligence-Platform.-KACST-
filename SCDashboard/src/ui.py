from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import pandas as pd
import streamlit as st

from .config import LOGO_FILE, NAVIGATION_ITEMS, PAGE_CARD_BACKGROUNDS


def _safe(value: object) -> str:
    if value is None or (
        not isinstance(value, (list, tuple, dict)) and pd.isna(value)
    ):
        return "—"
    return html.escape(str(value))


def image_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    suffix = path.suffix.lower().lstrip(".") or "png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/{suffix};base64,{encoded}"


def _page_card_css() -> str:
    rules = []
    for key, background in PAGE_CARD_BACKGROUNDS.items():
        rules.append(
            f"""
            .st-key-{key},
            .st-key-{key} > div[data-testid="stVerticalBlockBorderWrapper"] {{
                background: {background} !important;
            }}
            """
        )
    return "\n".join(rules)


def inject_global_css() -> None:
    css = """
        <style>
            :root {
                --text: #111216;
                --muted: #717783;
                --line: #E7E8EC;
                --panel: #F8F8FA;
                --radius-lg: 22px;
            }

            html, body, [class*="css"] {
                font-family: Inter, "Segoe UI", Arial, sans-serif;
                color: var(--text);
            }

            .stApp { background: #FFFFFF; }
            [data-testid="stHeader"] { background: transparent !important; }
            [data-testid="stToolbar"],
            [data-testid="stDecoration"],
            footer { display: none !important; }

            [data-testid="stMainBlockContainer"] {
                max-width: 1400px;
                padding: 2.7rem 2.1rem 4rem;
            }

            section[data-testid="stSidebar"] {
                width: 250px !important;
                min-width: 250px !important;
                max-width: 250px !important;
                flex: 0 0 250px !important;
                left: 0 !important;
                right: auto !important;
                margin: 0 !important;
                transform: translateX(0) !important;
                background: #FFFFFF !important;
                border-right: 1px solid #E3E5E9 !important;
            }

            section[data-testid="stSidebar"] > div:first-child,
            [data-testid="stSidebarContent"] {
                width: 250px !important;
                min-width: 250px !important;
                max-width: 250px !important;
                box-sizing: border-box !important;
            }

            [data-testid="stSidebarContent"] {
                padding: 1.9rem 1.15rem 6.2rem !important;
            }

            [data-testid="stSidebarCollapseButton"],
            [data-testid="collapsedControl"],
            [data-testid="stSidebarCollapsedControl"] {
                display: none !important;
            }

            [data-testid="stSidebar"] [role="radiogroup"] { gap: 0.2rem; }
            [data-testid="stSidebar"] [role="radiogroup"] label {
                min-height: 39px;
                padding: 0.5rem 0.55rem !important;
                border-radius: 9px;
                transition: background 120ms ease;
            }
            [data-testid="stSidebar"] [role="radiogroup"] label:hover {
                background: #F4F4F6;
            }
            [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
                background: #EEEEF0;
                font-weight: 600;
            }
            [data-testid="stSidebar"] [role="radiogroup"] label p {
                font-size: 0.89rem;
                color: #2F3238;
            }
            [data-testid="stSidebar"] [role="radiogroup"] label[data-baseweb="radio"] > div:first-child,
            [data-testid="stSidebar"] [role="radiogroup"] input[type="radio"] {
                display: none !important;
            }

            .sidebar-brand {
                position: fixed;
                left: 30px;
                bottom: 20px;
                width: 160px;
                padding: 5px;
                background: #FFFFFF;
            }
            .sidebar-brand img {
                display: block;
                width: 100%;
                height: auto;
                object-fit: contain;
            }

            h1, h2, h3, h4 { letter-spacing: -0.025em; color: #111216; }
            h1 { font-size: 2rem !important; margin: 0 0 0.2rem !important; }
            h2 { font-size: 1.3rem !important; margin-top: 0.3rem !important; }
            h3 { font-size: 1.08rem !important; }

            .page-purpose {
                color: #7A808B;
                font-size: 0.88rem;
                margin-bottom: 1.25rem;
            }
            .section-title {
                font-size: 1rem;
                font-weight: 700;
                margin: 0 0 0.65rem;
            }
            .section-caption {
                color: #7A808B;
                font-size: 0.78rem;
                margin: -0.35rem 0 0.65rem;
            }

            .metric-card {
                min-height: 111px;
                border-radius: var(--radius-lg);
                padding: 1.1rem 1.2rem;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                border: 1px solid rgba(16, 24, 40, 0.012);
            }
            .metric-label { font-size: 0.86rem; color: #22252B; }
            .metric-value {
                margin-top: 0.55rem;
                font-size: 1.72rem;
                line-height: 1;
                font-weight: 760;
                letter-spacing: -0.035em;
            }
            .metric-caption {
                margin-top: 0.45rem;
                color: #707783;
                font-size: 0.73rem;
                line-height: 1.35;
            }

            .st-key-maturity_score_card {
                min-height: 111px;
                border-radius: var(--radius-lg);
                padding: 1.1rem 1.2rem 0.85rem;
                background: #E7F1FD;
                border: 1px solid rgba(16, 24, 40, 0.012);
                box-sizing: border-box;
            }
            .st-key-maturity_score_card > div[data-testid="stVerticalBlock"] {
                gap: 0 !important;
            }
            .st-key-maturity_score_card .metric-value {
                margin: 0.55rem 0 0.42rem;
            }
            .st-key-view_maturity_score { margin: 0 !important; }
            .st-key-view_maturity_score button {
                min-height: auto !important;
                height: auto !important;
                padding: 0 !important;
                border: 0 !important;
                background: transparent !important;
                box-shadow: none !important;
                color: #365F9D !important;
                font-size: 0.75rem !important;
                font-weight: 650 !important;
                text-decoration: underline;
                text-underline-offset: 2px;
                justify-content: flex-start !important;
            }
            .st-key-view_maturity_score button:hover {
                color: #1F477F !important;
            }
            .st-key-view_maturity_score button:focus:not(:active) {
                box-shadow: 0 0 0 2px rgba(54, 95, 157, 0.2) !important;
            }

            .rubric-intro {
                color: #646B76;
                font-size: 0.86rem;
                margin: -0.15rem 0 0.9rem;
            }
            .rubric-table {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
                font-size: 0.9rem;
                color: #20232A;
            }
            .rubric-table th {
                padding: 0.66rem 0.75rem;
                text-align: left;
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.035em;
                border-bottom: 1px solid #AEB3BC;
            }
            .rubric-table th:first-child,
            .rubric-table td:first-child {
                width: 80px;
                text-align: center;
                font-weight: 750;
                border-right: 1px solid #C7CAD0;
            }
            .rubric-table td {
                padding: 0.62rem 0.75rem;
                vertical-align: top;
                line-height: 1.42;
                border-bottom: 1px solid #ECEEF1;
            }
            .rubric-table tbody tr:nth-child(odd) td { background: #F4F4F5; }
            .rubric-table tbody tr:last-child td { border-bottom: 0; }

            .insight-card {
                border-radius: 18px;
                padding: 0.95rem 1.05rem;
                margin-bottom: 0.7rem;
                border: 1px solid rgba(16, 24, 40, 0.02);
            }
            .insight-title {
                color: #6B7280;
                font-size: 0.72rem;
                font-weight: 750;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }
            .insight-value {
                margin-top: 0.32rem;
                font-size: 1.05rem;
                font-weight: 740;
            }
            .insight-text {
                margin-top: 0.3rem;
                color: #5E6570;
                font-size: 0.8rem;
                line-height: 1.45;
            }

            .action-card {
                background: #FBFBFC;
                border: 1px solid #ECEEF1;
                border-radius: 17px;
                padding: 0.9rem 1rem;
                margin-bottom: 0.62rem;
            }
            .action-header {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 0.8rem;
            }
            .action-title {
                font-size: 0.9rem;
                line-height: 1.4;
                font-weight: 720;
                color: #20232A;
            }
            .action-reason {
                color: #646B76;
                font-size: 0.78rem;
                line-height: 1.5;
                margin-top: 0.36rem;
            }
            .action-formula {
                color: #7A808A;
                font-size: 0.7rem;
                margin-top: 0.36rem;
            }

            .pill {
                display: inline-block;
                border-radius: 999px;
                padding: 0.24rem 0.55rem;
                font-size: 0.68rem;
                font-weight: 750;
                white-space: nowrap;
            }
            .pill-high { background: #FBE4E4; color: #A62A2A; }
            .pill-medium { background: #FFF0D5; color: #925800; }
            .pill-low { background: #E5F5ED; color: #176E49; }
            .pill-neutral { background: #EEF0F4; color: #515864; }

            .detail-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.7rem;
            }
            .detail-item {
                border-radius: 15px;
                background: rgba(255, 255, 255, 0.68);
                border: 1px solid #EDEEF1;
                padding: 0.84rem 0.9rem;
                min-height: 82px;
            }
            .detail-label {
                color: #707783;
                font-size: 0.68rem;
                font-weight: 750;
                text-transform: uppercase;
                letter-spacing: 0.02em;
                margin-bottom: 0.15rem;
            }
            .detail-value {
                color: #272B32;
                font-size: 0.8rem;
                line-height: 1.48;
                overflow-wrap: anywhere;
            }

            .summary-chip {
                display: inline-block;
                padding: 0.32rem 0.62rem;
                border-radius: 999px;
                background: #F0F1F4;
                color: #515762;
                font-size: 0.74rem;
                margin: 0 0.28rem 0.4rem 0;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
                border-radius: var(--radius-lg) !important;
                border-color: #ECEEF1 !important;
                background: #FAFAFB;
                overflow: hidden;
            }

            __PAGE_CARD_RULES__

            .st-key-evidence_quality_level_card,
            .st-key-quality_meaning_card {
                background: rgba(255, 255, 255, 0.72) !important;
                border: 1px solid #E5E7EB;
                border-radius: 18px;
                min-height: 7.2rem;
            }
            .st-key-evidence_quality_level_card [data-testid="stButton"] button {
                min-height: auto;
                padding: 0;
                border: 0;
                background: transparent;
                color: #1558B0;
                font-size: 0.82rem;
                font-weight: 650;
                text-decoration: underline;
            }
            .st-key-evidence_quality_level_card [data-testid="stButton"] button:hover {
                color: #0F3F82;
                background: transparent;
            }

            .st-key-executive_filters,
            .st-key-library_filters,
            .st-key-domain_filters,
            .st-key-comparison_filters,
            .st-key-gap_filters,
            .st-key-evidence_filters,
            .st-key-checker_filters {
                background: #F8F8FA;
                border: 1px solid #ECEEF1;
                border-radius: 18px;
                padding: 0.62rem 0.78rem 0.18rem;
                margin-bottom: 1rem;
                width: 100%;
            }
            .st-key-executive_filters {
                max-width: 500px;
                margin-right: auto;
            }
            .st-key-library_filters,
            .st-key-comparison_filters,
            .st-key-gap_filters,
            .st-key-evidence_filters,
            .st-key-checker_filters { max-width: 1180px; }
            .st-key-domain_filters { max-width: 760px; }

            .stSelectbox [data-baseweb="select"],
            .stMultiSelect [data-baseweb="select"],
            .stTextInput input,
            .stTextArea textarea {
                border-radius: 11px !important;
                border-color: #E0E2E7 !important;
                background: #FFFFFF !important;
            }
            .stButton button {
                border-radius: 11px !important;
                min-height: 38px;
                font-weight: 650;
                border-color: #DDE0E5;
            }
            [data-testid="stDataFrame"] {
                border: 1px solid #E8E9ED;
                border-radius: 15px;
                overflow: hidden;
            }
            [data-testid="stPlotlyChart"] { border-radius: 18px; }

            @media (max-width: 980px) {
                section[data-testid="stSidebar"],
                section[data-testid="stSidebar"] > div:first-child,
                [data-testid="stSidebarContent"] {
                    width: 250px !important;
                    min-width: 250px !important;
                    max-width: 250px !important;
                    flex-basis: 250px !important;
                }
                .detail-grid { grid-template-columns: 1fr; }
                [data-testid="stMainBlockContainer"] { padding: 2rem 1rem 3rem; }
            }
        </style>
    """
    st.markdown(
        css.replace("__PAGE_CARD_RULES__", _page_card_css()),
        unsafe_allow_html=True,
    )


def render_sidebar() -> str:
    selected = st.sidebar.radio(
        "Dashboard navigation",
        NAVIGATION_ITEMS,
        label_visibility="collapsed",
        key="main_navigation",
    )

    st.sidebar.markdown(
        f"""
        <div class="sidebar-brand">
            <img src="{image_data_uri(LOGO_FILE)}" alt="KACST logo" />
        </div>
        """,
        unsafe_allow_html=True,
    )
    return selected


def page_header(title: str, purpose: str) -> None:
    st.markdown(f"<h1>{html.escape(title)}</h1>", unsafe_allow_html=True)
    if purpose:
        st.markdown(
            f"<div class='page-purpose'>{html.escape(purpose)}</div>",
            unsafe_allow_html=True,
        )


def section_header(title: str, caption: str | None = None) -> None:
    st.markdown(
        f"<div class='section-title'>{html.escape(title)}</div>",
        unsafe_allow_html=True,
    )
    if caption:
        st.markdown(
            f"<div class='section-caption'>{html.escape(caption)}</div>",
            unsafe_allow_html=True,
        )


def maturity_scale(rubric: Mapping[int, str]) -> None:
    rows = "".join(
        f"<tr><td>{score}</td><td>{html.escape(description)}</td></tr>"
        for score, description in rubric.items()
    )
    st.markdown(
        f"""
        <table class="rubric-table">
            <thead><tr><th>Score</th><th>Meaning</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def metric_card(
    label: str,
    value: str,
    caption: str = "",
    background: str = "#F7F7F9",
) -> None:
    st.markdown(
        f"""
        <div class="metric-card" style="background:{background}">
            <div class="metric-label">{html.escape(label)}</div>
            <div class="metric-value">{html.escape(value)}</div>
            <div class="metric-caption">{html.escape(caption)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(
    title: str,
    value: str,
    text: str,
    background: str = "#F8F8FA",
) -> None:
    st.markdown(
        f"""
        <div class="insight-card" style="background:{background}">
            <div class="insight-title">{html.escape(title)}</div>
            <div class="insight-value">{html.escape(value)}</div>
            <div class="insight-text">{html.escape(text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def action_card(
    title: str,
    explanation: str,
    priority: str,
    formula: str | None = None,
) -> None:
    priority_clean = priority if priority in {"High", "Medium", "Low"} else "Low"
    formula_html = (
        f"<div class='action-formula'>Priority logic: {html.escape(formula)}</div>"
        if formula
        else ""
    )
    st.markdown(
        f"""
        <div class="action-card">
            <div class="action-header">
                <div class="action-title">{html.escape(title)}</div>
                <span class="pill pill-{priority_clean.lower()}">{priority_clean} priority</span>
            </div>
            <div class="action-reason">{html.escape(explanation)}</div>
            {formula_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def detail_grid(items: Sequence[tuple[str, object]]) -> None:
    blocks = [
        "<div class='detail-item'>"
        f"<div class='detail-label'>{html.escape(label)}</div>"
        f"<div class='detail-value'>{_safe(value)}</div>"
        "</div>"
        for label, value in items
    ]
    st.markdown(
        "<div class='detail-grid'>" + "".join(blocks) + "</div>",
        unsafe_allow_html=True,
    )


def summary_chips(items: Iterable[str]) -> None:
    html_items = "".join(
        f"<span class='summary-chip'>{html.escape(str(item))}</span>" for item in items
    )
    st.markdown(html_items, unsafe_allow_html=True)


def dataframe_selection_rows(event: object) -> list[int]:
    try:
        return list(event.selection.rows)
    except (AttributeError, KeyError, TypeError):
        try:
            return list(event.get("selection", {}).get("rows", []))
        except (AttributeError, TypeError):
            return []


def plotly_selected_customdata(event: object) -> list[object]:
    try:
        points = event.selection.points
    except (AttributeError, KeyError, TypeError):
        try:
            points = event.get("selection", {}).get("points", [])
        except (AttributeError, TypeError):
            points = []

    values: list[object] = []
    for point in points or []:
        custom = (
            point.get("customdata")
            if isinstance(point, dict)
            else getattr(point, "customdata", None)
        )
        if isinstance(custom, (list, tuple)) and custom:
            values.append(custom[0])
        elif custom is not None:
            values.append(custom)
    return values
