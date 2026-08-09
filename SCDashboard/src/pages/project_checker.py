from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from ..config import DOMAIN_DISPLAY
from ..database import save_project_submission
from ..ui import page_header, section_header


_DISPLAY_TO_DOMAIN = {display: domain for domain, display in DOMAIN_DISPLAY.items()}
_STATUS_LEVEL = {
    "Not implemented": 0,
    "Planning": 1,
    "Partially implemented, but limited coverage": 2,
    "Implemented and operational, but needs further improvement": 3,
    "Implemented with good performance": 4,
    "Fully implemented, optimized, and continuously improved": 5,
}


def _tokens(text: object) -> set[str]:
    if text is None or pd.isna(text):
        return set()
    return {
        token
        for token in re.findall(r"[a-z0-9]+", str(text).lower())
        if len(token) >= 3
    }


def _relevant_indicators(
    standards: pd.DataFrame,
    domain: str,
    technology_used: str,
    data_sources: str,
    target_users: str,
    expected_impact: str,
    available_evidence: str,
) -> pd.DataFrame:
    candidates = standards[standards["domain"] == domain].copy()
    if candidates.empty:
        return candidates

    query_tokens = _tokens(
        " ".join(
            [
                technology_used,
                data_sources,
                target_users,
                expected_impact,
                available_evidence,
            ]
        )
    )

    def score_row(row: pd.Series) -> int:
        searchable = " ".join(
            str(row.get(column, ""))
            for column in [
                "project_type_tags",
                "subdomain",
                "indicator_name",
                "indicator_definition",
                "required_data",
                "required_evidence",
            ]
        )
        return len(query_tokens.intersection(_tokens(searchable)))

    candidates["relevance_score"] = candidates.apply(score_row, axis=1)
    if candidates["relevance_score"].max() > 0:
        candidates = candidates[candidates["relevance_score"] > 0]

    return candidates.sort_values(
        ["relevance_score", "indicator_id"],
        ascending=[False, True],
    ).head(10)


def _possible_actions(
    dashboard: pd.DataFrame,
    domain: str,
    indicator_ids: list[str],
) -> pd.DataFrame:
    actions = dashboard[
        (dashboard["domain"] == domain)
        & dashboard["recommended_action"].fillna("").astype(str).str.strip().ne("")
    ].copy()

    if indicator_ids:
        matched = actions[actions["indicator_id"].isin(indicator_ids)]
        if not matched.empty:
            actions = matched

    return (
        actions.sort_values(
            ["priority_score", "gap_score"],
            ascending=[False, False],
        )
        .drop_duplicates("recommended_action")
        .head(5)
    )


def render(data: dict[str, pd.DataFrame]) -> None:
    page_header(
        "Project Checker",
        "Support early assessment of a new smart city project.",
    )

    standards = data["standards"].copy()
    dashboard = data["dashboard"].copy()

    with st.form("project_checker_form", clear_on_submit=False):
        with st.container(key="checker_filters"):
            project_name = st.text_input(
                "Project name *",
                placeholder="Example: Smart Parking Expansion",
            )
            display_domain = st.selectbox(
                "Domain *",
                list(_DISPLAY_TO_DOMAIN.keys()),
            )

        left_input, right_input = st.columns(2, gap="large")
        with left_input:
            technology_used = st.text_area(
                "Technology used",
                placeholder="IoT sensors, cameras, AI, mobile application...",
            )
            data_sources = st.text_area(
                "Data sources",
                placeholder="Sensors, databases, APIs, manual records...",
            )
            target_users = st.text_area(
                "Target users",
                placeholder="Citizens, operators, municipality staff...",
            )

        with right_input:
            expected_impact = st.text_area(
                "Expected impact",
                placeholder="Reduce congestion, improve service quality...",
            )
            current_status = st.selectbox(
                "Current status",
                list(_STATUS_LEVEL.keys()),
            )
            available_evidence = st.text_area(
                "Available evidence",
                placeholder="Reports, dashboards, APIs, datasets, official documents...",
            )

        submitted = st.form_submit_button(
            "Save this project profile",
            use_container_width=True,
        )

    if submitted:
        if not project_name.strip():
            st.error("Project name is required.")
            return

        domain = _DISPLAY_TO_DOMAIN[display_domain]
        relevant = _relevant_indicators(
            standards=standards,
            domain=domain,
            technology_used=technology_used,
            data_sources=data_sources,
            target_users=target_users,
            expected_impact=expected_impact,
            available_evidence=available_evidence,
        )
        actions = _possible_actions(
            dashboard=dashboard,
            domain=domain,
            indicator_ids=relevant["indicator_id"].tolist(),
        )

        try:
            submission_id = save_project_submission(
                project_name=project_name,
                domain=display_domain,
                project_type="",
                technology_used=technology_used,
                data_sources=data_sources,
                target_users=target_users,
                expected_impact=expected_impact,
                current_status=current_status,
                available_evidence=available_evidence,
            )
        except Exception as exc:
            st.error(f"The project could not be saved: {exc}")
            return

        st.session_state["checker_results"] = {
            "project_name": project_name,
            "domain": domain,
            "current_status": current_status,
            "relevant": relevant,
            "actions": actions,
        }
        st.success(f"Project saved and analyzed successfully. Submission ID: {submission_id}")

    results = st.session_state.get("checker_results")
    if not results:
        st.info("Complete the project profile and select Save this project profile to view results.")
        return

    relevant = results["relevant"]
    actions = results["actions"]
    starting_level = _STATUS_LEVEL.get(results["current_status"], 0)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    left, right = st.columns(2, gap="large")

    with left:
        with st.container(border=True):
            section_header("Relevant standards")
            if relevant.empty:
                st.info("No standards matched the project profile.")
            else:
                standards_display = (
                    relevant[["standard_source"]]
                    .drop_duplicates()
                    .rename(columns={"standard_source": "Standard"})
                )
                st.dataframe(standards_display, width="stretch", hide_index=True)

        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            section_header("Relevant indicators")
            if relevant.empty:
                st.info("No indicators matched the project profile.")
            else:
                st.dataframe(
                    relevant[
                        [
                            "indicator_id",
                            "indicator_name",
                            "subdomain",
                            "relevance_score",
                        ]
                    ].rename(
                        columns={
                            "indicator_id": "ID",
                            "indicator_name": "Indicator",
                            "subdomain": "Subdomain",
                            "relevance_score": "Match score",
                        }
                    ),
                    width="stretch",
                    hide_index=True,
                )

        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            section_header(
                "Possible priority actions",
                "Examples from assessed projects in the selected domain. Final priority requires project-specific scoring.",
            )
            if actions.empty:
                st.info("No example priority actions are available for this domain.")
            else:
                st.dataframe(
                    actions[
                        [
                            "indicator_id",
                            "indicator_name",
                            "recommended_action",
                            "priority_level",
                            "evidence_needed",
                        ]
                    ].rename(
                        columns={
                            "indicator_id": "ID",
                            "indicator_name": "Indicator",
                            "recommended_action": "Possible action",
                            "priority_level": "Priority",
                            "evidence_needed": "Evidence needed",
                        }
                    ),
                    width="stretch",
                    hide_index=True,
                )

    with right:
        with st.container(border=True):
            section_header("Required evidence")
            if relevant.empty:
                st.info("No evidence requirements are available.")
            else:
                st.dataframe(
                    relevant[
                        ["indicator_id", "indicator_name", "required_evidence"]
                    ].rename(
                        columns={
                            "indicator_id": "ID",
                            "indicator_name": "Indicator",
                            "required_evidence": "Required evidence",
                        }
                    ),
                    width="stretch",
                    hide_index=True,
                )

        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            section_header(
                "Initial maturity checklist",
                f"Suggested starting point from current status: {starting_level}/5. Review every indicator against the official 0-5 rubric.",
            )
            if relevant.empty:
                st.info("No checklist items are available.")
            else:
                checklist = relevant[
                    ["indicator_id", "indicator_name", "maturity_guidance"]
                ].copy()
                checklist["Starting level"] = starting_level
                checklist = checklist.rename(
                    columns={
                        "indicator_id": "ID",
                        "indicator_name": "Checklist indicator",
                        "maturity_guidance": "Scoring guidance",
                    }
                )
                st.dataframe(
                    checklist,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Starting level": st.column_config.NumberColumn(format="%d / 5")
                    },
                )
