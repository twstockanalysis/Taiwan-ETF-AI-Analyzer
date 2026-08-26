"""產生不洩漏個別原始分數的 V4-1 校準摘要。"""

from __future__ import annotations

from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path
from statistics import median

from backend.app.models.assessment_calibration import (
    AssessmentCalibrationReport,
    CalibrationFactorDecision,
    CalibrationFactorStatus,
    CalibrationScoreSummary,
)
from backend.app.models.market_eligibility import MarketEligibilityIndexRequest
from backend.app.models.quality_grade import ETFQualityGradeStatus
from backend.app.services.market_eligibility_index import (
    build_market_eligibility_index,
)
from backend.app.services.quality_grading import (
    evaluate_quality_grade_publication_readiness,
    grade_quality_score,
)


_SENSITIVITY_DISTANCE = Decimal("2.5")
_INTERNAL_GRADE_BOUNDARIES = tuple(
    Decimal(value) for value in ("40", "50", "60", "70", "80", "90")
)
_QUALITY_FACTORS = (
    "AFTER_TAX_TOTAL_RETURN",
    "DOWNSIDE_RETURN",
    "AFTER_TAX_CASH_RATE",
    "DISTRIBUTION_STABILITY",
    "ACTUAL_76W_RATIO",
)


def _is_boundary_sensitive(score: Decimal | None) -> bool:
    return score is not None and any(
        abs(score - boundary) <= _SENSITIVITY_DISTANCE
        for boundary in _INTERNAL_GRADE_BOUNDARIES
    )


def _score_summary(
    scores: list[Decimal],
    observed_values: list[Decimal],
) -> CalibrationScoreSummary:
    ordered = sorted(scores)
    observed = sorted(observed_values)
    return CalibrationScoreSummary(
        available_count=len(ordered),
        minimum=ordered[0] if ordered else None,
        median=Decimal(str(median(ordered))) if ordered else None,
        maximum=ordered[-1] if ordered else None,
        observed_minimum=observed[0] if observed else None,
        observed_median=Decimal(str(median(observed))) if observed else None,
        observed_maximum=observed[-1] if observed else None,
    )


def build_assessment_calibration_report(
    request: MarketEligibilityIndexRequest,
    database_path: str | Path,
    *,
    as_of_date: date | None = None,
) -> AssessmentCalibrationReport:
    """以同一資料快照摘要評等覆蓋與門檻敏感度，不輸出個別分數。"""

    built = build_market_eligibility_index(
        request,
        database_path,
        as_of_date=as_of_date,
    )
    public_items = built.response.candidates
    internal_items = built.internal_candidates
    provisional_grades = [
        grade_quality_score(item.quality_score)
        for item in internal_items
        if item.quality_grade_eligible and item.quality_score is not None
    ]
    grade_counts = Counter(
        grade.value for grade in provisional_grades if grade is not None
    )
    factor_available_counts = {
        factor: sum(
            factor not in item.quality_missing
            for item in internal_items
        )
        for factor in _QUALITY_FACTORS
    }
    factor_score_summaries = {
        factor: _score_summary(
            [
                component.score
                for item in internal_items
                for component in item.quality_components
                if component.code == factor
            ],
            [
                component.observed_value
                for item in internal_items
                for component in item.quality_components
                if component.code == factor
                and component.observed_value is not None
            ],
        )
        for factor in _QUALITY_FACTORS
    }
    rated_scores = sorted(
        item.quality_score
        for item in internal_items
        if item.quality_grade_eligible and item.quality_score is not None
    )
    readiness = evaluate_quality_grade_publication_readiness(
        scores=(
            item.quality_score if item.quality_grade_eligible else None
            for item in internal_items
        ),
        supported_product_count=built.response.supported_product_count,
        total_return_component_scores=(
            component.score
            for item in internal_items
            for component in item.quality_components
            if component.code == "AFTER_TAX_TOTAL_RETURN"
        ),
    )
    published_rated_count = sum(
        item.historical_quality_grade.status == ETFQualityGradeStatus.RATED
        for item in public_items
    )
    return AssessmentCalibrationReport(
        analysis_date=built.response.analysis_date,
        snapshot_id=built.response.snapshot_id,
        universe_count=built.response.universe_count,
        supported_product_count=built.response.supported_product_count,
        publication_ready=readiness.ready,
        publication_blockers=list(readiness.reasons),
        provisional_rated_count=len(rated_scores),
        published_rated_count=published_rated_count,
        provisional_grade_counts={
            grade: grade_counts.get(grade, 0)
            for grade in ("A+", "A", "B", "C", "D", "E", "F")
        },
        boundary_sensitive_count=sum(
            _is_boundary_sensitive(item.quality_score)
            if item.quality_grade_eligible
            else False
            for item in internal_items
        ),
        rated_score_min=rated_scores[0] if rated_scores else None,
        rated_score_median=(
            Decimal(str(median(rated_scores))) if rated_scores else None
        ),
        rated_score_max=rated_scores[-1] if rated_scores else None,
        factor_available_counts=factor_available_counts,
        factor_score_summaries=factor_score_summaries,
        factor_decisions=[
            CalibrationFactorDecision(
                code="CURRENT_TOTAL_RETURN_LED_SCORE",
                status=CalibrationFactorStatus.RETAINED,
                reason=(
                    "現行方法保留獨立的總報酬與下行風險，且高配息或高 76W "
                    "不能越過核心閘門。"
                ),
            ),
            CalibrationFactorDecision(
                code="FILL_CAPABILITY",
                status=CalibrationFactorStatus.DEFERRED,
                reason=(
                    "目前尚無經企業行動調整的填息事件與覆蓋契約，不能安全納入評分。"
                ),
            ),
            CalibrationFactorDecision(
                code="ETF_CONSTITUENT_CONCENTRATION",
                status=CalibrationFactorStatus.RISK_EVIDENCE_ONLY,
                reason=(
                    "正式成分股可用時應顯示集中風險，但不以單一固定懲罰取代配置閘門。"
                ),
            ),
            CalibrationFactorDecision(
                code="PORTFOLIO_CONSTITUENT_CONCENTRATION",
                status=CalibrationFactorStatus.RISK_EVIDENCE_ONLY,
                reason=(
                    "整體組合集中度取決於主人持股與配置結果，應在組合層評估。"
                ),
            ),
            CalibrationFactorDecision(
                code="EXTERNAL_LINEAR_FORMULA",
                status=CalibrationFactorStatus.NOT_ADOPTED,
                reason=(
                    "外部權重尚無回放與缺值證據，僅保留填息及集中度的研究優點。"
                ),
            ),
        ],
        conclusion=(
            "V4-1 保留現行確定性分數與固定評等契約；只有樣本、覆蓋率與分數區辨力"
            "同時通過時才公開字母評等，否則前台維持暫不評等。"
        ),
    )
