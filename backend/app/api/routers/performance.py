"""ETF 績效查詢 API 路由。"""

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
from backend.app.models.etf_analysis import (
    PerformanceMetric,
)
from backend.app.models.performance_api import (
    ETFPerformanceResponse,
    PerformanceRankingResponse,
    SupportedPerformancePeriod,
)
from backend.app.repositories.etf_repository import (
    get_etf_by_code,
)
from backend.app.repositories.performance_repository import (
    count_latest_performance_ranking,
    list_latest_etf_performance,
    list_latest_performance_ranking,
)


DatabasePath = Annotated[
    Path,
    Depends(get_database_path),
]


router = APIRouter(
    tags=["Performance"],
)


@router.get(
    "/api/v1/performance/ranking",
    response_model=PerformanceRankingResponse,
    summary="取得 ETF 績效排行榜",
)
def read_performance_ranking(
    database_path: DatabasePath,
    period: Annotated[
        SupportedPerformancePeriod,
        Query(
            description=(
                "績效期間：1M、3M、6M 或 1Y"
            ),
        ),
    ] = SupportedPerformancePeriod.SIX_MONTHS,
    metric: Annotated[
        PerformanceMetric,
        Query(
            description="績效計算類型",
        ),
    ] = PerformanceMetric.PRICE_RETURN,
    is_active: Annotated[
        bool | None,
        Query(
            description="篩選主動式或被動式 ETF",
        ),
    ] = None,
    is_bond: Annotated[
        bool | None,
        Query(
            description=(
                "篩選債券或非債券 ETF；"
                "預設只顯示非債券 ETF"
            ),
        ),
    ] = False,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="單次回傳筆數",
        ),
    ] = 20,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="略過筆數",
        ),
    ] = 0,
) -> dict[str, Any]:
    """取得指定期間的 ETF 最新績效排行榜。"""

    period_code = (
        period.to_performance_period()
    )

    rows = list_latest_performance_ranking(
        database_path=database_path,
        period_code=period_code,
        metric_code=metric,
        is_active=is_active,
        is_bond=is_bond,
        limit=limit,
        offset=offset,
    )

    total = count_latest_performance_ranking(
        database_path=database_path,
        period_code=period_code,
        metric_code=metric,
        is_active=is_active,
        is_bond=is_bond,
    )

    items = [
        {
            **row,
            "rank": offset + index,
        }
        for index, row in enumerate(
            rows,
            start=1,
        )
    ]

    return {
        "period_code": period_code,
        "metric_code": metric,
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }


@router.get(
    "/api/v1/etfs/{code}/performance",
    response_model=ETFPerformanceResponse,
    summary="取得單一 ETF 多期間績效",
)
def read_etf_performance(
    code: str,
    database_path: DatabasePath,
    metric: Annotated[
        PerformanceMetric,
        Query(
            description="績效計算類型",
        ),
    ] = PerformanceMetric.PRICE_RETURN,
) -> dict[str, Any]:
    """取得單一 ETF 的 1M、3M、6M、1Y 最新績效。"""

    normalized_code = (
        code.strip().upper()
    )

    etf = get_etf_by_code(
        normalized_code,
        database_path,
    )

    if etf is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                f"找不到 ETF："
                f"{normalized_code}"
            ),
        )

    items = list_latest_etf_performance(
        etf_code=normalized_code,
        database_path=database_path,
        metric_code=metric,
    )

    return {
        "etf_code": normalized_code,
        "metric_code": metric,
        "items": items,
    }
