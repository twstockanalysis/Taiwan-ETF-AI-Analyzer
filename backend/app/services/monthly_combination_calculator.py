"""M10-5 月配缺口與候選排除純計算服務。"""

from decimal import Decimal

from backend.app.models.monthly_combination import (
    CandidateReason,
    CandidateReasonCode,
    CandidateReasonKind,
    MonthlyCombinationCalculationInput,
    MonthlyCombinationCalculationResult,
    MonthlyCombinationCandidateInput,
    MonthlyCombinationCandidateResult,
    MonthlyCombinationStatus,
)


ALL_MONTHS = set(range(1, 13))


def _percentage(value: Decimal | None) -> str:
    return "尚未取得" if value is None else f"{value}%"


def _reason(
    kind: CandidateReasonKind,
    code: CandidateReasonCode,
    message: str,
    months: list[int] | None = None,
) -> CandidateReason:
    return CandidateReason(
        kind=kind,
        code=code,
        message=message,
        affected_months=months or [],
    )


def _eligibility_reasons(
    candidate: MonthlyCombinationCandidateInput,
    value: MonthlyCombinationCalculationInput,
) -> list[CandidateReason]:
    rules = value.rules
    reasons: list[CandidateReason] = []

    if (
        candidate.completeness_pct is None
        or candidate.completeness_pct < rules.min_completeness_pct
    ):
        reasons.append(
            _reason(
                CandidateReasonKind.EXCLUDE,
                CandidateReasonCode.INCOMPLETE_DATA,
                "資料完整度未達候選門檻"
                f"（觀察值 {_percentage(candidate.completeness_pct)}；"
                f"門檻 {rules.min_completeness_pct}%）。",
            )
        )
    if candidate.data_is_fresh is not True:
        reasons.append(
            _reason(
                CandidateReasonKind.EXCLUDE,
                CandidateReasonCode.STALE_DATA,
                "配息或績效資料缺少、或已超過新鮮度門檻。",
            )
        )
    if (
        candidate.distribution_stability_pct is None
        or candidate.distribution_stability_pct
        < rules.min_distribution_stability_pct
    ):
        reasons.append(
            _reason(
                CandidateReasonKind.EXCLUDE,
                CandidateReasonCode.UNSTABLE_DISTRIBUTIONS,
                "歷史付款月份的重複出現比例未達門檻"
                "（觀察值 "
                f"{_percentage(candidate.distribution_stability_pct)}；"
                f"門檻 {rules.min_distribution_stability_pct}%）。",
            )
        )
    if candidate.estimated_after_tax_total_return_pct is None:
        reasons.append(
            _reason(
                CandidateReasonKind.EXCLUDE,
                CandidateReasonCode.MISSING_TOTAL_RETURN,
                "缺少可用的稅後總報酬估算。",
            )
        )
    elif (
        candidate.estimated_after_tax_total_return_pct
        < rules.min_after_tax_total_return_pct
    ):
        reasons.append(
            _reason(
                CandidateReasonKind.EXCLUDE,
                CandidateReasonCode.WEAK_TOTAL_RETURN,
                "稅後總報酬估算未達門檻"
                f"（觀察值 {candidate.estimated_after_tax_total_return_pct}%；"
                f"門檻 {rules.min_after_tax_total_return_pct}%）；"
                "不能只因高配息納入。",
            )
        )
    if candidate.downside_return_pct is None:
        reasons.append(
            _reason(
                CandidateReasonKind.EXCLUDE,
                CandidateReasonCode.MISSING_DOWNSIDE_RISK,
                "缺少下行風險資料。",
            )
        )
    elif candidate.downside_return_pct < rules.min_downside_return_pct:
        reasons.append(
            _reason(
                CandidateReasonKind.EXCLUDE,
                CandidateReasonCode.EXCESSIVE_DOWNSIDE_RISK,
                "觀察期間的價格下跌超過容許門檻"
                f"（觀察值 {candidate.downside_return_pct}%；"
                f"門檻 {rules.min_downside_return_pct}%）。",
            )
        )
    if candidate.annual_after_tax_cash_rate_pct is None:
        reasons.append(
            _reason(
                CandidateReasonKind.EXCLUDE,
                CandidateReasonCode.MISSING_AFTER_TAX_CASH,
                "缺少稅後現金流貢獻估算。",
            )
        )
    elif candidate.annual_after_tax_cash_rate_pct <= 0:
        reasons.append(
            _reason(
                CandidateReasonKind.EXCLUDE,
                CandidateReasonCode.NON_POSITIVE_AFTER_TAX_CASH,
                "稅後現金流貢獻不是正值。",
            )
        )
    if candidate.holding_overlap_pct is None:
        kind = (
            CandidateReasonKind.EXCLUDE
            if rules.require_holding_overlap
            else CandidateReasonKind.TRADEOFF
        )
        reasons.append(
            _reason(
                kind,
                CandidateReasonCode.HOLDING_OVERLAP_UNAVAILABLE,
                "尚無持股重疊資料；不得解讀為零重疊。",
            )
        )
    elif candidate.holding_overlap_pct > rules.max_holding_overlap_pct:
        reasons.append(
            _reason(
                CandidateReasonKind.EXCLUDE,
                CandidateReasonCode.EXCESSIVE_HOLDING_OVERLAP,
                "與基準 ETF 的持股重疊超過門檻"
                f"（觀察值 {candidate.holding_overlap_pct}%；"
                f"門檻 {rules.max_holding_overlap_pct}%）。",
            )
        )
    if candidate.proposed_allocation_pct > rules.max_candidate_allocation_pct:
        reasons.append(
            _reason(
                CandidateReasonKind.EXCLUDE,
                CandidateReasonCode.EXCESSIVE_CONCENTRATION,
                "候選 ETF 的情境配置比例超過集中度門檻"
                f"（配置 {candidate.proposed_allocation_pct}%；"
                f"門檻 {rules.max_candidate_allocation_pct}%）。",
            )
        )
    return reasons


def _result(
    candidate: MonthlyCombinationCandidateInput,
    *,
    selected: bool,
    supported_months: list[int],
    reasons: list[CandidateReason],
) -> MonthlyCombinationCandidateResult:
    return MonthlyCombinationCandidateResult(
        etf_code=candidate.etf_code,
        name=candidate.name,
        is_active=candidate.is_active,
        is_bond=candidate.is_bond,
        selected=selected,
        supported_gap_months=supported_months,
        stable_payment_months=candidate.stable_payment_months,
        completeness_pct=candidate.completeness_pct,
        data_is_fresh=candidate.data_is_fresh,
        distribution_stability_pct=(
            candidate.distribution_stability_pct
        ),
        annual_after_tax_cash_rate_pct=(
            candidate.annual_after_tax_cash_rate_pct
        ),
        estimated_after_tax_total_return_pct=(
            candidate.estimated_after_tax_total_return_pct
        ),
        downside_return_pct=candidate.downside_return_pct,
        holding_overlap_pct=candidate.holding_overlap_pct,
        proposed_allocation_pct=candidate.proposed_allocation_pct,
        reasons=reasons,
    )


def calculate_monthly_payment_combination(
    value: MonthlyCombinationCalculationInput,
) -> MonthlyCombinationCalculationResult:
    """先通過品質與報酬規則，再依可補月份挑選至多三檔。"""

    if value.base_payment_months is None:
        base_issue = _reason(
            CandidateReasonKind.EXCLUDE,
            CandidateReasonCode.BASE_MONTHLY_DATA_UNAVAILABLE,
            "基準 ETF 缺少付款月份資料，無法建立組合情境。",
        )
        return MonthlyCombinationCalculationResult(
            status=MonthlyCombinationStatus.UNAVAILABLE,
            base_etf_code=value.base_etf_code,
            base_etf_name=value.base_etf_name,
            base_payment_months=None,
            initial_gap_months=None,
            selected_candidates=[],
            rejected_candidates=[
                _result(
                    candidate,
                    selected=False,
                    supported_months=[],
                    reasons=[base_issue],
                )
                for candidate in value.candidates
            ],
            combined_payment_months=None,
            remaining_gap_months=None,
            tradeoffs=[base_issue],
        )

    base_months = set(value.base_payment_months)
    initial_gaps = sorted(ALL_MONTHS - base_months)
    if not value.monthly_coverage_enabled:
        disabled = _reason(
            CandidateReasonKind.EXCLUDE,
            CandidateReasonCode.MONTHLY_COVERAGE_DISABLED,
            "使用者未啟用月配缺口組合。",
        )
        return MonthlyCombinationCalculationResult(
            status=MonthlyCombinationStatus.AVAILABLE,
            base_etf_code=value.base_etf_code,
            base_etf_name=value.base_etf_name,
            base_payment_months=sorted(base_months),
            initial_gap_months=initial_gaps,
            selected_candidates=[],
            rejected_candidates=[
                _result(
                    candidate,
                    selected=False,
                    supported_months=[],
                    reasons=[disabled],
                )
                for candidate in value.candidates
            ],
            combined_payment_months=sorted(base_months),
            remaining_gap_months=initial_gaps,
        )

    evaluated = []
    for candidate in value.candidates:
        reasons = _eligibility_reasons(candidate, value)
        supported = sorted(
            set(candidate.stable_payment_months) & set(initial_gaps)
        )
        if not supported:
            reasons.append(
                _reason(
                    CandidateReasonKind.EXCLUDE,
                    CandidateReasonCode.NO_GAP_CONTRIBUTION,
                    "未支援基準 ETF 的付款缺口月份。",
                )
            )
        evaluated.append((candidate, reasons, supported))

    eligible = [
        item
        for item in evaluated
        if not any(
            reason.kind == CandidateReasonKind.EXCLUDE
            for reason in item[1]
        )
    ]
    remaining_gaps = set(initial_gaps)
    selected_codes: set[str] = set()
    selected_results: list[MonthlyCombinationCandidateResult] = []
    extra_rejections: dict[str, CandidateReason] = {}
    remaining_eligible = list(eligible)

    while (
        remaining_eligible
        and len(selected_results) < value.max_complementary_etfs
    ):
        remaining_eligible.sort(
            key=lambda item: (
                -len(
                    set(item[0].stable_payment_months) & remaining_gaps
                ),
                -(
                    item[0].estimated_after_tax_total_return_pct
                    if item[0].estimated_after_tax_total_return_pct is not None
                    else Decimal("-100")
                ),
                -(
                    item[0].annual_after_tax_cash_rate_pct
                    if item[0].annual_after_tax_cash_rate_pct is not None
                    else Decimal("0")
                ),
                item[0].etf_code,
            )
        )
        candidate, reasons, _ = remaining_eligible.pop(0)
        current_support = sorted(
            set(candidate.stable_payment_months) & remaining_gaps
        )
        if not current_support:
            remaining_eligible.insert(0, (candidate, reasons, []))
            break
        include_reasons = [
            *reasons,
            _reason(
                CandidateReasonKind.INCLUDE,
                CandidateReasonCode.PASSES_ELIGIBILITY,
                "通過資料品質、現金流、總報酬與風險門檻。",
            ),
            _reason(
                CandidateReasonKind.INCLUDE,
                CandidateReasonCode.SUPPORTS_PAYMENT_MONTHS,
                "支援目前尚未覆蓋的付款月份。",
                current_support,
            ),
        ]
        selected_results.append(
            _result(
                candidate,
                selected=True,
                supported_months=current_support,
                reasons=include_reasons,
            )
        )
        selected_codes.add(candidate.etf_code)
        remaining_gaps -= set(current_support)

    for candidate, _, _ in remaining_eligible:
        current_support = set(candidate.stable_payment_months) & remaining_gaps
        if current_support:
            extra_rejections[candidate.etf_code] = _reason(
                CandidateReasonKind.EXCLUDE,
                CandidateReasonCode.MAX_COMPLEMENTARY_ETFS_REACHED,
                "已達使用者設定的互補 ETF 數量上限。",
            )
        else:
            extra_rejections[candidate.etf_code] = _reason(
                CandidateReasonKind.EXCLUDE,
                CandidateReasonCode.REDUNDANT_MONTH_COVERAGE,
                "缺口月份已由排序較前的候選 ETF 支援。",
            )

    rejected_results = []
    for candidate, reasons, supported in evaluated:
        if candidate.etf_code in selected_codes:
            continue
        extra = extra_rejections.get(candidate.etf_code)
        rejected_results.append(
            _result(
                candidate,
                selected=False,
                supported_months=supported,
                reasons=[*reasons, *([extra] if extra else [])],
            )
        )

    tradeoffs = [
        reason
        for result in selected_results
        for reason in result.reasons
        if reason.kind == CandidateReasonKind.TRADEOFF
    ]
    combined = ALL_MONTHS - remaining_gaps
    return MonthlyCombinationCalculationResult(
        status=(
            MonthlyCombinationStatus.PARTIAL
            if tradeoffs
            else MonthlyCombinationStatus.AVAILABLE
        ),
        base_etf_code=value.base_etf_code,
        base_etf_name=value.base_etf_name,
        base_payment_months=sorted(base_months),
        initial_gap_months=initial_gaps,
        selected_candidates=selected_results,
        rejected_candidates=rejected_results,
        combined_payment_months=sorted(combined),
        remaining_gap_months=sorted(remaining_gaps),
        tradeoffs=tradeoffs,
    )
