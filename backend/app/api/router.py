"""集中管理後端 API Router。"""

from fastapi import APIRouter

from backend.app.api.routers import (
    data_quality,
    dividends,
    etfs,
    performance,
    system,
)


api_router = APIRouter()

api_router.include_router(
    system.router
)

api_router.include_router(
    etfs.router
)

api_router.include_router(
    performance.router
)

api_router.include_router(
    dividends.router
)

api_router.include_router(
    data_quality.router
)
