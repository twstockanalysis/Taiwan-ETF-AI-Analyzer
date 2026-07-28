"""系統狀態相關 API 路由。"""

from fastapi import APIRouter


router = APIRouter(
    tags=["System"],
)


@router.get(
    "/",
    summary="API 首頁",
)
async def read_root() -> dict[str, str]:
    """回傳 API 基本資訊。

    Returns:
        dict[str, str]: API 名稱及目前執行狀態。
    """

    return {
        "message": "TW ETF AI Analyzer API",
        "status": "running",
    }


@router.get(
    "/health",
    summary="健康檢查",
)
async def health_check() -> dict[str, str]:
    """檢查後端 API 是否正常運作。

    Returns:
        dict[str, str]: API 健康狀態。
    """

    return {
        "status": "healthy",
    }