"""M11-2 已儲存手動持倉的整體目標分析。"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from backend.app.models.cash_flow_analysis import AnalysisMode, CalculationContext
from backend.app.models.decision_profile import (
    CurrentHoldingAnalysisResponse,
    CurrentHoldingFact,
    UserConditionsResponse,
)
from backend.app.models.target_analysis import (
    TargetAnalysisRequest,
    TargetAnalysisStatus,
    TargetAnalysisUnavailableField,
    TargetAnalysisWarning,
    TargetAnalysisWarningCode,
)
from backend.app.repositories.decision_profile_repository import (
    get_user_conditions,
    list_manual_holdings,
)
from backend.app.services.target_analysis_calculator import calculate_target_analysis
from backend.app.services.target_analysis_data import load_target_analysis_data


_HUNDRED = Decimal("100")
_AMOUNT_QUANTUM = Decimal("0.000001")
_PERCENT_QUANTUM = Decimal("0.000001")
_PERFORMANCE_PERIOD_YEARS = {
    "1Y": Decimal("1"),
    "3Y": Decimal("3"),
    "5Y": Decimal("5"),
}


def _decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _date(value: object, fallback: date) -> date:
    if isinstance(value, date):
        return value
    if value is not None:
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            pass
    return fallback


def annualize_price_return(performance: dict | None) -> Decimal | None:
    """將 PRICE_RETURN 期間報酬換成情境估算所需的年化報酬。"""

    if performance is None:
        return None
    years = _PERFORMANCE_PERIOD_YEARS.get(str(performance.get("period_code", "")))
    period_return = _decimal(performance.get("return_pct"))
    if years is None or period_return is None:
        return None
    if period_return == Decimal("-100"):
        return Decimal("-100.000000")
    growth_factor = Decimal("1") + period_return / _HUNDRED
    annual_factor = growth_factor ** (Decimal("1") / years)
    return ((annual_factor - Decimal("1")) * _HUNDRED).quantize(
        _PERCENT_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def _unavailable(field: str, reason: str) -> TargetAnalysisUnavailableField:
    return TargetAnalysisUnavailableField(field=field, reason=reason)


def _append_unavailable(
    items: list[TargetAnalysisUnavailableField],
    *,
    field: str,
    reason: str,
) -> None:
    if any(item.field == field for item in items):
        return
    items.append(_unavailable(field, reason))


def analyze_holding_snapshot(
    database_path: str | Path,
    *,
    condition_row: dict,
    holding_rows: list[dict],
    as_of_date: date | None = None,
) -> CurrentHoldingAnalysisResponse:
    """彙總指定持倉快照後，只執行一次既有 M10 目標計算器。"""

    analysis_date = as_of_date or date.today()
    conditions = UserConditionsResponse(**condition_row)
    if not holding_rows:
        return CurrentHoldingAnalysisResponse(
            status=TargetAnalysisStatus.UNAVAILABLE,
            analysis_date=analysis_date,
            conditions=conditions,
            holdings=[],
            unavailable_fields=[
                _unavailable("holdings", "尚未建立手動持有部位")
            ],
        )

    facts: list[CurrentHoldingFact] = []
    total_current_value = Decimal("0")
    current_value_complete = True
    total_gross_cash = Decimal("0")
    gross_cash_complete = True
    weighted_price_return = Decimal("0")
    price_return_complete = True
    period_starts: list[date] = []
    period_ends: list[date] = []
    top_level_unavailable: list[TargetAnalysisUnavailableField] = []

    for holding in holding_rows:
        units = int(holding["held_units"])
        unit_price = _decimal(holding.get("unit_price"))
        current_value = unit_price * units if unit_price is not None else None
        if current_value is None:
            current_value_complete = False
        else:
            total_current_value += current_value
        loaded = load_target_analysis_data(
            etf_code=holding["etf_code"],
            database_path=database_path,
            history_years=conditions.history_years,
            as_of_date=analysis_date,
        )
        monthly = loaded.monthly_income
        period_starts.append(_date(monthly.get("window_start_date"), analysis_date))
        period_ends.append(_date(monthly.get("as_of_date"), analysis_date))

        fact_warnings = list(loaded.warnings)
        fact_unavailable = list(loaded.unavailable_fields)
        if current_value is None:
            _append_unavailable(
                fact_unavailable,
                field="current_value",
                reason="尚無可信的已保存官方收盤價",
            )
        total_per_unit = _decimal(monthly.get("total_amount_per_unit"))
        analysis_currency = monthly.get("analysis_currency")
        currency_compatible = analysis_currency == conditions.currency
        annual_gross_cash = None
        if (
            total_per_unit is None
            or monthly.get("has_mixed_currencies", False)
            or not currency_compatible
        ):
            gross_cash_complete = False
            reason = (
                "配息幣別與手動持倉的 TWD 參考價不相容"
                if analysis_currency not in (None, conditions.currency)
                else "沒有可用且幣別一致的配息現金資料"
            )
            _append_unavailable(
                fact_unavailable,
                field="annual_gross_distribution_cash",
                reason=reason,
            )
            if analysis_currency not in (None, conditions.currency):
                fact_warnings.append(
                    TargetAnalysisWarning(
                        code=TargetAnalysisWarningCode.MIXED_CURRENCY,
                        message=reason,
                        affected_fields=["annual_gross_distribution_cash"],
                    )
                )
        else:
            annual_gross_cash = (
                total_per_unit
                * units
                / Decimal(conditions.history_years)
            ).quantize(
                _AMOUNT_QUANTUM,
                rounding=ROUND_HALF_UP,
            )
            total_gross_cash += annual_gross_cash

        annualized_return = annualize_price_return(loaded.selected_performance)
        if annualized_return is None:
            price_return_complete = False
            _append_unavailable(
                fact_unavailable,
                field="annualized_price_return_pct",
                reason="沒有可用的期間價格報酬資料",
            )
        elif current_value is not None:
            weighted_price_return += current_value * annualized_return

        prefixed_unavailable = [
            item.model_copy(update={"field": f"holdings.{holding['etf_code']}.{item.field}"})
            for item in fact_unavailable
        ]
        top_level_unavailable.extend(prefixed_unavailable)
        facts.append(
            CurrentHoldingFact(
                etf_code=holding["etf_code"],
                name=holding["name"],
                held_units=units,
                unit_price=unit_price,
                current_value=current_value,
                annual_gross_distribution_cash=annual_gross_cash,
                price_return_period_code=(
                    str(loaded.selected_performance.get("period_code"))
                    if loaded.selected_performance is not None
                    else None
                ),
                annualized_price_return_pct=annualized_return,
                warnings=fact_warnings,
                unavailable_fields=fact_unavailable,
            )
        )

    if not current_value_complete:
        _append_unavailable(
            top_level_unavailable,
            field="total_current_value",
            reason="部分持股尚無可信的已保存官方收盤價",
        )
        return CurrentHoldingAnalysisResponse(
            status=TargetAnalysisStatus.PARTIAL,
            analysis_date=analysis_date,
            conditions=conditions,
            total_current_value=None,
            holdings=facts,
            portfolio_analysis=None,
            unavailable_fields=top_level_unavailable,
        )

    portfolio_gross_cash = total_gross_cash if gross_cash_complete else None
    portfolio_cash_rate = (
        (total_gross_cash / total_current_value * _HUNDRED).quantize(
            _PERCENT_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
        if gross_cash_complete
        else None
    )
    portfolio_price_return = (
        (weighted_price_return / total_current_value).quantize(
            _PERCENT_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
        if price_return_complete
        else None
    )

    deduction_rate = conditions.cash_deduction_rate_pct
    total_deductions = (
        total_gross_cash * deduction_rate / _HUNDRED
        if gross_cash_complete and deduction_rate is not None
        else None
    )
    zero = Decimal("0") if total_deductions is not None else None

    request = TargetAnalysisRequest(
        held_units=1,
        unit_price=total_current_value,
        monthly_after_tax_target=conditions.monthly_after_tax_target,
        analysis_years=conditions.analysis_years,
        history_years=conditions.history_years,
        cash_deduction_rate_pct=deduction_rate,
    )
    portfolio_analysis = calculate_target_analysis(
        request,
        context=CalculationContext(
            mode=AnalysisMode.SCENARIO_ESTIMATE,
            currency="TWD",
            period_start=min(period_starts),
            period_end=max(period_ends),
        ),
        gross_distribution_cash=portfolio_gross_cash,
        distribution_tax=zero,
        supplementary_premium=zero,
        other_distribution_costs=total_deductions,
        annual_gross_cash_rate_pct=portfolio_cash_rate,
        annual_price_return_pct=portfolio_price_return,
    )

    seen_fields = {item.field for item in top_level_unavailable}
    for item in portfolio_analysis.unavailable_fields:
        if item.field not in seen_fields:
            seen_fields.add(item.field)
            top_level_unavailable.append(item)

    return CurrentHoldingAnalysisResponse(
        status=(
            TargetAnalysisStatus.PARTIAL
            if top_level_unavailable
            else TargetAnalysisStatus.AVAILABLE
        ),
        analysis_date=analysis_date,
        conditions=conditions,
        total_current_value=total_current_value,
        holdings=facts,
        portfolio_analysis=portfolio_analysis,
        unavailable_fields=top_level_unavailable,
    )


def analyze_current_holdings(
    database_path: str | Path,
    *,
    as_of_date: date | None = None,
) -> CurrentHoldingAnalysisResponse:
    """載入已儲存條件與持倉，建立目前持倉分析。"""

    analysis_date = as_of_date or date.today()
    condition_row = get_user_conditions(database_path)
    if condition_row is None:
        return CurrentHoldingAnalysisResponse(
            status=TargetAnalysisStatus.UNAVAILABLE,
            analysis_date=analysis_date,
            conditions=None,
            holdings=[],
            unavailable_fields=[
                _unavailable("conditions", "尚未儲存固定分析條件")
            ],
        )
    return analyze_holding_snapshot(
        database_path,
        condition_row=condition_row,
        holding_rows=list_manual_holdings(database_path),
        as_of_date=analysis_date,
    )
