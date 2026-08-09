"""單一 ETF 目標分析 API。"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
_PERCENT_QUANTUM = Decimal("0.000001")
_PERFORMANCE_PERIOD_YEARS = {
    "1Y": Decimal("1"),
    "3Y": Decimal("3"),
    "5Y": Decimal("5"),
}
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from backend.app.api.dependencies import (
    get_database_path,
)
from backend.app.models.cash_flow_analysis import (
    AnalysisMode,
    CalculationContext,
)
from backend.app.models.target_analysis import (
    TargetAnalysisRequest,
    TargetAnalysisResult,
    TargetAnalysisStatus,
)
from backend.app.models.tax_reinvestment import (
    TaxReinvestmentAnalysisRequest,
    TaxReinvestmentAnalysisResult,
    TaxReinvestmentCalculationInput,
    TaxReinvestmentHistoricalFacts,
)
from backend.app.repositories.dividend_repository import (
    list_etf_actual_component_history,
)
from backend.app.repositories.etf_repository import (
    get_etf_by_code,
)
from backend.app.services.target_analysis_calculator import (
    calculate_target_analysis,
)
from backend.app.services.target_analysis_data import (
    load_target_analysis_data,
)
from backend.app.services.tax_reinvestment_calculator import (
    calculate_tax_reinvestment_scenarios,
)
from backend.app.services.tax_reinvestment_data import (
    select_latest_complete_actual_mix,
)


router = APIRouter(
    prefix="/api/v1/etfs",
    tags=["Target Analysis"],
)


def _to_decimal(value) -> Decimal | None:
    """將資料欄位安全轉成 Decimal。"""

    if value is None:
        return None

    return Decimal(str(value))


def _to_date(value) -> date:
    """將資料欄位轉成日期。"""

    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value))


def _annualize_price_return(
    performance: dict | None,
) -> Decimal | None:
    """將 1Y/3Y/5Y 期間價格報酬轉為年化報酬。"""

    if performance is None:
        return None
    period_code = str(performance.get("period_code", ""))
    years = _PERFORMANCE_PERIOD_YEARS.get(period_code)
    period_return = _to_decimal(performance.get("return_pct"))
    if years is None or period_return is None:
        return None
    if period_return == Decimal("-100"):
        return Decimal("-100.000000")

    growth_factor = Decimal("1") + period_return / Decimal("100")
    annual_factor = growth_factor ** (Decimal("1") / years)
    return ((annual_factor - Decimal("1")) * Decimal("100")).quantize(
        _PERCENT_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


@router.post(
    "/{code}/target-analysis",
    response_model=TargetAnalysisResult,
    summary="分析單一 ETF 投資目標",
)
def analyze_etf_target(
    code: str,
    request: TargetAnalysisRequest,
    database_path: Path = Depends(
        get_database_path
    ),
) -> TargetAnalysisResult:
    """載入 ETF 資料並執行目標分析。"""

    normalized_code = code.strip().upper()

    etf = get_etf_by_code(
        normalized_code,
        database_path,
    )

    if etf is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到 ETF：{normalized_code}",
        )

    analysis_date = date.today()

    loaded_data = load_target_analysis_data(
        etf_code=normalized_code,
        database_path=database_path,
        history_years=request.history_years,
        as_of_date=analysis_date,
    )

    monthly_income = loaded_data.monthly_income

    context = CalculationContext(
        mode=AnalysisMode.SCENARIO_ESTIMATE,
        currency=monthly_income[
            "analysis_currency"
        ],
        period_start=_to_date(
            monthly_income["window_start_date"]
        ),
        period_end=_to_date(
            monthly_income["as_of_date"]
        ),
    )

    total_amount_per_unit = _to_decimal(
        monthly_income.get(
            "total_amount_per_unit"
        )
    )

    gross_distribution_cash = None
    annual_gross_cash_rate_pct = None

    if total_amount_per_unit is not None:
        history_years = Decimal(
            str(request.history_years)
        )
        annual_amount_per_unit = (
            total_amount_per_unit
            / history_years
        )

        gross_distribution_cash = (
            annual_amount_per_unit
            * Decimal(str(request.held_units))
        )

        annual_gross_cash_rate_pct = (
            annual_amount_per_unit
            / request.unit_price
            * Decimal("100")
        ).quantize(
            _PERCENT_QUANTUM,
            rounding=ROUND_HALF_UP,
        )

    annual_price_return_pct = None

    if loaded_data.selected_performance is not None:
        annual_price_return_pct = _to_decimal(
            loaded_data.selected_performance.get(
                "return_pct"
            )
        )

    calculated_result = calculate_target_analysis(
        request,
        context=context,
        gross_distribution_cash=(
            gross_distribution_cash
        ),
        distribution_tax=None,
        supplementary_premium=None,
        other_distribution_costs=None,
        annual_gross_cash_rate_pct=(
            annual_gross_cash_rate_pct
        ),
        annual_price_return_pct=(
            annual_price_return_pct
        ),
    )

    merged_warnings = list(
        calculated_result.warnings
    )
    warning_codes = {
        warning.code
        for warning in merged_warnings
    }

    for warning in loaded_data.warnings:
        if warning.code in warning_codes:
            continue

        warning_codes.add(warning.code)
        merged_warnings.append(warning)

    merged_unavailable_fields = list(
        calculated_result.unavailable_fields
    )
    unavailable_names = {
        item.field
        for item in merged_unavailable_fields
    }

    for item in loaded_data.unavailable_fields:
        if item.field in unavailable_names:
            continue

        unavailable_names.add(item.field)
        merged_unavailable_fields.append(item)

    merged_status = calculated_result.status

    if merged_unavailable_fields:
        merged_status = TargetAnalysisStatus.PARTIAL

    return calculated_result.model_copy(
        update={
            "status": merged_status,
            "warnings": merged_warnings,
            "unavailable_fields": (
                merged_unavailable_fields
            ),
        },
    )


@router.post(
    "/{code}/tax-reinvestment-scenarios",
    response_model=TaxReinvestmentAnalysisResult,
    summary="比較 ETF 稅務與再投資情境",
)
def analyze_tax_reinvestment_scenarios(
    code: str,
    request: TaxReinvestmentAnalysisRequest,
    database_path: Path = Depends(get_database_path),
) -> TaxReinvestmentAnalysisResult:
    """以歷史 ACTUAL 組成和明示稅務假設執行情境估算。"""

    normalized_code = code.strip().upper()
    if get_etf_by_code(normalized_code, database_path) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到 ETF：{normalized_code}",
        )

    loaded_data = load_target_analysis_data(
        etf_code=normalized_code,
        database_path=database_path,
        history_years=request.history_years,
        as_of_date=date.today(),
    )
    monthly_income = loaded_data.monthly_income
    total_amount_per_unit = _to_decimal(
        monthly_income.get("total_amount_per_unit")
    )
    annual_distribution_rate = None
    if total_amount_per_unit is not None:
        annual_distribution_rate = (
            total_amount_per_unit
            / Decimal(request.history_years)
            / request.unit_price
            * Decimal("100")
        ).quantize(_PERCENT_QUANTUM, rounding=ROUND_HALF_UP)

    selected_performance = loaded_data.selected_performance
    annual_price_return = _annualize_price_return(selected_performance)

    component_rows = list_etf_actual_component_history(
        normalized_code,
        database_path,
    )
    selection = select_latest_complete_actual_mix(component_rows)
    actual_mix = selection.mix if selection is not None else None
    history_start = _to_date(monthly_income["window_start_date"])
    history_end = _to_date(monthly_income["as_of_date"])

    calculation = calculate_tax_reinvestment_scenarios(
        TaxReinvestmentCalculationInput(
            initial_units=request.held_units,
            initial_unit_price=request.unit_price,
            annual_gross_distribution_rate_pct=annual_distribution_rate,
            annual_price_return_pct=annual_price_return,
            projection_years=request.analysis_years,
            annual_cash_target=request.monthly_cash_target * Decimal("12"),
            payments_per_year=request.payments_per_year,
            actual_component_mix=actual_mix,
            tax_rule=request.tax_rule,
            custom_reinvestment_pct=request.custom_reinvestment_pct,
        )
    )

    return TaxReinvestmentAnalysisResult(
        status="PARTIAL" if calculation.issues else "AVAILABLE",
        historical_facts=TaxReinvestmentHistoricalFacts(
            component_dividend_id=(
                selection.dividend_id if selection is not None else None
            ),
            component_source_event_id=(
                selection.source_event_id if selection is not None else None
            ),
            component_source_date=(
                selection.source_date if selection is not None else None
            ),
            actual_component_mix=actual_mix,
            annual_gross_distribution_rate_pct=annual_distribution_rate,
            price_return_period_code=(
                str(selected_performance.get("period_code"))
                if selected_performance is not None
                and selected_performance.get("period_code") is not None
                else None
            ),
            annual_price_return_pct=annual_price_return,
            history_start_date=history_start,
            history_end_date=history_end,
        ),
        calculation=calculation,
    )
