from __future__ import annotations

from math import floor
from typing import Any

import pandas as pd

from .config import (
    DATA_READINESS_RUBRIC,
    EVIDENCE_RUBRIC,
    HIGH_PRIORITY_MIN,
    MATURITY_RUBRIC,
)


def _as_float(value: object, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def rubric_level(score: float | int | None, maximum: int) -> int:
    """Return a bounded discrete rubric level using conventional half-up rounding."""
    bounded = clamp(_as_float(score), 0.0, float(maximum))
    return int(floor(bounded + 0.5))


def bounded_average(values: pd.Series, maximum: float) -> float:
    """Arithmetic mean after numeric conversion and rubric clipping."""
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if numeric.empty:
        return 0.0
    return float(numeric.clip(lower=0, upper=maximum).mean())


def maturity_interpretation(score: float | int | None) -> str:
    if score is None or pd.isna(score):
        return "No maturity score is available."
    return MATURITY_RUBRIC[rubric_level(score, 5)]


def maturity_rubric_text(score: float | int | None) -> str:
    return maturity_interpretation(score)


def evidence_label(score: float | int | None) -> str:
    if score is None or pd.isna(score):
        return EVIDENCE_RUBRIC[0][0]
    return EVIDENCE_RUBRIC[rubric_level(score, 4)][0]


def evidence_meaning(score: float | int | None) -> str:
    if score is None or pd.isna(score):
        return EVIDENCE_RUBRIC[0][1]
    return EVIDENCE_RUBRIC[rubric_level(score, 4)][1]


def data_readiness_label(score: float | int | None) -> str:
    if score is None or pd.isna(score):
        return DATA_READINESS_RUBRIC[0][0]
    return DATA_READINESS_RUBRIC[rubric_level(score, 3)][0]


def data_readiness_meaning(score: float | int | None) -> str:
    if score is None or pd.isna(score):
        return DATA_READINESS_RUBRIC[0][1]
    return DATA_READINESS_RUBRIC[rubric_level(score, 3)][1]


def calculate_gap_severity(
    current_score: float | int | None,
    target_score: float | int | None,
) -> float:
    """Gap severity = Target maturity - Current maturity, bounded to 0-5."""
    current = clamp(_as_float(current_score), 0.0, 5.0)
    target = clamp(_as_float(target_score), 0.0, 5.0)
    return clamp(target - current, 0.0, 5.0)


def high_impact_gap_label(value: object) -> str:
    """Clean up the assessment file's free-text High impact gap column."""
    text = str(value or "").strip().lower()
    if not text:
        return "—"
    if "high" in text:
        return "High impact"
    if "medium" in text or "med" in text:
        return "Medium impact"
    if "low" in text:
        return "Low impact"
    return str(value).strip()


def priority_level(score: float | int | None) -> str:
    """Initial priority grouping based only on gap severity."""
    value = clamp(_as_float(score), 0.0, 5.0)
    if value >= HIGH_PRIORITY_MIN:
        return "High"
    if value >= 2:
        return "Medium"
    return "Low"


def calculate_priority_components(
    row: pd.Series | dict[str, Any],
) -> dict[str, float]:
    """Return the approved initial-priority components.

    The rubric documents an expanded future formula, but the active initial formula
    is Priority score = Gap severity. The unused components remain zero so the
    calculation stays transparent and does not invent unsupported weights.
    """
    gap = calculate_gap_severity(
        row.get("current_score", 0),
        row.get("target_score", 0),
    )
    return {
        "gap_severity": gap,
        "indicator_importance": 0.0,
        "evidence_risk": 0.0,
        "data_readiness_need": 0.0,
        "expected_impact": 0.0,
        "implementation_effort": 0.0,
    }


def calculate_priority_score(row: pd.Series | dict[str, Any]) -> int:
    return rubric_level(calculate_priority_components(row)["gap_severity"], 5)


def priority_breakdown(row: pd.Series | dict[str, Any]) -> str:
    return f"Priority score = gap severity = {calculate_priority_score(row)}"


def _normalise_rubric_column(
    series: pd.Series,
    maximum: int,
    default: int = 0,
) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").fillna(default)
    return numeric.apply(lambda value: rubric_level(value, maximum)).astype(int)


def enrich_assessments(assessments: pd.DataFrame) -> pd.DataFrame:
    """Clean assessment records and recalculate every scoring field.

    Official scales:
    - Current and target maturity: 0-5
    - Evidence quality/confidence: 0-4
    - Data readiness: 0-3
    - Gap severity: Target maturity - Current maturity, bounded 0-5
    - Initial priority score: Gap severity
    """
    result = assessments.copy()

    defaults = {
        "current_score": 0,
        "target_score": 0,
        "evidence_quality_score": 0,
        "data_readiness_score": 0,
        "evidence_count": 0,
    }
    for column, default in defaults.items():
        if column not in result.columns:
            result[column] = default

    result["current_score"] = _normalise_rubric_column(
        result["current_score"], 5
    )
    result["target_score"] = _normalise_rubric_column(
        result["target_score"], 5
    )
    result["evidence_quality_score"] = _normalise_rubric_column(
        result["evidence_quality_score"], 4
    )
    result["data_readiness_score"] = _normalise_rubric_column(
        result["data_readiness_score"], 3
    )
    result["evidence_count"] = (
        pd.to_numeric(result["evidence_count"], errors="coerce")
        .fillna(0)
        .round()
        .clip(lower=0)
        .astype(int)
    )

    # Source gap/priority columns are intentionally overwritten with the rubric formula.
    result["gap_score"] = (
        result["target_score"] - result["current_score"]
    ).clip(lower=0, upper=5).astype(int)
    result["priority_score"] = result["gap_score"].astype(int)
    result["priority_level"] = result["priority_score"].apply(priority_level)
    result["priority_breakdown"] = result.apply(priority_breakdown, axis=1)

    result["maturity_interpretation"] = result["current_score"].apply(
        maturity_interpretation
    )
    result["evidence_quality_label"] = result[
        "evidence_quality_score"
    ].apply(evidence_label)
    result["evidence_quality_meaning"] = result[
        "evidence_quality_score"
    ].apply(evidence_meaning)
    result["data_readiness_label"] = result[
        "data_readiness_score"
    ].apply(data_readiness_label)
    result["data_readiness_meaning"] = result[
        "data_readiness_score"
    ].apply(data_readiness_meaning)

    # Evidence completeness is traceability, not a scoring scale.
    result["evidence_complete"] = result["evidence_count"].gt(0)
    result["evidence_confidence_score"] = result["evidence_quality_score"]
    result["evidence_risk"] = 4 - result["evidence_quality_score"]
    result["data_readiness_need"] = 3 - result["data_readiness_score"]

    return result


def evidence_completeness_pct(df: pd.DataFrame) -> float:
    """Percentage of applicable assessments linked to at least one evidence record."""
    if df.empty:
        return 0.0
    if "evidence_complete" in df.columns:
        complete = df["evidence_complete"].fillna(False).astype(bool)
    else:
        complete = pd.to_numeric(
            df.get("evidence_count", pd.Series(0, index=df.index)),
            errors="coerce",
        ).fillna(0).gt(0)
    return float(complete.mean() * 100)


def recommendation_explanation(
    row: pd.Series | dict[str, Any],
) -> str:
    indicator_id = str(row.get("indicator_id", "")).strip()
    indicator_name = str(row.get("indicator_name", indicator_id or "Indicator"))
    indicator = f"{indicator_id}: {indicator_name}" if indicator_id else indicator_name
    current = rubric_level(row.get("current_score", 0), 5)
    target = rubric_level(row.get("target_score", 0), 5)
    gap = rubric_level(
        row.get("gap_score", calculate_gap_severity(current, target)), 5
    )
    evidence_score = rubric_level(row.get("evidence_quality_score", 0), 4)
    readiness_score = rubric_level(row.get("data_readiness_score", 0), 3)

    return (
        f"{indicator}: gap {gap}/5, evidence confidence {evidence_score}/4 "
        f"({evidence_label(evidence_score)}), and data readiness "
        f"{readiness_score}/3 ({data_readiness_label(readiness_score)})."
    )
