"""正式配息覆蓋率與待處理佇列 API。"""

from pathlib import Path
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path as PathParameter,
    Query,
    status,
)

from backend.app.api.dependencies import (
    get_database_path,
)
from backend.app.models.dividend_quality import (
    DividendReviewIssueType,
    DividendReviewStatus,
)
from backend.app.models.dividend_quality_api import (
    ActualDividendCoverageResponse,
    DividendReviewQueueItem,
    DividendReviewQueueResponse,
)
from backend.app.repositories.dividend_quality_repository import (
    build_actual_dividend_coverage_summary,
    count_dividend_review_queue,
    get_dividend_review_queue_item,
    list_dividend_review_queue,
)
from backend.app.repositories.etf_repository import (
    get_etf_by_code,
)


DatabasePath = Annotated[
    Path,
    Depends(get_database_path),
]


router = APIRouter(
    tags=["Data Quality"],
)


def normalize_existing_etf_code(
    etf_code: str | None,
    database_path: Path,
) -> str | None:
    """驗證可選 ETF 篩選條件。"""

    if etf_code is None:
        return None

    normalized_code = (
        etf_code.strip().upper()
    )

    if get_etf_by_code(
        normalized_code,
        database_path,
    ) is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                f"找不到 ETF："
                f"{normalized_code}"
            ),
        )

    return normalized_code


@router.get(
    (
        "/api/v1/data-quality/dividends/"
        "actual-coverage"
    ),
    response_model=(
        ActualDividendCoverageResponse
    ),
    summary="取得正式配息資料覆蓋率",
)
def read_actual_dividend_coverage(
    database_path: DatabasePath,
    etf_code: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=10,
            description="篩選 ETF 代號",
        ),
    ] = None,
) -> dict[str, Any]:
    """即時計算 ACTUAL、76W 與來源文件覆蓋率。"""

    normalized_code = (
        normalize_existing_etf_code(
            etf_code,
            database_path,
        )
    )

    return (
        build_actual_dividend_coverage_summary(
            database_path=database_path,
            etf_code=normalized_code,
        )
    )


@router.get(
    (
        "/api/v1/data-quality/dividends/"
        "review-queue"
    ),
    response_model=(
        DividendReviewQueueResponse
    ),
    summary="查詢正式配息待處理佇列",
)
def read_dividend_review_queue(
    database_path: DatabasePath,
    queue_status: Annotated[
        DividendReviewStatus | None,
        Query(
            alias="status",
            description="篩選審核狀態",
        ),
    ] = None,
    etf_code: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=10,
            description="篩選 ETF 代號",
        ),
    ] = None,
    issue_type: Annotated[
        DividendReviewIssueType | None,
        Query(
            description="篩選缺失類型",
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 20,
    offset: Annotated[
        int,
        Query(
            ge=0,
        ),
    ] = 0,
) -> dict[str, Any]:
    """分頁回傳正式配息待處理項目。"""

    normalized_code = (
        normalize_existing_etf_code(
            etf_code,
            database_path,
        )
    )

    rows = list_dividend_review_queue(
        database_path=database_path,
        status=queue_status,
        etf_code=normalized_code,
        issue_type=issue_type,
        limit=limit,
        offset=offset,
    )

    total = count_dividend_review_queue(
        database_path=database_path,
        status=queue_status,
        etf_code=normalized_code,
        issue_type=issue_type,
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": rows,
    }


@router.get(
    (
        "/api/v1/data-quality/dividends/"
        "review-queue/{queue_id}"
    ),
    response_model=DividendReviewQueueItem,
    summary="取得單一正式配息待處理項目",
)
def read_dividend_review_queue_item(
    queue_id: Annotated[
        int,
        PathParameter(
            ge=1,
        ),
    ],
    database_path: DatabasePath,
) -> dict[str, Any]:
    """依資料庫 ID 取得審核佇列項目。"""

    row = get_dividend_review_queue_item(
        queue_id=queue_id,
        database_path=database_path,
    )

    if row is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "找不到正式配息審核項目："
                f"{queue_id}"
            ),
        )

    return row
