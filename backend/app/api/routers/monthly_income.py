"""每月領息分布查詢 API。"""

from pathlib import Path
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from backend.app.api.dependencies import (
    get_database_path,
)
from backend.app.models.monthly_income_api import (
    MonthlyIncomeDistributionResponse,
)
from backend.app.repositories.monthly_income_repository import (
    build_monthly_income_distribution,
)


DatabasePath = Annotated[
    Path,
    Depends(get_database_path),
]


router = APIRouter(
    tags=["Monthly Income"],
)


@router.get(
    "/api/v1/etfs/{code}/monthly-income",
    response_model=(
        MonthlyIncomeDistributionResponse
    ),
    summary="取得 ETF 每月領息分布",
)
def read_monthly_income_distribution(
    code: str,
    database_path: DatabasePath,
    lookback_years: Annotated[
        int,
        Query(
            ge=1,
            le=10,
            description="回看年數",
        ),
    ] = 3,
) -> dict[str, Any]:
    """依歷史實際入帳日回傳 1–12 月分布。"""

    normalized_code = code.strip().upper()
    result = build_monthly_income_distribution(
        etf_code=normalized_code,
        database_path=database_path,
        lookback_years=lookback_years,
    )

    if result is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                f"找不到 ETF："
                f"{normalized_code}"
            ),
        )

    return result
