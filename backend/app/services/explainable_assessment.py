"""以既有候選閘門建立可追溯、不可覆寫風險的評定基線。"""

from backend.app.models.decision_profile import (
    ExplainableAssessment,
    ExplainableAssessmentFactor,
    ExplainableAssessmentFactorStatus,
    ExplainableAssessmentOutcome,
)
from backend.app.models.monthly_combination import (
    CandidateReasonCode,
    MonthlyCombinationCalculationResult,
    MonthlyCombinationCandidateResult,
    MonthlyCombinationEligibilityRules,
)


_DATA_CODES = {
    CandidateReasonCode.INCOMPLETE_DATA,
    CandidateReasonCode.STALE_DATA,
    CandidateReasonCode.UNSTABLE_DISTRIBUTIONS,
}
_MISSING_RISK_CODES = {
    CandidateReasonCode.MISSING_TOTAL_RETURN,
    CandidateReasonCode.MISSING_DOWNSIDE_RISK,
}
_FAILED_RISK_CODES = {
    CandidateReasonCode.WEAK_TOTAL_RETURN,
    CandidateReasonCode.EXCESSIVE_DOWNSIDE_RISK,
    CandidateReasonCode.EXCESSIVE_HOLDING_OVERLAP,
    CandidateReasonCode.EXCESSIVE_CONCENTRATION,
}
_MISSING_CASH_CODES = {CandidateReasonCode.MISSING_AFTER_TAX_CASH}
_FAILED_CASH_CODES = {CandidateReasonCode.NON_POSITIVE_AFTER_TAX_CASH}


def _percentage(value) -> str:
    return "尚未取得" if value is None else f"{value}%"


def _factor(
    category: str,
    status: ExplainableAssessmentFactorStatus,
    title: str,
    summary: str,
    candidate: MonthlyCombinationCandidateResult,
    codes: set[CandidateReasonCode],
    evidence: list[str],
) -> ExplainableAssessmentFactor:
    matching = [reason for reason in candidate.reasons if reason.code in codes]
    return ExplainableAssessmentFactor(
        category=category,
        status=status,
        title=title,
        summary=summary,
        evidence=[*evidence, *(reason.message for reason in matching)],
        reason_codes=[reason.code.value for reason in matching],
    )


def _candidate(
    result: MonthlyCombinationCalculationResult,
) -> MonthlyCombinationCandidateResult | None:
    candidates = [*result.selected_candidates, *result.rejected_candidates]
    return candidates[0] if candidates else None


def build_explainable_assessment(
    result: MonthlyCombinationCalculationResult,
    rules: MonthlyCombinationEligibilityRules,
) -> ExplainableAssessment:
    """依固定優先順序彙整候選證據；不計總分也不產生買賣訊號。"""

    candidate = _candidate(result)
    if candidate is None:
        return ExplainableAssessment(
            outcome=ExplainableAssessmentOutcome.INSUFFICIENT_DATA,
            headline="缺少候選評估結果，暫時無法形成評定。",
            factors=[],
        )

    reason_codes = {reason.code for reason in candidate.reasons}
    factors: list[ExplainableAssessmentFactor] = []

    data_status = (
        ExplainableAssessmentFactorStatus.FAIL
        if reason_codes & _DATA_CODES
        else ExplainableAssessmentFactorStatus.PASS
    )
    factors.append(
        _factor(
            "DATA_QUALITY",
            data_status,
            "資料品質",
            "資料完整度、新鮮度與配息月份穩定性均須通過。",
            candidate,
            _DATA_CODES,
            [
                "完整度 "
                f"{_percentage(candidate.completeness_pct)}"
                f"（門檻 {rules.min_completeness_pct}%）",
                f"資料新鮮：{'是' if candidate.data_is_fresh is True else '否或未知'}",
                "配息月份穩定度 "
                f"{_percentage(candidate.distribution_stability_pct)}"
                f"（門檻 {rules.min_distribution_stability_pct}%）",
            ],
        )
    )

    risk_missing = reason_codes & _MISSING_RISK_CODES
    risk_failed = reason_codes & _FAILED_RISK_CODES
    overlap_unknown = CandidateReasonCode.HOLDING_OVERLAP_UNAVAILABLE in reason_codes
    if risk_missing:
        risk_status = ExplainableAssessmentFactorStatus.UNAVAILABLE
    elif risk_failed:
        risk_status = ExplainableAssessmentFactorStatus.FAIL
    elif overlap_unknown:
        risk_status = ExplainableAssessmentFactorStatus.REVIEW
    else:
        risk_status = ExplainableAssessmentFactorStatus.PASS
    factors.append(
        _factor(
            "TOTAL_RETURN_AND_PRINCIPAL_RISK",
            risk_status,
            "總報酬與本金風險",
            "總報酬、下行風險、持股重疊與配置集中度優先於配息月份。",
            candidate,
            _MISSING_RISK_CODES
            | _FAILED_RISK_CODES
            | {CandidateReasonCode.HOLDING_OVERLAP_UNAVAILABLE},
            [
                "稅後總報酬估算 "
                f"{_percentage(candidate.estimated_after_tax_total_return_pct)}"
                f"（最低 {rules.min_after_tax_total_return_pct}%）",
                f"下行報酬 {_percentage(candidate.downside_return_pct)}"
                f"（最低 {rules.min_downside_return_pct}%）",
                f"候選配置 {candidate.proposed_allocation_pct}%"
                f"（上限 {rules.max_candidate_allocation_pct}%）",
                "持股重疊 "
                f"{_percentage(candidate.holding_overlap_pct)}"
                f"（上限 {rules.max_holding_overlap_pct}%）",
            ],
        )
    )

    if reason_codes & _MISSING_CASH_CODES:
        cash_status = ExplainableAssessmentFactorStatus.UNAVAILABLE
    elif reason_codes & _FAILED_CASH_CODES:
        cash_status = ExplainableAssessmentFactorStatus.FAIL
    else:
        cash_status = ExplainableAssessmentFactorStatus.PASS
    factors.append(
        _factor(
            "AFTER_TAX_CASH_FLOW",
            cash_status,
            "稅後現金流",
            "以稅後可用現金評估貢獻，不以名目配息率代替。",
            candidate,
            _MISSING_CASH_CODES | _FAILED_CASH_CODES,
            [
                "年化稅後現金率 "
                f"{_percentage(candidate.annual_after_tax_cash_rate_pct)}"
            ],
        )
    )

    if CandidateReasonCode.MONTHLY_COVERAGE_DISABLED in reason_codes:
        month_status = ExplainableAssessmentFactorStatus.NOT_EVALUATED
    elif candidate.selected:
        month_status = ExplainableAssessmentFactorStatus.PASS
    else:
        month_status = ExplainableAssessmentFactorStatus.REVIEW
    month_codes = {
        CandidateReasonCode.MONTHLY_COVERAGE_DISABLED,
        CandidateReasonCode.NO_GAP_CONTRIBUTION,
        CandidateReasonCode.REDUNDANT_MONTH_COVERAGE,
        CandidateReasonCode.MAX_COMPLEMENTARY_ETFS_REACHED,
        CandidateReasonCode.BASE_MONTHLY_DATA_UNAVAILABLE,
        CandidateReasonCode.SUPPORTS_PAYMENT_MONTHS,
    }
    factors.append(
        _factor(
            "OPTIONAL_PAYMENT_MONTH_COVERAGE",
            month_status,
            "選配領息月份",
            "只有在核心資料、報酬、風險與現金流閘門後才考量月份互補。",
            candidate,
            month_codes,
            [
                "可支援缺口月份："
                + ("、".join(map(str, candidate.supported_gap_months)) or "無")
            ],
        )
    )

    core_statuses = [factor.status for factor in factors[:3]]
    if ExplainableAssessmentFactorStatus.UNAVAILABLE in core_statuses:
        outcome = ExplainableAssessmentOutcome.INSUFFICIENT_DATA
        headline = "核心證據不足，暫時不能形成可靠評定。"
    elif ExplainableAssessmentFactorStatus.FAIL in core_statuses:
        outcome = ExplainableAssessmentOutcome.BLOCKED_BY_GATE
        headline = "至少一項核心閘門未通過，不應只因配息或月份納入。"
    elif candidate.selected:
        outcome = ExplainableAssessmentOutcome.GATE_ALIGNED
        headline = "此情境通過目前設定的核心閘門與月份互補條件。"
    else:
        outcome = ExplainableAssessmentOutcome.NEEDS_REVIEW
        headline = "核心閘門未阻擋，但月份互補或次要資訊仍需人工判斷。"

    return ExplainableAssessment(
        outcome=outcome,
        headline=headline,
        factors=factors,
    )
