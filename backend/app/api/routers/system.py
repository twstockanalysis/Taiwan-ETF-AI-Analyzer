"""系統狀態與首頁資料總覽 API。"""

from pathlib import Path
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
)

from backend.app.api.dependencies import (
    get_database_path,
)
from backend.app.models.system_overview_api import (
    SystemOverviewResponse,
)
from backend.app.repositories.system_overview_repository import (
    build_system_overview,
)


DatabasePath = Annotated[
    Path,
    Depends(get_database_path),
]


router = APIRouter(
    tags=["System"],
)


@router.get(
    "/",
    summary="API 首頁",
)
async def read_root() -> dict[str, str]:
    """回傳 API 基本資訊。"""

    return {
        "message": "TW ETF AI Analyzer API",
        "status": "running",
    }


@router.get(
    "/health",
    summary="健康檢查",
)
async def health_check() -> dict[str, str]:
    """檢查後端 API 是否正常運作。"""

    return {
        "status": "healthy",
    }


@router.get(
    "/api/v1/system/overview",
    response_model=SystemOverviewResponse,
    summary="取得首頁系統資料總覽",
)
def read_system_overview(
    database_path: DatabasePath,
) -> dict[str, Any]:
    """回傳 ETF、績效、配息與最近匯入摘要。"""

    return build_system_overview(
        database_path=database_path,
        recent_batch_limit=5,
    )
