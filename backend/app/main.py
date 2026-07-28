"""TW ETF AI Analyzer FastAPI 應用程式入口。"""

from fastapi import FastAPI

from backend.app.api.router import api_router


def create_app() -> FastAPI:
    """建立並設定 FastAPI 應用程式。

    Returns:
        FastAPI: 完成設定的 FastAPI 應用程式。
    """

    application = FastAPI(
        title="TW ETF AI Analyzer API",
        description="台灣 ETF 分析網站後端 API",
        version="0.1.0",
    )

    application.include_router(api_router)

    return application


app = create_app()