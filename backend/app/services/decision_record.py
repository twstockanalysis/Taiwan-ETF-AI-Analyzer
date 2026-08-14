"""M11-4 候選分析快照、理由與替代方案建立服務。"""

from pathlib import Path

from backend.app.models.decision_profile import (
    CandidateHoldingAnalysisRequest,
    CandidateHoldingAnalysisResponse,
    DecisionRecordNote,
    DecisionRecordResponse,
)
from backend.app.repositories.decision_record_repository import (
    create_decision_record,
)
from backend.app.services.candidate_holding_analysis import (
    analyze_candidate_holding,
)


_ALTERNATIVES = {
    "INCOMPLETE_DATA": (
        "COMPLETE_REQUIRED_DATA",
        "先補齊候選 ETF 的配息與績效資料，再建立新的比較快照。",
    ),
    "STALE_DATA": (
        "REFRESH_MARKET_DATA",
        "更新候選 ETF 的績效或配息資料後重新比較。",
    ),
    "UNSTABLE_DISTRIBUTIONS": (
        "COMPARE_STABLER_DISTRIBUTION",
        "比較配息月份穩定度符合目前門檻的其他候選 ETF。",
    ),
    "MISSING_TOTAL_RETURN": (
        "OBTAIN_TOTAL_RETURN_FACTS",
        "取得可用的價格報酬歷史後，再評估總報酬與本金風險。",
    ),
    "WEAK_TOTAL_RETURN": (
        "COMPARE_TOTAL_RETURN_ALTERNATIVE",
        "比較總報酬門檻較合適的其他候選，不以配息月份取代總報酬檢查。",
    ),
    "MISSING_DOWNSIDE_RISK": (
        "OBTAIN_DOWNSIDE_FACTS",
        "取得可用的下行期間資料後，再評估本金風險。",
    ),
    "EXCESSIVE_DOWNSIDE_RISK": (
        "COMPARE_LOWER_DOWNSIDE_ALTERNATIVE",
        "比較下行風險符合目前門檻的其他候選 ETF。",
    ),
    "MISSING_AFTER_TAX_CASH": (
        "SAVE_CASH_DEDUCTION_ASSUMPTION",
        "先儲存現金扣減率假設，再建立可比較的稅後現金流快照。",
    ),
    "NON_POSITIVE_AFTER_TAX_CASH": (
        "COMPARE_POSITIVE_CASH_ALTERNATIVE",
        "比較稅後可用現金為正且仍通過風險門檻的候選 ETF。",
    ),
    "HOLDING_OVERLAP_UNAVAILABLE": (
        "REFRESH_CONSTITUENT_DATA",
        "更新目前持倉與候選 ETF 的正式成分股快照後再比較；未知值不視為零。",
    ),
    "EXCESSIVE_HOLDING_OVERLAP": (
        "COMPARE_LOWER_OVERLAP_ALTERNATIVE",
        "比較與目前持倉重疊較低的候選 ETF。",
    ),
    "EXCESSIVE_CONCENTRATION": (
        "REDUCE_PROPOSED_UNITS",
        "降低預計增加單位數，重新檢查候選配置比例。",
    ),
    "NO_GAP_CONTRIBUTION": (
        "COMPARE_DIFFERENT_PAYMENT_MONTHS",
        "若仍需要月月領息，再比較能補足缺口月份且先通過風險門檻的候選。",
    ),
    "REDUNDANT_MONTH_COVERAGE": (
        "COMPARE_DIFFERENT_PAYMENT_MONTHS",
        "若仍需要月月領息，再比較能補足未覆蓋月份的候選。",
    ),
    "BASE_MONTHLY_DATA_UNAVAILABLE": (
        "COMPLETE_CURRENT_HOLDING_MONTHS",
        "先補齊目前持倉的付款月份資料，再比較月配缺口。",
    ),
}


def _note(reason) -> DecisionRecordNote:
    return DecisionRecordNote(
        code=reason.code.value,
        message=reason.message,
        affected_months=reason.affected_months,
    )


def _candidate_result(analysis: CandidateHoldingAnalysisResponse):
    eligibility = analysis.eligibility
    if eligibility is None:
        return None, False
    if eligibility.selected_candidates:
        return eligibility.selected_candidates[0], True
    if eligibility.rejected_candidates:
        return eligibility.rejected_candidates[0], False
    return None, False


def _build_record_content(analysis: CandidateHoldingAnalysisResponse):
    candidate, selected = _candidate_result(analysis)
    reasons = candidate.reasons if candidate is not None else []
    reason_codes = {reason.code.value for reason in reasons}
    if analysis.status.value == "UNAVAILABLE":
        outcome = "UNAVAILABLE"
    elif "MONTHLY_COVERAGE_DISABLED" in reason_codes:
        outcome = "NOT_EVALUATED"
    elif selected:
        outcome = "ELIGIBLE"
    else:
        outcome = "INELIGIBLE"

    rationale = [
        _note(reason)
        for reason in reasons
        if reason.kind.value == "INCLUDE"
    ]
    exclusions = [
        _note(reason)
        for reason in reasons
        if reason.kind.value == "EXCLUDE"
    ]
    alternatives = []
    seen_alternatives = set()
    for reason in reasons:
        mapped = _ALTERNATIVES.get(reason.code.value)
        if mapped is None or mapped[0] in seen_alternatives:
            continue
        seen_alternatives.add(mapped[0])
        alternatives.append(
            DecisionRecordNote(code=mapped[0], message=mapped[1])
        )
    if not alternatives:
        alternatives.append(
            DecisionRecordNote(
                code="COMPARE_ANOTHER_SCENARIO",
                message=(
                    "可用相同門檻比較另一個候選或不同投入單位；"
                    "新分析應另存為新快照。"
                ),
            )
        )

    risk_notes = [
        DecisionRecordNote(
            code="USER_ENTERED_REFERENCE_PRICE",
            message="候選價格與單位數為使用者輸入的 TWD 情境，不是即時報價。",
        ),
        DecisionRecordNote(
            code="SCENARIO_NOT_ADVICE",
            message="本紀錄是估算快照，不是投資建議、報酬保證或交易指示。",
        ),
        DecisionRecordNote(
            code="NO_BROKER_OR_TRADING",
            message="系統未連接券商，也不會讀取帳戶或送出交易。",
        ),
        DecisionRecordNote(
            code="IMMUTABLE_SNAPSHOT",
            message="此紀錄不隨後續條件、持倉或市場資料更新；重新分析會新增另一筆。",
        ),
    ]
    risk_notes.extend(
        _note(reason)
        for reason in reasons
        if reason.kind.value == "TRADEOFF"
    )
    risk_notes.extend(
        DecisionRecordNote(
            code="UNAVAILABLE_ANALYSIS_FIELD",
            message=f"{item.field}：{item.reason}",
        )
        for item in analysis.unavailable_fields
    )
    return outcome, rationale, exclusions, alternatives, risk_notes


def create_candidate_decision_record(
    candidate_code: str,
    request: CandidateHoldingAnalysisRequest,
    database_path: str | Path,
) -> DecisionRecordResponse | None:
    """重新執行伺服器端分析並保存完整快照，避免信任前端結果。"""

    analysis = analyze_candidate_holding(
        candidate_code,
        request,
        database_path,
    )
    if analysis is None:
        return None
    outcome, rationale, exclusions, alternatives, risk_notes = (
        _build_record_content(analysis)
    )
    record = create_decision_record(
        candidate_etf_code=analysis.candidate_etf_code,
        candidate_name=analysis.candidate_name,
        analysis_status=analysis.status.value,
        outcome=outcome,
        request=request.model_dump(mode="json"),
        analysis=analysis.model_dump(mode="json"),
        rationale=[item.model_dump(mode="json") for item in rationale],
        exclusions=[item.model_dump(mode="json") for item in exclusions],
        alternatives=[item.model_dump(mode="json") for item in alternatives],
        risk_notes=[item.model_dump(mode="json") for item in risk_notes],
        database_path=database_path,
    )
    return DecisionRecordResponse.model_validate(record)
