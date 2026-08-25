"""V3-1 公開且不儲存資料的現金流試算 API。"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.dependencies import get_database_path
from backend.app.models.public_planner import PublicPlannerRequest, PublicPlannerResponse
from backend.app.models.market_eligibility import (
    MarketEligibilityIndexRequest,
    MarketEligibilityIndexResponse,
)
from backend.app.services.market_eligibility_index import (
    build_market_eligibility_index,
)
from backend.app.services.public_planner import analyze_public_planner_baseline


router = APIRouter(prefix="/api/v1/allocation-plans", tags=["Public Planner"])


@router.post(
    "/baseline",
    response_model=PublicPlannerResponse,
    summary="建立不儲存資料的現有持股現金流基線",
)
def analyze_public_baseline(
    request: PublicPlannerRequest,
    database_path: Path = Depends(get_database_path),
) -> PublicPlannerResponse:
    try:
        return analyze_public_planner_baseline(request, database_path)
    except LookupError as error:
        code = str(error.args[0]).strip().upper()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到 ETF：{code}",
        ) from error


@router.post(
    "/eligibility-index",
    response_model=MarketEligibilityIndexResponse,
    summary="建立不含內部評分的全市場候選資格索引",
)
def read_market_eligibility_index(
    request: MarketEligibilityIndexRequest,
    database_path: Path = Depends(get_database_path),
) -> MarketEligibilityIndexResponse:
    try:
        return build_market_eligibility_index(request, database_path).response
    except LookupError as error:
        code = str(error.args[0]).strip().upper()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到 ETF：{code}",
        ) from error
