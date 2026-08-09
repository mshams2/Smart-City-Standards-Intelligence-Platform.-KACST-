from __future__ import annotations

import pandas as pd
import streamlit as st

from ..config import DOMAIN_DISPLAY, LOW_EVIDENCE_MAX, MISSING_DATA_LEVEL
from ..scoring import high_impact_gap_label
from ..ui import page_header, section_header


def _filtered_dashboard(data: pd.DataFrame) -> pd.DataFrame:
    domains = sorted(data["domain"].dropna().unique().tolist())
    projects = sorted(data["project_name"].dropna().unique().tolist())
    with st.container(key="gap_filters"):
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            selected_domain = st.selectbox(
                "Domain",
                ["All domains", *domains],
                format_func=lambda value: (
                    value
                    if value == "All domains"
                    else DOMAIN_DISPLAY.get(value, value)
                ),
                key="gap_domain_filter",
            )
        with c2:
            selected_project = st.selectbox(
                "Project",
                ["All projects", *projects],
                key="gap_project_filter",
            )

    filtered = data.copy()
    if selected_domain != "All domains":
        filtered = filtered[filtered["domain"] == selected_domain]
    if selected_project != "All projects":
        filtered = filtered[filtered["project_name"] == selected_project]
    return filtered


def _display_gap_table(
    df: pd.DataFrame, max_rows: int = 15, show_impact_level: bool = True
) -> None:
    if df.empty:
        st.info("No matching indicators were found.")
        return
    view = df.head(max_rows).copy()
    view["Domain"] = view["domain"].map(DOMAIN_DISPLAY).fillna(view["domain"])
    view["Indicator"] = (
        view["indicator_id"].astype(str) + " - " + view["indicator_name"].astype(str)
    )
    columns = [
        "project_name",
        "Domain",
        "Indicator",
        "current_score",
        "target_score",
        "gap_score",
    ]
    column_config = {
        "Project": st.column_config.TextColumn(width="large"),
        "Domain": st.column_config.TextColumn(width="medium"),
        "Indicator": st.column_config.TextColumn(width="large"),
        "Current maturity": st.column_config.NumberColumn(format="%d / 5"),
        "Target maturity": st.column_config.NumberColumn(format="%d / 5"),
        "Gap severity": st.column_config.ProgressColumn(
            min_value=0, max_value=5, format="%d / 5"
        ),
        "Evidence quality": st.column_config.NumberColumn(format="%d / 4"),
        "Data readiness": st.column_config.NumberColumn(format="%d / 3"),
        "Priority": st.column_config.TextColumn(width="small"),
    }
    if show_impact_level:
        view["High impact gap"] = view["high_impact_gap"].map(high_impact_gap_label)
        columns.append("High impact gap")
        column_config["High impact gap"] = st.column_config.TextColumn(
            width="small",
            help="From the assessment file's High impact gap column.",
        )
    columns += ["evidence_quality_score", "data_readiness_score", "priority_level"]
    display = view[columns].rename(
        columns={
            "project_name": "Project",
            "current_score": "Current maturity",
            "target_score": "Target maturity",
            "gap_score": "Gap severity",
            "evidence_quality_score": "Evidence quality",
            "data_readiness_score": "Data readiness",
            "priority_level": "Priority",
        }
    )
    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        column_config=column_config,
    )


def _priority_action_table(df: pd.DataFrame) -> None:
    rows = df[
        df["recommended_action"].fillna("").astype(str).str.strip().ne("")
    ].sort_values(
        ["gap_score", "priority_score"], ascending=False
    ).drop_duplicates("recommended_action")

    if rows.empty:
        st.info("No data is available for the priority action table.")
        return

    rows = rows.copy()
    rows["Domain"] = rows["domain"].map(DOMAIN_DISPLAY).fillna(rows["domain"])
    rows["Indicator"] = (
        rows["indicator_id"].astype(str) + " - " + rows["indicator_name"].astype(str)
    )
    display = rows[
        ["project_name", "Domain", "Indicator", "gap_score", "priority_level"]
    ].rename(
        columns={
            "project_name": "Project",
            "gap_score": "Gap severity",
            "priority_level": "Priority level",
        }
    )
    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        column_config={
            "Project": st.column_config.TextColumn(width="large"),
            "Indicator": st.column_config.TextColumn(width="large"),
            "Gap severity": st.column_config.NumberColumn(format="%d / 5"),
            "Priority level": st.column_config.TextColumn(width="small"),
        },
    )


def render(data: dict[str, pd.DataFrame]) -> None:
    page_header("Gap Analysis", "Identify where improvement is most needed.")
    dashboard = data["dashboard"].copy()
    if dashboard.empty:
        st.warning("No assessment data is available.")
        return

    filtered = _filtered_dashboard(dashboard)
    if filtered.empty:
        st.info("No assessment records match the selected filters.")
        return

    left, right = st.columns(2, gap="large")

    with left:
        with st.container(border=True, key="gap_largest_card"):
            section_header(
                "Largest maturity gaps",
                "Indicators ranked by Target maturity - Current maturity.",
            )
            largest = filtered.sort_values(
                ["gap_score", "current_score"], ascending=[False, True]
            )
            _display_gap_table(largest, max_rows=2, show_impact_level=False)

        st.markdown(
            "<div style='height:0.8rem'></div>",
            unsafe_allow_html=True,
        )
        with st.container(border=True, key="gap_missing_card"):
            section_header(
                "Missing data indicators",
                "Indicators with Data Readiness level 0/3.",
            )
            missing_data = filtered[
                filtered["data_readiness_score"] == MISSING_DATA_LEVEL
            ].sort_values("gap_score", ascending=False)
            if missing_data.empty:
                st.success("No indicators have Data Readiness 0/3.")
            else:
                _display_gap_table(missing_data, max_rows=10)

        st.markdown(
            "<div style='height:0.8rem'></div>",
            unsafe_allow_html=True,
        )
        with st.container(border=True, key="gap_low_evidence_card"):
            section_header(
                "High-risk low-evidence indicators",
                "Indicators with a maturity gap and Evidence Quality of 1/4 or below.",
            )
            low_evidence = filtered[
                (filtered["gap_score"] > 0)
                & (filtered["evidence_quality_score"] <= LOW_EVIDENCE_MAX)
            ].sort_values(
                ["gap_score", "evidence_quality_score"],
                ascending=[False, True],
            )
            if low_evidence.empty:
                st.success("No high-risk low-evidence indicators were found.")
            else:
                _display_gap_table(low_evidence, max_rows=10)

    with right:
        with st.container(border=True, key="gap_high_impact_card"):
            section_header(
                "High-impact gaps",
            )
            high_impact = filtered[
                filtered["recommended_action"]
                .fillna("")
                .astype(str)
                .str.strip()
                .ne("")
            ].sort_values(
                ["gap_score", "priority_score"], ascending=False
            ).drop_duplicates("recommended_action")
            if high_impact.empty:
                st.info("No high-impact gap descriptions are available.")
            else:
                high_impact = high_impact.copy()
                high_impact["Indicator"] = (
                    high_impact["indicator_id"].astype(str)
                    + " - "
                    + high_impact["indicator_name"].astype(str)
                )
                high_impact["High impact gap"] = high_impact["high_impact_gap"].map(
                    high_impact_gap_label
                )
                display = high_impact[
                    [
                        "project_name",
                        "Indicator",
                        "gap_score",
                        "High impact gap",
                        "expected_benefit",
                        "recommended_action",
                    ]
                ].rename(
                    columns={
                        "project_name": "Project",
                        "gap_score": "Gap severity",
                        "expected_benefit": "Expected benefit",
                        "recommended_action": "Recommended action",
                    }
                )
                st.dataframe(
                    display,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Gap severity": st.column_config.NumberColumn(format="%d / 5"),
                        "High impact gap": st.column_config.TextColumn(
                            width="small",
                            help="From the assessment file's High impact gap column.",
                        ),
                    },
                )

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    with st.container(border=True, key="gap_priority_card"):
        section_header(
            "Priority action",
            "All indicators with a recommended action, ranked by gap severity.",
        )
        _priority_action_table(filtered)
