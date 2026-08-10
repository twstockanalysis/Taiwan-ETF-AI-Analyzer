"""M11-3 候選 ETF 加入目前持倉前後的唯讀比較。"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from backend.app.models.decision_profile import (
    CandidateHoldingAnalysisRequest,
    CandidateHoldingAnalysisResponse,
    CandidatePortfolioComparison,
)
from backend.app.models.monthly_combination import (
    MonthlyCombinationCalculationInput,
    MonthlyCombinationCandidateAssumption,
)
from backend.app.models.target_analysis import (
    TargetAnalysisStatus,
    TargetAnalysisUnavailableField,
)
from backend.app.repositories.decision_profile_repository import (
    get_user_conditions,
    list_manual_holdings,
)
from backend.app.repositories.etf_repository import get_etf_by_code
from backend.app.repositories.monthly_income_repository import (
    build_monthly_income_distribution,
)
from backend.app.repositories.performance_repository import (
    list_latest_etf_performance,
)
from backend.app.services.current_holding_analysis import (
    analyze_holding_snapshot,
)
from backend.app.services.monthly_combination_calculator import (
    calculate_monthly_payment_combination,
)
from backend.app.services.monthly_combination_data import (
    build_candidate_input,
    stable_payment_months,
)


_PERCENT_QUANTUM = Decimal("0.000001")


def _unavailable(field: str, reason: str) -> TargetAnalysisUnavailableField:
    return TargetAnalysisUnavailableField(field=field, reason=reason)


def _decimal(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _difference(after: Decimal | None, before: Decimal | None) -> Decimal | None:
    if after is None or before is None:
        return None
    return after - before


def _portfolio_value(response, section: str, field: str) -> Decimal | None:
    if response.portfolio_analysis is None:
        return None
    value = getattr(getattr(response.portfolio_analysis, section), field)
    return _decimal(value)


def _merge_candidate_holding(
    holdings: list[dict],
    *,
    candidate_etf: dict,
    request: CandidateHoldingAnalysisRequest,
) -> list[dict]:
    """以價值加權參考價合併同代號，不變更資料庫。"""

    result = [dict(item) for item in holdings]
    additional_value = request.unit_price * request.proposed_units
    for index, item in enumerate(result):
        if item["etf_code"] != candidate_etf["code"]:
            continue
        existing_units = int(item["held_units"])
        combined_units = existing_units + request.proposed_units
        combined_value = (
            Decimal(str(item["unit_price"])) * existing_units
            + additional_value
        )
        result[index] = {
            **item,
            "held_units": combined_units,
            "unit_price": combined_value / combined_units,
            "price_as_of_date": None,
        }
        return result

    result.append(
        {
            "etf_code": candidate_etf["code"],
            "name": candidate_etf["name"],
            "is_active": bool(candidate_etf["is_active"]),
            "is_bond": bool(candidate_etf["is_bond"]),
            "held_units": request.proposed_units,
            "unit_price": request.unit_price,
            "price_as_of_date": None,
            "currency": "TWD",
        }
    )
    return result


def _base_payment_months(
    holdings: list[dict],
    *,
    database_path: str | Path,
    lookback_years: int,
    minimum_stability_pct: Decimal,
) -> list[int] | None:
    months: set[int] = set()
    for holding in holdings:
        monthly = build_monthly_income_distribution(
            holding["etf_code"],
            database_path,
            lookback_years,
        )
        holding_months = stable_payment_months(
            monthly,
            lookback_years=lookback_years,
            minimum_stability_pct=minimum_stability_pct,
        )
        if holding_months is None:
            return None
        months.update(holding_months)
    return sorted(months)


def _comparison(current, proposed, additional_capital: Decimal):
    before_cash = _portfolio_value(
        current, "cash_flow", "after_tax_usable_cash"
    )
    after_cash = _portfolio_value(
        proposed, "cash_flow", "after_tax_usable_cash"
    )
    before_coverage = _portfolio_value(
        current, "cash_flow", "target_coverage_pct"
    )
    after_coverage = _portfolio_value(
        proposed, "cash_flow", "target_coverage_pct"
    )
    before_shortfall = _portfolio_value(
        current, "cash_flow", "funding_shortfall"
    )
    after_shortfall = _portfolio_value(
        proposed, "cash_flow", "funding_shortfall"
    )
    before_return = _portfolio_value(
        current, "scenario_estimate", "after_tax_total_return_pct"
    )
    after_return = _portfolio_value(
        proposed, "scenario_estimate", "after_tax_total_return_pct"
    )
    return CandidatePortfolioComparison(
        additional_capital=additional_capital,
        total_value_before=current.total_current_value or Decimal("0"),
        total_value_after=proposed.total_current_value or Decimal("0"),
        annual_after_tax_cash_before=before_cash,
        annual_after_tax_cash_after=after_cash,
        annual_after_tax_cash_delta=_difference(after_cash, before_cash),
        target_coverage_pct_before=before_coverage,
        target_coverage_pct_after=after_coverage,
        target_coverage_pct_delta=_difference(after_coverage, before_coverage),
        funding_shortfall_before=before_shortfall,
        funding_shortfall_after=after_shortfall,
        funding_shortfall_reduction=_difference(
            before_shortfall, after_shortfall
        ),
        after_tax_total_return_pct_before=before_return,
        after_tax_total_return_pct_after=after_return,
        after_tax_total_return_pct_delta=_difference(
            after_return, before_return
        ),
    )


def analyze_candidate_holding(
    candidate_code: str,
    request: CandidateHoldingAnalysisRequest,
    database_path: str | Path,
    *,
    as_of_date: date | None = None,
) -> CandidateHoldingAnalysisResponse | None:
    """比較候選加入前後，並重用 M10-5 排除與理由契約。"""

    analysis_date = as_of_date or date.today()
    normalized_code = candidate_code.strip().upper()
    candidate_etf = get_etf_by_code(normalized_code, database_path)
    if candidate_etf is None:
        return None

    condition_row = get_user_conditions(database_path)
    if condition_row is None:
        return CandidateHoldingAnalysisResponse(
            status=TargetAnalysisStatus.UNAVAILABLE,
            analysis_date=analysis_date,
            candidate_etf_code=normalized_code,
            candidate_name=candidate_etf["name"],
            unavailable_fields=[
                _unavailable("conditions", "尚未儲存固定分析條件")
            ],
        )
    holdings = list_manual_holdings(database_path)
    if not holdings:
        return CandidateHoldingAnalysisResponse(
            status=TargetAnalysisStatus.UNAVAILABLE,
            analysis_date=analysis_date,
            candidate_etf_code=normalized_code,
            candidate_name=candidate_etf["name"],
            unavailable_fields=[
                _unavailable("holdings", "尚未建立目前手動持有部位")
            ],
        )

    current = analyze_holding_snapshot(
        database_path,
        condition_row=condition_row,
        holding_rows=holdings,
        as_of_date=analysis_date,
    )
    if current.total_current_value is None:
        return CandidateHoldingAnalysisResponse(
            status=TargetAnalysisStatus.PARTIAL,
            analysis_date=analysis_date,
            candidate_etf_code=normalized_code,
            candidate_name=candidate_etf["name"],
            current_portfolio=current,
            unavailable_fields=[
                _unavailable(
                    "current.total_current_value",
                    "目前持股缺少可信的已保存官方收盤價",
                )
            ],
        )
    proposed_holdings = _merge_candidate_holding(
        holdings,
        candidate_etf=candidate_etf,
        request=request,
    )
    proposed = analyze_holding_snapshot(
        database_path,
        condition_row=condition_row,
        holding_rows=proposed_holdings,
        as_of_date=analysis_date,
    )

    candidate_total_value = sum(
        Decimal(str(item["unit_price"])) * int(item["held_units"])
        for item in proposed_holdings
        if item["etf_code"] == normalized_code
    )
    proposed_total = proposed.total_current_value or Decimal("0")
    proposed_allocation_pct = (
        candidate_total_value / proposed_total * Decimal("100")
    ).quantize(_PERCENT_QUANTUM, rounding=ROUND_HALF_UP)
    assumption = MonthlyCombinationCandidateAssumption(
        etf_code=normalized_code,
        unit_price=request.unit_price,
        proposed_allocation_pct=proposed_allocation_pct,
        holding_overlap_pct=request.holding_overlap_pct,
    )
    conditions = current.conditions
    assert conditions is not None
    monthly = build_monthly_income_distribution(
        normalized_code,
        database_path,
        conditions.history_years,
    )
    candidate_input = build_candidate_input(
        etf=candidate_etf,
        assumption=assumption,
        monthly_income=monthly,
        performance_rows=list_latest_etf_performance(
            normalized_code, database_path
        ),
        lookback_years=conditions.history_years,
        cash_deduction_rate_pct=conditions.cash_deduction_rate_pct,
        rules=request.rules,
        as_of_date=analysis_date,
    )
    eligibility = calculate_monthly_payment_combination(
        MonthlyCombinationCalculationInput(
            base_etf_code="CURRENT",
            base_etf_name="目前持倉",
            base_payment_months=_base_payment_months(
                holdings,
                database_path=database_path,
                lookback_years=conditions.history_years,
                minimum_stability_pct=(
                    request.rules.min_distribution_stability_pct
                ),
            ),
            candidates=[candidate_input],
            max_complementary_etfs=1,
            monthly_coverage_enabled=request.monthly_coverage_enabled,
            rules=request.rules,
        )
    )

    unavailable_fields = [
        item.model_copy(update={"field": f"current.{item.field}"})
        for item in current.unavailable_fields
    ]
    unavailable_fields.extend(
        item.model_copy(update={"field": f"proposed.{item.field}"})
        for item in proposed.unavailable_fields
    )
    status = (
        TargetAnalysisStatus.PARTIAL
        if unavailable_fields or eligibility.status.value != "AVAILABLE"
        else TargetAnalysisStatus.AVAILABLE
    )
    return CandidateHoldingAnalysisResponse(
        status=status,
        analysis_date=analysis_date,
        candidate_etf_code=normalized_code,
        candidate_name=candidate_etf["name"],
        current_portfolio=current,
        proposed_portfolio=proposed,
        comparison=_comparison(
            current,
            proposed,
            request.unit_price * request.proposed_units,
        ),
        eligibility=eligibility,
        unavailable_fields=unavailable_fields,
    )
