from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..config import (
    DOMAIN_COLORS,
    DOMAIN_DISPLAY,
    HIGH_PRIORITY_MIN,
    PLOTLY_CONFIG,
)
from ..scoring import recommendation_explanation
from ..ui import action_card, page_header, section_header


def _bounded_scores(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    limits = {
        "current_score": 5,
        "gap_score": 5,
        "evidence_quality_score": 4,
        "priority_score": 5,
    }
    for column, maximum in limits.items():
        result[column] = (
            pd.to_numeric(result[column], errors="coerce")
            .fillna(0)
            .clip(lower=0, upper=maximum)
        )
    return result


def _project_summary(df: pd.DataFrame) -> pd.DataFrame:
    scored = _bounded_scores(df)
    summary = (
        scored.groupby(["project_id", "project_name", "domain"], as_index=False)
        .agg(
            maturity_score=("current_score", "mean"),
            applicable_indicators=("indicator_id", "nunique"),
            gap_severity=("gap_score", "mean"),
            evidence_confidence=("evidence_quality_score", "mean"),
            priority_gaps=(
                "priority_score",
                lambda values: int((values >= HIGH_PRIORITY_MIN).sum()),
            ),
        )
        .sort_values("maturity_score", ascending=False)
        .reset_index(drop=True)
    )
    summary[["maturity_score", "gap_severity", "evidence_confidence"]] = summary[
        ["maturity_score", "gap_severity", "evidence_confidence"]
    ].round(1)
    summary["applicable_indicators"] = summary["applicable_indicators"].astype(int)
    summary["priority_gaps"] = summary["priority_gaps"].astype(int)
    return summary


def _wrap_label(text: str, width: int = 22) -> str:
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "<br>".join(lines)


def _comparison_chart(summary: pd.DataFrame) -> None:
    colors = [DOMAIN_COLORS.get(domain, "#8FA7C7") for domain in summary["domain"]]
    labels = summary["project_name"].map(_wrap_label)
    display_domains = summary["domain"].map(DOMAIN_DISPLAY).fillna(summary["domain"])
    hover_data = pd.DataFrame(
        {
            "project_name": summary["project_name"],
            "domain": display_domains,
        }
    ).to_numpy()

    fig = go.Figure()

    # Plotly does not create separate legend entries for colors inside one bar trace,
    # so add marker-only traces to explain the domain color mapping.
    domains_in_chart = set(summary["domain"].dropna().astype(str))
    ordered_domains = [
        domain for domain in DOMAIN_DISPLAY if domain in domains_in_chart
    ]
    ordered_domains.extend(
        sorted(domains_in_chart.difference(ordered_domains))
    )
    for domain in ordered_domains:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker={
                    "color": DOMAIN_COLORS.get(domain, "#8FA7C7"),
                    "size": 10,
                    "symbol": "square",
                },
                name=f"{DOMAIN_DISPLAY.get(domain, domain)} domain",
                hoverinfo="skip",
                showlegend=True,
            )
        )

    fig.add_trace(
        go.Bar(
            x=labels,
            y=summary["maturity_score"],
            name="Project maturity score",
            marker_color=colors,
            text=summary["maturity_score"].map(lambda value: f"{value:.1f}/5"),
            textposition="outside",
            customdata=hover_data,
            hovertemplate=(
                "%{customdata[0]}<br>Domain: %{customdata[1]}"
                "<br>Project maturity: %{y:.1f}/5<extra></extra>"
            ),
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Bar(
            x=labels,
            y=summary["gap_severity"],
            name="Gap severity",
            marker_color="#D9DCE3",
            text=summary["gap_severity"].map(lambda value: f"{value:.1f}/5"),
            textposition="outside",
            customdata=summary[["project_name"]].to_numpy(),
            hovertemplate="%{customdata[0]}<br>Gap severity: %{y:.1f}/5<extra></extra>",
        )
    )
    fig.update_layout(
        height=430,
        barmode="group",
        margin={"l": 20, "r": 15, "t": 55, "b": 90},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Segoe UI, Arial", "color": "#606772", "size": 11},
        legend={"orientation": "h", "x": 0, "y": 1.13},
        xaxis={
            "title": None,
            "type": "category",
            "tickangle": 0,
            "automargin": True,
            "tickfont": {"size": 10},
        },
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


def _summary_table(summary: pd.DataFrame) -> None:
    display = summary[
        [
            "project_name",
            "maturity_score",
            "applicable_indicators",
            "gap_severity",
            "evidence_confidence",
            "priority_gaps",
        ]
    ].rename(
        columns={
            "project_name": "Project",
            "maturity_score": "Project maturity score",
            "applicable_indicators": "Applicable indicators",
            "gap_severity": "Gap severity",
            "evidence_confidence": "Evidence confidence",
            "priority_gaps": "Priority gaps",
        }
    )
    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        column_config={
            "Project": st.column_config.TextColumn(width="large"),
            "Project maturity score": st.column_config.ProgressColumn(
                min_value=0, max_value=5, format="%.1f / 5", width="medium"
            ),
            "Applicable indicators": st.column_config.NumberColumn(
                format="%d", width="small"
            ),
            "Gap severity": st.column_config.ProgressColumn(
                min_value=0, max_value=5, format="%.1f / 5", width="medium"
            ),
            "Evidence confidence": st.column_config.ProgressColumn(
                min_value=0, max_value=4, format="%.1f / 4", width="medium"
            ),
            "Priority gaps": st.column_config.NumberColumn(
                format="%d", width="small"
            ),
        },
    )


def _recommended_actions(df: pd.DataFrame, project_name: str) -> None:
    rows = df[df["project_name"] == project_name].copy()
    rows = rows[
        rows["recommended_action"].fillna("").astype(str).str.strip().ne("")
    ].sort_values(
        ["priority_score", "gap_score", "evidence_quality_score"],
        ascending=[False, False, True],
    ).drop_duplicates("recommended_action")

    if rows.empty:
        st.info("No recommended actions are available for this project.")
        return

    for _, row in rows.head(5).iterrows():
        explanation = recommendation_explanation(row)
        benefit = str(row.get("expected_benefit", "")).strip()
        if benefit:
            explanation = f"{explanation} Expected benefit: {benefit}"
        action_card(
            title=str(row["recommended_action"]),
            explanation=explanation,
            priority=str(row.get("priority_level", "Low")),
            formula=str(row.get("priority_breakdown", "Priority score = gap severity")),
        )


def render(data: dict[str, pd.DataFrame]) -> None:
    page_header("Project Comparison", "Compare sample smart city projects.")
    dashboard = _bounded_scores(data["dashboard"].copy())
    if dashboard.empty:
        st.warning("No project assessment data is available.")
        return

    available_domains = [
        domain
        for domain in DOMAIN_DISPLAY
        if domain in set(dashboard["domain"].dropna().astype(str))
    ]
    available_domains.extend(
        sorted(
            set(dashboard["domain"].dropna().astype(str)).difference(available_domains)
        )
    )

    with st.container(key="comparison_filters"):
        domain_column, project_column = st.columns([1, 2], gap="medium")
        with domain_column:
            selected_domains = st.multiselect(
                "Domains",
                options=available_domains,
                default=available_domains,
                format_func=lambda domain: DOMAIN_DISPLAY.get(domain, domain),
                help="Filter the projects by one or more smart city domains.",
                key="comparison_domain_filter",
            )

        if not selected_domains:
            st.info("Select at least one domain to view its projects.")
            return

        domain_filtered = dashboard[dashboard["domain"].isin(selected_domains)].copy()
        project_names = sorted(
            domain_filtered["project_name"].dropna().unique().tolist()
        )

        # Remove projects that are no longer available after changing the domain filter.
        project_filter_key = "comparison_project_filter"
        if project_filter_key in st.session_state:
            current_selection = st.session_state[project_filter_key]
            if isinstance(current_selection, list):
                st.session_state[project_filter_key] = [
                    project
                    for project in current_selection
                    if project in project_names
                ]

        with project_column:
            project_filter_options = {
                "label": "Projects to compare",
                "options": project_names,
                "help": "Select one or more projects from the chosen domains.",
                "key": project_filter_key,
            }
            if project_filter_key not in st.session_state:
                project_filter_options["default"] = project_names[:4]
            selected_projects = st.multiselect(**project_filter_options)

    if not selected_projects:
        st.info("Select at least one project to view the comparison.")
        return

    filtered = domain_filtered[
        domain_filtered["project_name"].isin(selected_projects)
    ].copy()
    summary = _project_summary(filtered)

    st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        section_header(
            "Project comparison",
            (
                "Project maturity use 0-5 scale for Current maturity and Target = 5, "
                "Gap = Target maturity – Current maturity"
            ),
        )
        _comparison_chart(summary)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        section_header(
            "Project comparison summary",
            "Evidence confidence is shown directly on the 0-4 evidence-quality rubric.",
        )
        _summary_table(summary)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        section_header("Recommended actions")
        selected_action_project = st.selectbox(
            "Project",
            options=summary["project_name"].tolist(),
            key="comparison_action_project",
        )
        _recommended_actions(filtered, selected_action_project)
