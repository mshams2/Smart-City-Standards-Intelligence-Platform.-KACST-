from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from ..config import DOMAIN_DISPLAY, EVIDENCE_RUBRIC
from ..scoring import evidence_label, evidence_meaning
from ..ui import (
    dataframe_selection_rows,
    detail_grid,
    page_header,
    section_header,
    summary_chips,
)


@st.dialog("Evidence Quality Score Rubric", width="large")
def _show_evidence_quality_score_rubric() -> None:
    rows = "".join(
        "<tr>"
        f"<td>{score}</td>"
        f"<td>{html.escape(quality)}</td>"
        f"<td>{html.escape(meaning)}</td>"
        "</tr>"
        for score, (quality, meaning) in EVIDENCE_RUBRIC.items()
    )
    st.markdown(
        f"""
        <table class="rubric-table">
            <thead>
                <tr>
                    <th>Score</th>
                    <th>Evidence quality</th>
                    <th>Meaning</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def _text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _link_or_reference_card(selected: pd.Series) -> None:
    label = _text(selected.get("link_or_reference")) or "No link or reference recorded"
    url = _text(selected.get("link_url"))

    if url:
        value_html = (
            f'<a href="{html.escape(url, quote=True)}" target="_blank" '
            'rel="noopener noreferrer" '
            'style="color:#1558B0;text-decoration:underline;font-weight:650;">'
            f"{html.escape(label)}</a>"
            f'<div style="margin-top:0.35rem;font-size:0.78rem;color:#747B86;'
            'overflow-wrap:anywhere;">'
            f"{html.escape(url)}</div>"
        )
    else:
        value_html = html.escape(label)

    st.markdown(
        f"""
        <div class="detail-grid">
            <div class="detail-item" style="grid-column:1 / -1;">
                <div class="detail-label">Link or reference</div>
                <div class="detail-value">{value_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _repository_view(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    evidence = data["evidence"].copy()
    projects = data["projects"][["project_id", "project_name", "domain"]].drop_duplicates(
        "project_id"
    )
    standards = data["standards"][["indicator_id", "indicator_name"]].drop_duplicates(
        "indicator_id"
    )

    view = evidence.merge(projects, on="project_id", how="left", validate="many_to_one")
    view = view.merge(standards, on="indicator_id", how="left", validate="many_to_one")
    view["evidence_quality_score"] = (
        pd.to_numeric(view["evidence_quality_score"], errors="coerce")
        .fillna(0)
        .clip(0, 4)
    )
    view["evidence_quality_level"] = view["evidence_quality_score"].apply(
        evidence_label
    )
    view["evidence_quality_meaning"] = view["evidence_quality_score"].apply(
        evidence_meaning
    )
    view["evidence_date_display"] = (
        pd.to_datetime(view["evidence_date"], errors="coerce")
        .dt.strftime("%Y-%m-%d")
        .fillna("—")
    )
    view["display_domain"] = view["domain"].map(DOMAIN_DISPLAY).fillna(view["domain"])
    return view


def render(data: dict[str, pd.DataFrame]) -> None:
    page_header("Evidence Repository", "Make scoring transparent and reviewable.")

    repository = _repository_view(data)
    if repository.empty:
        st.warning("No evidence records are available.")
        return

    projects = sorted(repository["project_name"].dropna().unique().tolist())
    domains = sorted(repository["domain"].dropna().unique().tolist())
    quality_levels = [f"{score}/4 - {evidence_label(score)}" for score in range(5)]

    with st.container(key="evidence_filters"):
        project_col, domain_col, quality_col = st.columns(
            [1.3, 0.9, 1.1], gap="medium"
        )
        with project_col:
            selected_project = st.selectbox(
                "Project",
                ["All projects", *projects],
                key="evidence_project_filter",
            )
        with domain_col:
            selected_domain = st.selectbox(
                "Domain",
                ["All domains", *domains],
                format_func=lambda value: (
                    value
                    if value == "All domains"
                    else DOMAIN_DISPLAY.get(value, value)
                ),
                key="evidence_domain_filter",
            )
        with quality_col:
            selected_quality = st.selectbox(
                "Evidence quality",
                ["All levels", *quality_levels],
                key="evidence_quality_filter",
            )

    filtered = repository.copy()
    if selected_project != "All projects":
        filtered = filtered[filtered["project_name"] == selected_project]
    if selected_domain != "All domains":
        filtered = filtered[filtered["domain"] == selected_domain]
    if selected_quality != "All levels":
        selected_score = int(selected_quality.split("/", 1)[0])
        filtered = filtered[filtered["evidence_quality_score"] == selected_score]

    summary_chips(
        [
            f"{len(filtered)} evidence records",
            selected_project,
            selected_domain,
            selected_quality,
        ]
    )
    if filtered.empty:
        st.info("No evidence records match the selected filters.")
        return

    ordered = filtered.sort_values(
        ["project_name", "indicator_id", "evidence_date"],
        ascending=[True, True, False],
    ).reset_index(drop=True)
    display = ordered[
        [
            "evidence_id",
            "project_name",
            "indicator_id",
            "indicator_name",
            "evidence_source",
            "evidence_type",
            "evidence_date_display",
            "evidence_quality_score",
            "source_organization",
        ]
    ].rename(
        columns={
            "evidence_id": "Evidence ID",
            "project_name": "Project",
            "indicator_id": "Indicator ID",
            "indicator_name": "Linked indicator",
            "evidence_source": "Evidence source",
            "evidence_type": "Evidence type",
            "evidence_date_display": "Evidence date",
            "evidence_quality_score": "Evidence quality",
            "source_organization": "Source organization",
        }
    )

    table_col, detail_col = st.columns([1.45, 1], gap="large")
    with table_col:
        with st.container(border=True, key="evidence_records_card"):
            section_header(
                "Evidence records",
                "Select a row to inspect reviewer notes and traceability details.",
            )
            event = st.dataframe(
                display,
                width="stretch",
                height=570,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="evidence_repository_table",
                column_config={
                    "Evidence quality": st.column_config.ProgressColumn(
                        min_value=0,
                        max_value=4,
                        format="%.0f / 4",
                        width="medium",
                    )
                },
            )

    rows = dataframe_selection_rows(event)
    selected = ordered.iloc[rows[0] if rows else 0]
    score = int(selected.get("evidence_quality_score", 0))

    with detail_col:
        with st.container(border=True, key="evidence_details_card"):
            section_header("Evidence details")
            st.markdown(f"### {selected.get('evidence_title', 'Evidence record')}")
            st.caption(
                f"{selected.get('project_name', '—')} - "
                f"{selected.get('indicator_id', '—')} - "
                f"{selected.get('indicator_name', '—')}"
            )
            detail_grid(
                [
                    ("Evidence source", selected.get("evidence_source")),
                    ("Evidence type", selected.get("evidence_type")),
                    ("Evidence date", selected.get("evidence_date_display")),
                    ("Source organization", selected.get("source_organization")),
                ]
            )

            quality_col, meaning_col = st.columns(2, gap="small")
            with quality_col:
                with st.container(border=True, key="evidence_quality_level_card"):
                    st.markdown(
                        f"""
                        <div class="detail-label">Evidence quality level</div>
                        <div class="detail-value">{score}/4 - {html.escape(evidence_label(score))}</div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "Evidence Quality Score Rubric",
                        key="show_evidence_quality_score_rubric",
                        type="tertiary",
                    ):
                        _show_evidence_quality_score_rubric()

            with meaning_col:
                with st.container(border=True, key="quality_meaning_card"):
                    st.markdown(
                        f"""
                        <div class="detail-label">Quality meaning</div>
                        <div class="detail-value">{html.escape(evidence_meaning(score))}</div>
                        """,
                        unsafe_allow_html=True,
                    )

            detail_grid([("Reviewer notes", selected.get("evidence_notes"))])
            _link_or_reference_card(selected)
