from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..config import (
    CARD_BACKGROUNDS,
    DOMAIN_DISPLAY,
    MATURITY_RUBRIC,
    PLOTLY_CONFIG,
    WEAK_MATURITY_MAX,
)
from ..scoring import bounded_average
from ..ui import metric_card, page_header, section_header


@st.dialog("Maturity score rubric", width="large")
def _show_maturity_score_rubric() -> None:
    rows = "".join(
        f"<tr><td>{score}</td><td>{meaning}</td></tr>"
        for score, meaning in MATURITY_RUBRIC.items()
    )
    st.markdown(
        f"""
        <div class="rubric-intro">
            Use the following 0–5 scale to interpret maturity scores.
        </div>
        <table class="maturity-rubric-table">
            <thead>
                <tr><th>Score</th><th>Meaning</th></tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


@st.dialog("Score Rubric", width="large")
def _show_score_rubric() -> None:
    maturity_rows = "".join(
        f"<tr><td>{score}</td><td>{meaning}</td></tr>"
        for score, meaning in MATURITY_RUBRIC.items()
    )
    evidence_rows = "".join(
        [
            "<tr><td>0</td><td>No evidence</td><td>No source or supporting material available</td></tr>",
            "<tr><td>1</td><td>Weak evidence</td><td>General description, announcement, or unsupported claim</td></tr>",
            "<tr><td>2</td><td>Moderate evidence</td><td>Public document, project page, report, or dataset reference</td></tr>",
            "<tr><td>3</td><td>Strong evidence</td><td>Measured data, dashboard, API, evaluation report, or official document</td></tr>",
            "<tr><td>4</td><td>Verified evidence</td><td>Evidence reviewed by expert, stakeholder, or project owner</td></tr>",
        ]
    )
    readiness_rows = "".join(
        [
            "<tr><td>0</td><td>No data</td><td>There is no source at all, not even a manual one.</td></tr>",
            "<tr><td>1</td><td>Unstructured data</td><td>Data exists but is stored in unstructured format, requires manual extraction or cleaning before it can be used (PDFs, paper records, manual documents)</td></tr>",
            "<tr><td>2</td><td>Structured but static</td><td>Data exists in a usable structured format but isn’t updated frequently, it does not refresh on its own (database snapshots, spreadsheets)</td></tr>",
            "<tr><td>3</td><td>Structured and live</td><td>Data exists in a usable format and is updated frequently (APIs, automatically updated systems)</td></tr>",
        ]
    )

    st.markdown(
        f"""
        <style>
            .score-rubric-heading {{
                margin: 1.35rem 0 0.55rem;
                font-size: 1.2rem;
                font-weight: 700;
                color: #111827;
            }}
            .score-rubric-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 0.8rem;
                font-size: 0.92rem;
            }}
            .score-rubric-table th {{
                text-align: left;
                padding: 0.55rem 0.65rem;
                border-bottom: 1px solid #AEB3BC;
                text-transform: uppercase;
            }}
            .score-rubric-table td {{
                padding: 0.5rem 0.65rem;
                vertical-align: top;
                border-right: 1px solid #C9CDD4;
            }}
            .score-rubric-table td:first-child {{
                width: 70px;
                text-align: center;
                font-weight: 700;
            }}
            .score-rubric-table td:last-child {{
                border-right: none;
            }}
            .score-rubric-table tbody tr:nth-child(odd) {{
                background: #F2F2F2;
            }}
            .gap-rubric {{
                padding: 0.25rem 0 0.5rem;
                line-height: 1.55;
            }}
        </style>

        <div class="score-rubric-heading">Maturity Score Rubric</div>
        <table class="score-rubric-table">
            <thead><tr><th>Score</th><th>Meaning</th></tr></thead>
            <tbody>{maturity_rows}</tbody>
        </table>

        <div class="score-rubric-heading">Evidence Quality Score Rubric</div>
        <table class="score-rubric-table">
            <thead><tr><th>Score</th><th>Evidence Quality</th><th>Meaning</th></tr></thead>
            <tbody>{evidence_rows}</tbody>
        </table>

        <div class="score-rubric-heading">Data Readiness Rubric</div>
        <table class="score-rubric-table">
            <thead><tr><th>Level</th><th></th><th>Meaning</th></tr></thead>
            <tbody>{readiness_rows}</tbody>
        </table>

        <div class="score-rubric-heading">Gap Severity Calculation</div>
        <div class="gap-rubric">
            The gap severity calculates how far the project is from the desired/target maturity.
            To calculate the gap, subtract the current maturity score from the target maturity.
            <br><br>
            <strong>Gap severity = Target maturity − Current maturity</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _maturity_score_card(value: str) -> None:
    with st.container(key="maturity_score_card"):
        st.markdown(
            f"""
            <div class="metric-label">Domain-level maturity scores</div>
            <div class="metric-value">{value}</div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            "View maturity score",
            key="view_maturity_score",
            type="tertiary",
        ):
            _show_maturity_score_rubric()


def _bounded_scores(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    limits = {
        "current_score": 5,
        "gap_score": 5,
        "evidence_quality_score": 4,
        "data_readiness_score": 3,
    }
    for column, maximum in limits.items():
        result[column] = (
            pd.to_numeric(result[column], errors="coerce")
            .fillna(0)
            .clip(lower=0, upper=maximum)
        )
    return result


def _domain_summary(df: pd.DataFrame) -> pd.DataFrame:
    scored = _bounded_scores(df)
    summary = (
        scored.groupby("domain", as_index=False)
        .agg(
            maturity_score=("current_score", "mean"),
            gap_score=("gap_score", "mean"),
            evidence_quality=("evidence_quality_score", "mean"),
            data_readiness=("data_readiness_score", "mean"),
        )
        .sort_values("maturity_score", ascending=False)
        .reset_index(drop=True)
    )
    score_columns = [
        "maturity_score",
        "gap_score",
        "evidence_quality",
        "data_readiness",
    ]
    summary[score_columns] = summary[score_columns].round(1)
    summary["display_domain"] = (
        summary["domain"].map(DOMAIN_DISPLAY).fillna(summary["domain"])
    )
    return summary


def _maturity_gap_chart(summary: pd.DataFrame) -> None:
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=summary["display_domain"],
            y=summary["maturity_score"],
            name="Maturity score (0-5)",
            marker_color="#5BFE7E",
            text=summary["maturity_score"].map(lambda value: f"{value:.1f}/5"),
            textposition="outside",
            hovertemplate="%{x}<br>Maturity score: %{y:.1f}/5<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=summary["display_domain"],
            y=summary["gap_score"],
            name="Gap severity (0-5)",
            marker_color="#D9DCE3",
            text=summary["gap_score"].map(lambda value: f"{value:.1f}/5"),
            textposition="outside",
            hovertemplate="%{x}<br>Gap severity: %{y:.1f}/5<extra></extra>",
        )
    )
    fig.update_layout(
        height=380,
        barmode="group",
        margin={"l": 20, "r": 15, "t": 50, "b": 70},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Segoe UI, Arial", "color": "#606772", "size": 11},
        legend={"orientation": "h", "x": 0, "y": 1.13},
        xaxis={"title": None, "automargin": True},
        yaxis={
            "range": [0, 5.5],
            "dtick": 1,
            "gridcolor": "#ECEEF2",
            "zeroline": False,
        },
        bargap=0.28,
        bargroupgap=0.08,
    )
    st.plotly_chart(fig, width="stretch", theme=None, config=PLOTLY_CONFIG)


def _evidence_readiness_chart(summary: pd.DataFrame) -> None:
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=summary["display_domain"],
            y=summary["evidence_quality"],
            name="Evidence quality (0-4)",
            marker_color="#8FB4E8",
            text=summary["evidence_quality"].map(lambda value: f"{value:.1f}/4"),
            textposition="outside",
            hovertemplate="%{x}<br>Evidence quality: %{y:.1f}/4<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=summary["display_domain"],
            y=summary["data_readiness"],
            name="Data readiness (0-3)",
            marker_color="#AA8CE5",
            text=summary["data_readiness"].map(lambda value: f"{value:.1f}/3"),
            textposition="outside",
            hovertemplate="%{x}<br>Data readiness: %{y:.1f}/3<extra></extra>",
        )
    )
    fig.update_layout(
        height=380,
        barmode="group",
        margin={"l": 20, "r": 15, "t": 50, "b": 70},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Segoe UI, Arial", "color": "#606772", "size": 11},
        legend={"orientation": "h", "x": 0, "y": 1.13},
        xaxis={"title": None, "automargin": True},
        yaxis={
            "range": [0, 4.5],
            "dtick": 1,
            "gridcolor": "#ECEEF2",
            "zeroline": False,
        },
        bargap=0.28,
        bargroupgap=0.08,
    )
    st.plotly_chart(fig, width="stretch", theme=None, config=PLOTLY_CONFIG)


def _weak_indicators_table(df: pd.DataFrame) -> None:
    weak = df[df["current_score"] <= WEAK_MATURITY_MAX].copy()
    if weak.empty:
        st.success("No indicators have a maturity score of 2/5 or below.")
        return

    weak["Domain"] = weak["domain"].map(DOMAIN_DISPLAY).fillna(weak["domain"])
    weak = weak.sort_values(
        ["domain", "current_score", "gap_score", "indicator_name"],
        ascending=[True, True, False, True],
    )
    display = weak[
        [
            "Domain",
            "project_name",
            "indicator_name",
            "current_score",
            "gap_score",
            "evidence_quality_score",
            "data_readiness_score",
        ]
    ].rename(
        columns={
            "project_name": "Project",
            "indicator_name": "Weak indicator",
            "current_score": "Maturity",
            "gap_score": "Gap severity",
            "evidence_quality_score": "Evidence quality",
            "data_readiness_score": "Data readiness",
        }
    )
    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        height=min(450, 85 + 35 * len(display)),
        column_config={
            "Domain": st.column_config.TextColumn(width="medium"),
            "Project": st.column_config.TextColumn(width="large"),
            "Weak indicator": st.column_config.TextColumn(width="large"),
            "Maturity": st.column_config.NumberColumn(format="%.1f / 5"),
            "Gap severity": st.column_config.NumberColumn(format="%.1f / 5"),
            "Evidence quality": st.column_config.NumberColumn(format="%.1f / 4"),
            "Data readiness": st.column_config.NumberColumn(format="%.1f / 3"),
        },
    )


def render(data: dict[str, pd.DataFrame]) -> None:
    page_header("Domain Maturity View", "Compare maturity across domains.")
    dashboard = _bounded_scores(data["dashboard"].copy())
    if dashboard.empty:
        st.warning("No domain assessment data is available.")
        return

    summary = _domain_summary(dashboard)
    metrics = st.columns(4, gap="medium")
    with metrics[0]:
        _maturity_score_card(
            f"{bounded_average(dashboard['current_score'], 5):.1f}/5"
        )
    with metrics[1]:
        metric_card(
            "Domain-level gap scores",
            f"{bounded_average(dashboard['gap_score'], 5):.1f}/5",
            "Target maturity minus current maturity.",
            CARD_BACKGROUNDS["gray"],
        )

        

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        with st.container(border=True):
            section_header(
                "Domain maturity and gap severity",
                "Both measures use the 0-5 scale.",
            )
            _maturity_gap_chart(summary)
    with chart_right:
        with st.container(border=True):
            section_header(
                "Evidence quality and data readiness by domain",
                "Evidence Quality uses 0-4; Data Readiness uses 0-3.",
            )
            _evidence_readiness_chart(summary)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        section_header(
            "Weak indicators by domain",
            "Indicators with maturity of 2/5 or below.",
        )
        st.markdown(
            """
            <style>
                .st-key-weak_score_rubric_link {
                    margin: 0.15rem 0 0.75rem !important;
                }
                .st-key-weak_score_rubric_link div[data-testid="stButton"] > button {
                    color: #1558B0 !important;
                    background: transparent !important;
                    border: none !important;
                    box-shadow: none !important;
                    padding: 0 !important;
                    min-height: 0 !important;
                    height: auto !important;
                    font-weight: 600 !important;
                    text-decoration: underline !important;
                }
                .st-key-weak_score_rubric_link div[data-testid="stButton"] > button p {
                    color: #1558B0 !important;
                    font-weight: 600 !important;
                    text-decoration: underline !important;
                }
                .st-key-weak_score_rubric_link div[data-testid="stButton"] > button:hover,
                .st-key-weak_score_rubric_link div[data-testid="stButton"] > button:hover p {
                    color: #0D3F82 !important;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        with st.container(key="weak_score_rubric_link"):
            if st.button(
                "Score Rubric",
                key="weak_score_rubric_button",
                type="secondary",
            ):
                _show_score_rubric()
        _weak_indicators_table(dashboard)
