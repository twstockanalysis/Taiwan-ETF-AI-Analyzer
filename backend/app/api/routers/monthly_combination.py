"""M10-5 月配缺口組合 API。"""

from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.dependencies import get_database_path
from backend.app.models.monthly_combination import (
    MonthlyCombinationAnalysisRequest,
    MonthlyCombinationAnalysisResult,
    MonthlyCombinationCalculationInput,
    MonthlyCombinationHistoricalFacts,
)
from backend.app.services.monthly_combination_calculator import (
    calculate_monthly_payment_combination,
)
from backend.app.services.monthly_combination_data import (
    load_monthly_combination_data,
)


router = APIRouter(
    prefix="/api/v1/etfs",
    tags=["Monthly Combination"],
)


@router.post(
    "/{code}/monthly-payment-combination",
    response_model=MonthlyCombinationAnalysisResult,
    summary="建立月配缺口與候選排除情境",
)
def analyze_monthly_payment_combination(
    code: str,
    request: MonthlyCombinationAnalysisRequest,
    database_path: Path = Depends(get_database_path),
) -> MonthlyCombinationAnalysisResult:
    """以基準 ETF 為錨點，先做品質門檻再補付款月份。"""

    normalized_code = code.strip().upper()
    if normalized_code in {
        candidate.etf_code for candidate in request.candidates
    }:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="候選清單不可包含基準 ETF",
        )

    analysis_date = date.today()
    loaded = load_monthly_combination_data(
        base_etf_code=normalized_code,
        assumptions=request.candidates,
        database_path=database_path,
        lookback_years=request.lookback_years,
        cash_deduction_rate_pct=request.cash_deduction_rate_pct,
        rules=request.rules,
        as_of_date=analysis_date,
    )
    if loaded.base_etf is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到 ETF：{normalized_code}",
        )
    missing_codes = [
        candidate.etf_code
        for candidate in request.candidates
        if loaded.candidate_etfs[candidate.etf_code] is None
    ]
    if missing_codes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到候選 ETF：{', '.join(missing_codes)}",
        )

    calculation = calculate_monthly_payment_combination(
        MonthlyCombinationCalculationInput(
            base_etf_code=normalized_code,
            base_etf_name=loaded.base_etf["name"],
            base_payment_months=loaded.base_payment_months,
            candidates=loaded.candidates,
            max_complementary_etfs=request.max_complementary_etfs,
            monthly_coverage_enabled=request.monthly_coverage_enabled,
            rules=request.rules,
        )
    )
    return MonthlyCombinationAnalysisResult(
        historical_facts=MonthlyCombinationHistoricalFacts(
            as_of_date=analysis_date,
            lookback_years=request.lookback_years,
        ),
        cash_deduction_rate_pct=request.cash_deduction_rate_pct,
        calculation=calculation,
    )
