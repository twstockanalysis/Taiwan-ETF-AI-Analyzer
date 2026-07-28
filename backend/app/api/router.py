"""集中管理後端 API Router。"""

from fastapi import APIRouter

from backend.app.api.routers import system


api_router = APIRouter()

api_router.include_router(system.router)