"""將既有確定性品質分數轉為固定、版本化且可公開的字母評等。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from backend.app.models.decision_profile import (
    ExplainableAssessmentScoreComponent,
)
from backend.app.models.quality_grade import (
    ETFHistoricalQualityGrade,
    ETFQualityGrade,
    ETFQualityGradeStatus,
)


GRADE_THRESHOLDS: tuple[tuple[Decimal, ETFQualityGrade], ...] = (
    (Decimal("90"), ETFQualityGrade.A_PLUS),
    (Decimal("80"), ETFQualityGrade.A),
    (Decimal("70"), ETFQualityGrade.B),
    (Decimal("60"), ETFQualityGrade.C),
    (Decimal("50"), ETFQualityGrade.D),
    (Decimal("40"), ETFQualityGrade.E),
    (Decimal("0"), ETFQualityGrade.F),
)
MIN_CALIBRATION_SAMPLE = 30
MIN_CALIBRATION_COVERAGE_PCT = Decimal("20")
MAX_COMPONENT_SATURATION_PCT = Decimal("50")

_DATA_BLOCKING_REASON_CODES = {
    "INCOMPLETE_DATA",
    "STALE_DATA",
    "MISSING_TOTAL_RETURN",
    "MISSING_DOWNSIDE_RISK",
    "MISSING_REFERENCE_PRICE",
    "FUTURE_REFERENCE_PRICE",
    "FUTURE_PERFORMANCE_DATA",
    "FUTURE_DIVIDEND_DATA",
}

_MISSING_LABELS = {
    "AFTER_TAX_TOTAL_RETURN": "稅後總報酬資料不足",
    "DOWNSIDE_RETURN": "下行風險資料不足",
    "AFTER_TAX_CASH_RATE": "稅後現金率資料不足",
    "DISTRIBUTION_STABILITY": "配息穩定度資料不足",
    "ACTUAL_76W_RATIO": "正式 ACTUAL 76W 組成資料不足",
}

_COMPONENT_MESSAGES = {
    "AFTER_TAX_TOTAL_RETURN": (
        "歷史稅後總報酬表現較佳。",
        "歷史稅後總報酬表現偏弱。",
    ),
    "DOWNSIDE_RETURN": (
        "觀察期下行表現相對穩定。",
        "觀察期曾出現較明顯的下行風險。",
    ),
    "AFTER_TAX_CASH_RATE": (
        "歷史稅後現金流貢獻較佳。",
        "歷史稅後現金流貢獻較低。",
    ),
    "DISTRIBUTION_STABILITY": (
        "歷史配息月份較穩定。",
        "歷史配息月份穩定度偏低。",
    ),
    "ACTUAL_76W_RATIO": (
        "正式配息組成顯示較高的 76W 比例。",
        "正式配息組成的 76W 比例較低。",
    ),
}


@dataclass(frozen=True, slots=True)
class QualityGradePublicationReadiness:
    ready: bool
    reasons: tuple[str, ...]


def evaluate_quality_grade_publication_readiness(
    *,
    scores: Iterable[Decimal | None],
    supported_product_count: int,
    total_return_component_scores: Iterable[Decimal],
) -> QualityGradePublicationReadiness:
    """以樣本、覆蓋與分數飽和防止過早公開失真的字母評等。"""

    rated_scores = [score for score in scores if score is not None]
    reasons: list[str] = []
    if len(rated_scores) < MIN_CALIBRATION_SAMPLE:
        reasons.append(
            f"可評等樣本僅 {len(rated_scores)} 檔，低於校準門檻 "
            f"{MIN_CALIBRATION_SAMPLE} 檔。"
        )
    coverage_pct = (
        Decimal(len(rated_scores)) / Decimal(supported_product_count) * 100
        if supported_product_count > 0
        else Decimal("0")
    )
    if coverage_pct < MIN_CALIBRATION_COVERAGE_PCT:
        reasons.append(
            "可評等樣本覆蓋率尚未達到 20%，不能代表支援的 ETF 市場。"
        )
    component_scores = list(total_return_component_scores)
    saturated_count = sum(score >= 100 for score in component_scores)
    saturation_pct = (
        Decimal(saturated_count) / Decimal(len(component_scores)) * 100
        if component_scores
        else Decimal("100")
    )
    if saturation_pct > MAX_COMPONENT_SATURATION_PCT:
        reasons.append(
            "稅後總報酬因子有超過一半樣本落在分數上限，門檻區辨力不足。"
        )
    return QualityGradePublicationReadiness(
        ready=not reasons,
        reasons=tuple(reasons),
    )


def grade_quality_score(score: Decimal | None) -> ETFQualityGrade | None:
    """以固定絕對門檻轉為字母評等；缺值不等同最低等級。"""

    if score is None:
        return None
    normalized = Decimal(str(score))
    if normalized < 0 or normalized > 100:
        raise ValueError("品質分數必須介於 0 到 100")
    return next(grade for minimum, grade in GRADE_THRESHOLDS if normalized >= minimum)


def _component_explanations(
    components: Iterable[ExplainableAssessmentScoreComponent],
) -> tuple[list[str], list[str]]:
    strengths: list[str] = []
    risks: list[str] = []
    for component in components:
        messages = _COMPONENT_MESSAGES.get(component.code)
        if messages is None:
            continue
        if component.score >= Decimal("70"):
            strengths.append(messages[0])
        elif component.score < Decimal("50"):
            risks.append(messages[1])
    return strengths[:3], risks[:3]


def build_historical_quality_grade(
    *,
    score: Decimal | None,
    components: Iterable[ExplainableAssessmentScoreComponent],
    missing_metrics: Iterable[str],
    history_years: int,
    blocking_reason_codes: Iterable[str] = (),
) -> ETFHistoricalQualityGrade:
    """建立不含原始分數的公開評等；核心或時效資料不可靠時暫不評等。"""

    missing = list(dict.fromkeys(str(item) for item in missing_metrics))
    blocking = sorted(
        _DATA_BLOCKING_REASON_CODES
        & {str(item) for item in blocking_reason_codes}
    )
    unavailable = [
        _MISSING_LABELS.get(code, code)
        for code in missing
    ]
    unavailable.extend(f"資料閘門未通過：{code}" for code in blocking)
    unavailable = list(dict.fromkeys(unavailable))
    grade = grade_quality_score(score)
    if grade is None or blocking:
        return ETFHistoricalQualityGrade(
            status=ETFQualityGradeStatus.UNRATED,
            evidence_period_years=history_years,
            unavailable_evidence=unavailable or ["核心歷史資料不足"],
            explanation="核心資料不足或未通過資料閘門，目前暫不評等。",
        )

    strengths, risks = _component_explanations(components)
    return ETFHistoricalQualityGrade(
        status=ETFQualityGradeStatus.RATED,
        grade=grade,
        evidence_period_years=history_years,
        strengths=strengths,
        risks=risks,
        unavailable_evidence=unavailable,
        explanation=(
            "此為歷史品質評等，不代表符合主人的領息月份、資金需求或買賣建議。"
        ),
    )


def build_unrated_quality_grade(
    *,
    history_years: int,
    reason: str,
) -> ETFHistoricalQualityGrade:
    return ETFHistoricalQualityGrade(
        status=ETFQualityGradeStatus.UNRATED,
        evidence_period_years=history_years,
        unavailable_evidence=[reason],
        explanation="此 ETF 目前不在可評等資料範圍內。",
    )
