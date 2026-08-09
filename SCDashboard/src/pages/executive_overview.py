from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..config import (
    CARD_BACKGROUNDS,
    DOMAIN_COLORS,
    DOMAIN_DISPLAY,
    HIGH_PRIORITY_MIN,
    PLOTLY_CONFIG,
)
from ..scoring import (
    bounded_average,
    data_readiness_label,
    evidence_label,
    maturity_interpretation,
    recommendation_explanation,
)
from ..ui import (
    action_card,
    detail_grid,
    insight_card,
    metric_card,
    page_header,
    plotly_selected_customdata,
    section_header,
)


def _domain_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for domain, group in df.groupby("domain", dropna=False):
        rows.append(
            {
                "domain": domain,
                "display_domain": DOMAIN_DISPLAY.get(domain, str(domain)),
                "maturity_score": round(bounded_average(group["current_score"], 5), 1),
                "gap_score": round(bounded_average(group["gap_score"], 5), 1),
                "evidence_quality": round(
                    bounded_average(group["evidence_quality_score"], 4), 1
                ),
                "data_readiness": round(
                    bounded_average(group["data_readiness_score"], 3), 1
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["maturity_score", "display_domain"], ascending=[False, True]
    )


def _scope_filter(dashboard: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    domains = sorted(dashboard["domain"].dropna().unique().tolist())
    with st.container(key="executive_filters"):
        selected_domain = st.selectbox(
            "Domain",
            ["All domains", *domains],
            format_func=lambda value: (
                value
                if value == "All domains"
                else DOMAIN_DISPLAY.get(value, value)
            ),
            key="executive_domain_filter",
        )

    if selected_domain == "All domains":
        return dashboard.copy(), selected_domain
    return dashboard[dashboard["domain"] == selected_domain].copy(), selected_domain


def _domain_chart(summary: pd.DataFrame) -> None:
    colors = [DOMAIN_COLORS.get(domain, "#263242") for domain in summary["domain"]]
    fig = go.Figure(
        go.Bar(
            x=summary["display_domain"],
            y=summary["maturity_score"],
            marker_color=colors,
            text=summary["maturity_score"].map(lambda value: f"{value:.1f}/5"),
            textposition="outside",
            customdata=summary[["domain"]].to_numpy(),
            hovertemplate=(
                "%{x}<br>Average maturity score: %{y:.1f}/5<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        height=350,
        margin={"l": 15, "r": 15, "t": 20, "b": 70},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font={"family": "Inter, Segoe UI, Arial", "color": "#606772", "size": 11},
        xaxis={"title": None, "automargin": True},
        yaxis={
            "range": [0, 5.5],
            "tickmode": "array",
            "tickvals": [0, 1, 2, 3, 4, 5],
            "gridcolor": "#ECEEF2",
            "zeroline": False,
        },
    )
    event = st.plotly_chart(
        fig,
        width="stretch",
        theme=None,
        config=PLOTLY_CONFIG,
        key="executive_domain_chart",
        on_select="rerun",
        selection_mode="points",
    )
    selected_domains = plotly_selected_customdata(event)
    if selected_domains:
        _evidence_drilldown(
            st.session_state.get("executive_filtered_data", pd.DataFrame()),
            str(selected_domains[0]),
        )


def _evidence_drilldown(filtered: pd.DataFrame, selected_domain: str) -> None:
    rows = filtered[filtered["domain"] == selected_domain].copy()
    if rows.empty:
        return

    with st.expander(
        f"Evidence details - {DOMAIN_DISPLAY.get(selected_domain, selected_domain)}",
        expanded=True,
    ):
        indicator_options = rows["indicator_name"].dropna().drop_duplicates().tolist()
        if not indicator_options:
            st.info("No indicators are available for this domain.")
            return
        selected_indicator = st.selectbox(
            "Indicator",
            indicator_options,
            key=f"executive_evidence_{selected_domain}",
        )
        row = rows[rows["indicator_name"] == selected_indicator].iloc[0]
        detail_grid(
            [
                ("Indicator", row.get("indicator_name")),
                ("Project", row.get("project_name")),
                ("Maturity", f"{int(row.get('current_score', 0))}/5"),
                ("Target maturity", f"{int(row.get('target_score', 0))}/5"),
                ("Gap severity", f"{int(row.get('gap_score', 0))}/5"),
                (
                    "Evidence quality",
                    f"{int(row.get('evidence_quality_score', 0))}/4 - "
                    f"{evidence_label(row.get('evidence_quality_score', 0))}",
                ),
                ("Evidence source", row.get("evidence_source")),
                ("Reviewer notes", row.get("evidence_notes")),
            ]
        )


def _recommended_actions(filtered: pd.DataFrame) -> None:
    actions = filtered[
        filtered["recommended_action"].fillna("").astype(str).str.strip().ne("")
    ].copy()
    actions = actions.sort_values(
        ["priority_score", "gap_score", "evidence_quality_score"],
        ascending=[False, False, True],
    ).drop_duplicates("recommended_action")

    if actions.empty:
        st.info("No recommended actions are available.")
        return

    for _, row in actions.head(5).iterrows():
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
    page_header(
        "Executive Overview",
        "Provide a high-level summary for decision-makers.",
    )

    dashboard = data["dashboard"].copy()
    if dashboard.empty:
        st.warning("No assessment data is available.")
        return

    filtered, selected_domain = _scope_filter(dashboard)
    if filtered.empty:
        st.info("No assessment records match the selected domain.")
        return
    st.session_state["executive_filtered_data"] = filtered

    overall_maturity = bounded_average(filtered["current_score"], 5)
    data_readiness = bounded_average(filtered["data_readiness_score"], 3)
    evidence_quality = bounded_average(filtered["evidence_quality_score"], 4)
    high_priority_gaps = int(
        (pd.to_numeric(filtered["priority_score"], errors="coerce").fillna(0)
         >= HIGH_PRIORITY_MIN).sum()
    )

    summary = _domain_summary(filtered)
    all_domains_summary = _domain_summary(dashboard)
    strongest = all_domains_summary.iloc[0]
    weakest = all_domains_summary.sort_values(
        ["maturity_score", "display_domain"], ascending=[True, True]
    ).iloc[0]

    left, right = st.columns([0.9, 1.3], gap="large")

    with left:
        row_one = st.columns(2, gap="medium")
        with row_one[0]:
            metric_card(
                "Overall Maturity Score",
                f"{overall_maturity:.1f}/5",
                maturity_interpretation(overall_maturity),
                CARD_BACKGROUNDS["blue"],
            )
        with row_one[1]:
            metric_card(
                "Evidence Quality",
                f"{evidence_quality:.1f}/4",
                evidence_label(evidence_quality),
                CARD_BACKGROUNDS["gray"],
            )

        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        row_two = st.columns(2, gap="medium")
        with row_two[0]:
            metric_card(
                "High-Priority Gaps",
                str(high_priority_gaps),
                "Indicators with initial priority score 3 or higher.",
                CARD_BACKGROUNDS["gray"],
            )
        with row_two[1]:
            metric_card(
                "Data Readiness",
                f"{data_readiness:.1f}/3",
                data_readiness_label(data_readiness),
                CARD_BACKGROUNDS["purple"],
            )

        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            section_header(
                "Domain maturity scores",
            )
            _domain_chart(summary)

    with right:
        if selected_domain == "All domains":
            strongest_col, weakest_col = st.columns(2, gap="medium")
            with strongest_col:
                insight_card(
                    "Strongest domain",
                    f"{strongest['display_domain']} - {float(strongest['maturity_score']):.1f}/5",
                    maturity_interpretation(float(strongest["maturity_score"])),
                    "#EAF8F4",
                )
            with weakest_col:
                insight_card(
                    "Weakest domain",
                    f"{weakest['display_domain']} - {float(weakest['maturity_score']):.1f}/5",
                    maturity_interpretation(float(weakest["maturity_score"])),
                    "#FDEEEE",
                )

            st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            section_header("Top recommended actions")
            _recommended_actions(filtered)
