from __future__ import annotations

import pandas as pd
import streamlit as st

from ..config import CARD_BACKGROUNDS, MATURITY_RUBRIC
from ..ui import (
    dataframe_selection_rows,
    detail_grid,
    insight_card,
    maturity_scale,
    page_header,
    section_header,
    summary_chips,
)


_ALL_PROJECT_TYPES = "All project types"


def _split_project_types(value: object) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _project_type_options(series: pd.Series) -> list[str]:
    options: list[str] = []
    seen: set[str] = set()
    for value in series:
        for tag in _split_project_types(value):
            key = tag.casefold()
            if key not in seen:
                options.append(tag)
                seen.add(key)
    return sorted(options, key=str.casefold)


def _matches_project_type(value: object, selected: str) -> bool:
    if not selected or selected == _ALL_PROJECT_TYPES:
        return True
    tags = {tag.casefold() for tag in _split_project_types(value)}
    return selected.casefold() in tags


def render(data: dict[str, pd.DataFrame]) -> None:
    page_header("Standards Library", "Browse selected standards and indicators.")

    standards = data["standards"].copy()
    if standards.empty:
        st.warning("No standards or indicators are available.")
        return

    standard_options = sorted(
        standards["standard_source"].dropna().astype(str).unique().tolist()
    )
    domain_options = sorted(standards["domain"].dropna().unique().tolist())
    project_type_options = _project_type_options(standards["project_type_tags"])

    with st.container(key="library_filters"):
        standard_col, domain_col, project_type_col = st.columns(
            [1.0, 0.9, 1.8], gap="medium"
        )
        with standard_col:
            selected_standard = st.selectbox(
                "Standard",
                ["All standards", *standard_options],
                key="library_standard_filter",
            )
        with domain_col:
            selected_domain = st.selectbox(
                "Domain",
                ["All domains", *domain_options],
                key="library_domain_filter",
            )
        with project_type_col:
            selected_project_type = st.selectbox(
                "Project type",
                [_ALL_PROJECT_TYPES, *project_type_options],
                key="library_project_type_filter",
                help="An indicator can match more than one project type.",
            )

    filtered = standards.copy()
    if selected_standard != "All standards":
        filtered = filtered[filtered["standard_source"] == selected_standard]
    if selected_domain != "All domains":
        filtered = filtered[filtered["domain"] == selected_domain]
    if selected_project_type != _ALL_PROJECT_TYPES:
        filtered = filtered[
            filtered["project_type_tags"].apply(
                lambda value: _matches_project_type(value, selected_project_type)
            )
        ]

    summary_chips(
        [
            f"{len(filtered)} indicators",
            selected_domain,
            selected_project_type,
        ]
    )

    if filtered.empty:
        st.warning("No indicators match the selected filters.")
        return

    ordered = filtered.sort_values(
        ["domain", "subdomain", "indicator_id"]
    ).reset_index(drop=True)
    display = ordered[
        [
            "indicator_id",
            "indicator_name",
            "domain",
            "subdomain",
            "project_type_tags",
            "standard_source",
        ]
    ].rename(
        columns={
            "indicator_id": "ID",
            "indicator_name": "Indicator",
            "domain": "Domain",
            "subdomain": "Subdomain",
            "project_type_tags": "Project types",
            "standard_source": "Standard",
        }
    )

    table_col, detail_col = st.columns([1.35, 1], gap="large")
    with table_col:
        with st.container(border=True, key="library_catalogue_card"):
            section_header(
                "Indicator catalogue",
                "Select a row to inspect its definition and assessment requirements.",
            )
            event = st.dataframe(
                display,
                width="stretch",
                height=560,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="standards_library_table",
                column_config={
                    "ID": st.column_config.TextColumn(width="small"),
                    "Indicator": st.column_config.TextColumn(width="large"),
                    "Domain": st.column_config.TextColumn(width="medium"),
                    "Subdomain": st.column_config.TextColumn(width="medium"),
                    "Project types": st.column_config.TextColumn(width="large"),
                    "Standard": st.column_config.TextColumn(width="medium"),
                },
            )

    rows = dataframe_selection_rows(event)
    selected = ordered.iloc[rows[0] if rows else 0]

    with detail_col:
        with st.container(border=True, key="library_information_card"):
            section_header("Indicator information")
            st.markdown(
                f"### {selected.get('indicator_id', '')} - "
                f"{selected.get('indicator_name', '')}"
            )
            st.caption(
                f"{selected.get('domain', '—')} - {selected.get('subdomain', '—')}"
            )
            insight_card(
                "Standard source",
                str(selected.get("standard_source", "—")),
                f"Applicable project types: {selected.get('project_type_tags', '—')}",
                CARD_BACKGROUNDS["blue"],
            )

        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        with st.container(border=True, key="library_specification_card"):
            section_header("Operational indicator specification")
            detail_grid(
                [
                    ("Indicator definition", selected.get("indicator_definition")),
                    ("Measurement method", selected.get("measurement_method")),
                    ("Required evidence", selected.get("required_evidence")),
                    ("Required data", selected.get("required_data")),
                    ("Applicable project types", selected.get("project_type_tags")),
                    ("Applicability guidance", selected.get("applicability")),
                    ("Assessment limitations", selected.get("limitations")),
                    ("Maturity scoring guidance", selected.get("maturity_guidance")),
                ]
            )
            with st.expander("Show the common 0–5 maturity scale", expanded=False):
                maturity_scale(MATURITY_RUBRIC)
